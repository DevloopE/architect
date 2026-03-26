'use client'

import { useCallback, useEffect, useState } from 'react'

type FloorInfo = { id: string; level: number; label: string }

export default function FloorSelector() {
  const [floors, setFloors] = useState<FloorInfo[]>([])
  const [visibleUpTo, setVisibleUpTo] = useState<number>(-1) // -1 = show all
  const [open, setOpen] = useState(false)

  // Scan scene for levels
  const refreshFloors = useCallback(async () => {
    try {
      const { useScene } = await import('@pascal-app/core')
      const nodes = useScene.getState().nodes
      const found: FloorInfo[] = []
      for (const [id, node] of Object.entries(nodes)) {
        if ((node as any).type === 'level') {
          const lvl = (node as any).level ?? 0
          const label = lvl === 0 ? 'B' : lvl === 1 ? 'G' : `${lvl - 1}F`
          found.push({ id, level: lvl, label })
        }
      }
      found.sort((a, b) => a.level - b.level)
      setFloors(found)
      if (visibleUpTo === -1) setVisibleUpTo(found.length > 0 ? found[found.length - 1].level : -1)
    } catch { /* scene not ready */ }
  }, [visibleUpTo])

  // Refresh when scene changes
  useEffect(() => {
    refreshFloors()
    const interval = setInterval(refreshFloors, 3000)
    return () => clearInterval(interval)
  }, [refreshFloors])

  // Apply visibility: show floors up to the selected level, hide the rest
  const applyVisibility = useCallback(async (upToLevel: number) => {
    try {
      const { useScene } = await import('@pascal-app/core')
      const { useViewer } = await import('@pascal-app/viewer')
      const scene = useScene.getState()

      // Set level mode to stacked (show all, we control visibility manually)
      useViewer.getState().setLevelMode('stacked')

      for (const floor of floors) {
        const node = scene.nodes[floor.id as any]
        if (!node) continue
        const shouldShow = floor.level <= upToLevel
        if ((node as any).visible !== shouldShow) {
          scene.updateNode(floor.id as any, { visible: shouldShow } as any)
        }
      }

      // Select the top visible floor
      const topVisible = floors.filter(f => f.level <= upToLevel).pop()
      if (topVisible) {
        useViewer.getState().setSelection({ levelId: topVisible.id } as any)
      }
    } catch { /* */ }
  }, [floors])

  const handleFloorClick = useCallback((level: number) => {
    setVisibleUpTo(level)
    applyVisibility(level)
  }, [applyVisibility])

  const handleShowAll = useCallback(() => {
    const maxLevel = floors.length > 0 ? floors[floors.length - 1].level : 0
    setVisibleUpTo(maxLevel)
    applyVisibility(maxLevel)
  }, [floors, applyVisibility])

  if (floors.length <= 1) return null // No floor selector needed for single-floor buildings

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <span style={{ color: '#64748b', fontSize: 10 }}>FLOOR</span>

      <button onClick={handleShowAll} style={{
        ...fbtn,
        background: visibleUpTo === (floors.length > 0 ? floors[floors.length - 1].level : 0) ? '#3b82f6' : 'rgba(255,255,255,0.06)',
        color: visibleUpTo === (floors.length > 0 ? floors[floors.length - 1].level : 0) ? '#fff' : '#94a3b8',
        borderColor: visibleUpTo === (floors.length > 0 ? floors[floors.length - 1].level : 0) ? '#3b82f6' : 'rgba(255,255,255,0.1)',
      }}>ALL</button>

      {floors.map((f) => (
        <button key={f.id} onClick={() => handleFloorClick(f.level)} style={{
          ...fbtn,
          background: visibleUpTo === f.level ? '#a855f7' : 'rgba(255,255,255,0.06)',
          color: visibleUpTo === f.level ? '#fff' : f.level <= visibleUpTo ? '#e2e8f0' : '#475569',
          borderColor: visibleUpTo === f.level ? '#a855f7' : f.level <= visibleUpTo ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.05)',
        }}>{f.label}</button>
      ))}
    </div>
  )
}

const fbtn: React.CSSProperties = {
  background: 'rgba(255,255,255,0.06)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 4,
  color: '#94a3b8',
  padding: '2px 8px',
  cursor: 'pointer',
  fontSize: 11,
  fontFamily: 'monospace',
  fontWeight: 700,
  minWidth: 28,
  textAlign: 'center',
}
