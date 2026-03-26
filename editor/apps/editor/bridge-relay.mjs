import { WebSocketServer } from 'ws'

const PORT = 3100
const wss = new WebSocketServer({ port: PORT })

let editorClient = null
const pythonClients = new Set()

wss.on('connection', (ws) => {
  let role = null

  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw.toString())

      if (msg.type === 'register') {
        role = msg.role
        if (role === 'editor') {
          editorClient = ws
          console.log('[Relay] Editor connected')
        } else if (role === 'python') {
          pythonClients.add(ws)
          console.log(`[Relay] Python client connected (${pythonClients.size} total)`)
        }
        return
      }

      // Python -> Editor: forward command
      if (msg.type === 'command' && role === 'python') {
        if (editorClient && editorClient.readyState === 1) {
          editorClient.send(JSON.stringify(msg))
        } else {
          ws.send(JSON.stringify({
            type: 'response',
            payload: { id: msg.payload?.id, ok: false, error: 'Editor not connected' },
          }))
        }
        return
      }

      // Editor -> Python: forward response
      if (msg.type === 'response' && role === 'editor') {
        for (const client of pythonClients) {
          if (client.readyState === 1) {
            client.send(JSON.stringify(msg))
          }
        }
        return
      }

      // Editor -> Python: forward browser errors
      if (msg.type === 'browser_error' && role === 'editor') {
        for (const client of pythonClients) {
          if (client.readyState === 1) {
            client.send(JSON.stringify(msg))
          }
        }
        return
      }
    } catch (err) {
      console.error('[Relay] Parse error:', err.message)
    }
  })

  ws.on('close', () => {
    if (role === 'editor') {
      editorClient = null
      console.log('[Relay] Editor disconnected')
    } else if (role === 'python') {
      pythonClients.delete(ws)
      console.log(`[Relay] Python client disconnected (${pythonClients.size} remaining)`)
    }
  })
})

console.log(`[Relay] WebSocket relay running on ws://localhost:${PORT}`)
