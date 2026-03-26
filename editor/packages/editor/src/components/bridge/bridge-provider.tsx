'use client'

import { useEffect } from 'react'
import { handleCommand } from './command-handler'
import type { BridgeCommand } from './types'

const RELAY_URL = 'ws://localhost:3100'
const RECONNECT_DELAY = 3000

export default function BridgeProvider() {
  useEffect(() => {
    let ws: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let disposed = false

    // Intercept console.error and forward to Python via WebSocket
    const originalError = console.error
    console.error = (...args: unknown[]) => {
      originalError.apply(console, args)
      if (ws?.readyState === 1) {
        const msg = args.map(a =>
          typeof a === 'string' ? a : a instanceof Error ? a.message : String(a)
        ).join(' ')
        ws.send(JSON.stringify({ type: 'browser_error', payload: msg }))
      }
    }

    // Also catch unhandled errors
    const onError = (e: ErrorEvent) => {
      if (ws?.readyState === 1) {
        ws.send(JSON.stringify({ type: 'browser_error', payload: e.message }))
      }
    }
    window.addEventListener('error', onError)

    function connect() {
      if (disposed) return
      ws = new WebSocket(RELAY_URL)

      ws.addEventListener('open', () => {
        ws!.send(JSON.stringify({ type: 'register', role: 'editor' }))
      })

      ws.addEventListener('message', (event) => {
        try {
          const msg = JSON.parse(event.data as string)
          if (msg.type !== 'command') return
          const cmd = msg.payload as BridgeCommand
          const response = handleCommand(cmd)
          ws?.send(JSON.stringify({ type: 'response', payload: response }))
        } catch {
          // silently ignore malformed messages
        }
      })

      ws.addEventListener('close', () => {
        if (!disposed) scheduleReconnect()
      })

      ws.addEventListener('error', () => {})
    }

    function scheduleReconnect() {
      if (disposed) return
      reconnectTimer = setTimeout(connect, RECONNECT_DELAY)
    }

    connect()

    return () => {
      disposed = true
      console.error = originalError
      window.removeEventListener('error', onError)
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (ws) { ws.close(); ws = null }
    }
  }, [])

  return null
}
