'use client'

import { useEffect, useRef, useState } from 'react'
import { useConstruction } from './construction-store'
import type { LogEntry } from './construction-store'

const TYPE_COLORS: Record<LogEntry['type'], string> = {
  step: '#f59e0b',
  create: '#22c55e',
  info: '#3b82f6',
  error: '#ef4444',
  done: '#a855f7',
}

const TYPE_ICONS: Record<LogEntry['type'], string> = {
  step: '\u25B6',
  create: '+',
  info: '\u2022',
  error: '\u2716',
  done: '\u2714',
}

export default function ConstructionPanel() {
  const entries = useConstruction((s) => s.entries)
  const isBuilding = useConstruction((s) => s.isBuilding)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [entries.length])

  // Auto-expand when building starts
  useEffect(() => {
    if (isBuilding) setCollapsed(false)
  }, [isBuilding])

  if (!isBuilding && entries.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 16,
        left: 16,
        width: collapsed ? 200 : 360,
        maxHeight: collapsed ? 36 : 400,
        background: 'rgba(10, 10, 15, 0.92)',
        borderRadius: 10,
        border: '1px solid rgba(255,255,255,0.1)',
        backdropFilter: 'blur(12px)',
        fontFamily: 'monospace',
        fontSize: 11,
        color: '#e2e8f0',
        zIndex: 9999,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Header — always visible, clickable to toggle */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        style={{
          padding: '8px 12px',
          borderBottom: collapsed ? 'none' : '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 12, letterSpacing: 0.5 }}>
          {isBuilding ? '\u2692 CONSTRUCTING...' : '\u2714 LOG'}
        </span>
        <span style={{ color: '#64748b', fontSize: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
          {entries.length} steps
          <span style={{ fontSize: 8 }}>{collapsed ? '\u25B2' : '\u25BC'}</span>
        </span>
      </div>

      {/* Collapsible body */}
      {!collapsed && (
        <>
          <div
            ref={scrollRef}
            style={{ overflowY: 'auto', padding: '6px 0', maxHeight: 300 }}
          >
            {entries.map((entry) => (
              <div
                key={entry.id}
                style={{
                  padding: '3px 12px',
                  display: 'flex',
                  gap: 8,
                  alignItems: 'flex-start',
                  opacity: entry.type === 'info' ? 0.6 : 1,
                }}
              >
                <span style={{ color: TYPE_COLORS[entry.type], minWidth: 14, textAlign: 'center', fontWeight: 700 }}>
                  {TYPE_ICONS[entry.type]}
                </span>
                <span style={{ flex: 1, lineHeight: 1.4 }}>
                  {entry.message}
                  {entry.nodeType && (
                    <span style={{ color: '#64748b', marginLeft: 6 }}>[{entry.nodeType}]</span>
                  )}
                </span>
              </div>
            ))}
            {isBuilding && (
              <div style={{ padding: '4px 12px', color: '#f59e0b' }}>
                \u2026 building
              </div>
            )}
          </div>

          {/* Attribution */}
          <div style={{
            padding: '6px 12px',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            color: '#475569',
            fontSize: 9,
            display: 'flex',
            justifyContent: 'space-between',
          }}>
            <span>Powered by <a href="https://github.com/pascalorg/editor" target="_blank" rel="noopener" style={{ color: '#64748b', textDecoration: 'none' }}>Pascal Editor</a></span>
            <span style={{ color: '#7c3aed' }}>Architect</span>
          </div>
        </>
      )}
    </div>
  )
}
