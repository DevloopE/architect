'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useConstruction } from './construction-store'
import PerfPanel from './perf-panel'
import FloorSelector from './floor-selector'

export default function Dashboard() {
  const isBuilding = useConstruction((s) => s.isBuilding)
  const isReplaying = useConstruction((s) => s.isReplaying)
  const replaySpeed = useConstruction((s) => s.replaySpeed)
  const replayProgress = useConstruction((s) => s.replayProgress)
  const replayTotal = useConstruction((s) => s.replayTotal)
  const soundEnabled = useConstruction((s) => s.soundEnabled)
  const entries = useConstruction((s) => s.entries)
  const [perfOpen, setPerfOpen] = useState(false)
  const [saved, setSaved] = useState(true)
  const [projectName, setProjectName] = useState('Untitled')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Warn on close if unsaved
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!saved && entries.length > 0) {
        e.preventDefault()
        e.returnValue = 'You have an unsaved building. Are you sure you want to leave?'
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [saved, entries.length])

  // Mark unsaved when building completes
  useEffect(() => {
    if (!isBuilding && entries.length > 0) setSaved(false)
  }, [isBuilding, entries.length])

  // Save pipeline to user-chosen directory
  const handleSave = useCallback(async () => {
    const pipeline = (window as any).__lastPipeline
    if (!pipeline || pipeline.length === 0) {
      alert('No construction pipeline recorded. Build something first!')
      return
    }
    const name = prompt('Project name:', projectName) ?? projectName
    setProjectName(name)

    const data = {
      version: 1,
      name,
      created: new Date().toISOString(),
      commands: pipeline,
    }
    const json = JSON.stringify(data, null, 2)
    const filename = `${name.replace(/\s+/g, '-').toLowerCase()}.architect.json`

    // Try File System Access API first (lets user pick directory)
    if ('showSaveFilePicker' in window) {
      try {
        const handle = await (window as any).showSaveFilePicker({
          suggestedName: filename,
          types: [{ description: 'Architect Pipeline', accept: { 'application/json': ['.architect.json', '.json'] } }],
        })
        const writable = await handle.createWritable()
        await writable.write(json)
        await writable.close()
        setSaved(true)
        return
      } catch {
        // User cancelled or API not available
      }
    }

    // Fallback: download
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    setSaved(true)
  }, [projectName])

  // Load pipeline file
  const handleLoad = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    let data: any
    try {
      data = JSON.parse(text)
    } catch {
      alert('Invalid JSON file.')
      return
    }

    // Pipeline format: { commands: [...] }
    if (data.commands && Array.isArray(data.commands)) {
      setProjectName(data.name ?? 'Loaded Project')
      replayPipeline(data.commands)
      e.target.value = ''
      return
    }

    // Scene format: { nodes: {...}, rootNodeIds: [...] }
    if (data.nodes && data.rootNodeIds) {
      try {
        const { useScene } = await import('@pascal-app/core')
        useScene.getState().clearScene()
        useConstruction.getState().clear()
        await new Promise((r) => setTimeout(r, 500))
        useScene.getState().setScene(data.nodes, data.rootNodeIds)
        setProjectName(data.name ?? file.name.replace(/\.json$/, ''))
        setSaved(true)
      } catch (err) {
        alert('Failed to load scene: ' + err)
      }
      e.target.value = ''
      return
    }

    alert('Invalid file. Expected .architect.json (pipeline with commands array) or scene JSON (with nodes and rootNodeIds).')
    e.target.value = ''
  }, [])

  // Export as GLB (standard 3D format) — uses the kernel's built-in GLTFExporter
  const handleExportGLB = useCallback(async () => {
    try {
      const { useViewer } = await import('@pascal-app/viewer')
      const { exportScene } = useViewer.getState()
      if (exportScene) {
        await exportScene()
      } else {
        alert('GLB export not available. The 3D scene may not be fully loaded.')
      }
    } catch (err) {
      alert('Export failed: ' + err)
    }
  }, [])

  // Export raw scene JSON
  const handleExportJSON = useCallback(async () => {
    try {
      const { useScene } = await import('@pascal-app/core')
      const scene = useScene.getState()
      const data = { nodes: scene.nodes, rootNodeIds: scene.rootNodeIds, collections: scene.collections }
      const json = JSON.stringify(data, null, 2)
      const filename = `${projectName.replace(/\s+/g, '-').toLowerCase()}-scene.json`

      if ('showSaveFilePicker' in window) {
        try {
          const handle = await (window as any).showSaveFilePicker({
            suggestedName: filename,
            types: [{ description: 'Scene JSON', accept: { 'application/json': ['.json'] } }],
          })
          const writable = await handle.createWritable()
          await writable.write(json)
          await writable.close()
          return
        } catch { /* cancelled */ }
      }

      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Export failed: ' + err)
    }
  }, [projectName])

  const toggleSound = useCallback(() => {
    useConstruction.getState().setSoundEnabled(!soundEnabled)
  }, [soundEnabled])

  const setSpeed = useCallback((s: number) => {
    useConstruction.getState().setReplaySpeed(s)
  }, [])

  const speeds = [0.5, 1, 2, 5, 10]

  return (
    <>
      {/* Top bar */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: 40,
        background: 'rgba(10,10,15,0.9)', borderBottom: '1px solid rgba(255,255,255,0.08)',
        backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center',
        padding: '0 16px', gap: 10, fontFamily: 'monospace', fontSize: 12,
        color: '#e2e8f0', zIndex: 10000,
      }}>
        {/* Logo + Project */}
        <span style={{ fontWeight: 900, fontSize: 18, color: '#a855f7', lineHeight: 1 }}>A</span>
        <span style={{ fontWeight: 700, fontSize: 13, color: '#e2e8f0', letterSpacing: 0.5 }}>rchitect</span>
        <span style={{ color: '#475569', fontSize: 9, marginLeft: 2 }}>
          <a href="https://github.com/pascalorg/editor" target="_blank" rel="noopener" style={{ color: '#475569', textDecoration: 'none' }}>Pascal Editor</a>
        </span>
        <span style={{ color: '#64748b', fontSize: 10 }}>| {projectName}</span>
        {!saved && <span style={{ color: '#f59e0b', fontSize: 10 }}>(unsaved)</span>}

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />

        {/* Status */}
        {isBuilding && (
          <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>&#x2692;</span>
            Building...
          </span>
        )}
        {isReplaying && (
          <span style={{ color: '#3b82f6' }}>
            &#x25B6; Replay {replayProgress}/{replayTotal}
          </span>
        )}

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />

        {/* Floor selector */}
        <FloorSelector />

        <div style={{ flex: 1 }} />

        {/* Speed */}
        <span style={{ color: '#64748b', fontSize: 10 }}>SPEED</span>
        {speeds.map((s) => (
          <button key={s} onClick={() => setSpeed(s)} style={{
            background: replaySpeed === s ? '#a855f7' : 'rgba(255,255,255,0.06)',
            border: '1px solid', borderColor: replaySpeed === s ? '#a855f7' : 'rgba(255,255,255,0.1)',
            borderRadius: 4, color: replaySpeed === s ? '#fff' : '#94a3b8',
            padding: '2px 6px', cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
          }}>{s}x</button>
        ))}

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />

        {/* Sound */}
        <button onClick={toggleSound} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: soundEnabled ? '#22c55e' : '#64748b', padding: '2px 6px' }}
          title={soundEnabled ? 'Sound ON' : 'Sound OFF'}>
          {soundEnabled ? '\u{1F50A}' : '\u{1F507}'}
        </button>

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />

        {/* File actions */}
        <button onClick={handleSave} style={btnStyle} title="Save construction pipeline (.architect.json)">
          Save
        </button>
        <button onClick={handleLoad} style={btnStyle} title="Load pipeline or scene JSON">
          Load
        </button>

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />

        {/* Export */}
        <button onClick={handleExportGLB} style={{ ...btnStyle, borderColor: '#22c55e', color: '#22c55e' }} title="Export as GLB (standard 3D format)">
          Export .glb
        </button>
        <button onClick={handleExportJSON} style={{ ...btnStyle, borderColor: '#3b82f6', color: '#3b82f6' }} title="Export raw scene JSON">
          Export .json
        </button>

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)' }} />

        <button onClick={() => setPerfOpen(!perfOpen)}
          style={{ ...btnStyle, borderColor: perfOpen ? '#a855f7' : undefined, color: perfOpen ? '#a855f7' : undefined }}
          title="Performance settings">
          &#x2699;
        </button>

        <input ref={fileInputRef} type="file" accept=".json,.architect.json" onChange={handleFileSelect} style={{ display: 'none' }} />
      </div>

      {/* Replay progress bar */}
      {isReplaying && (
        <div style={{ position: 'fixed', top: 40, left: 0, right: 0, height: 3, background: 'rgba(255,255,255,0.05)', zIndex: 10000 }}>
          <div style={{ height: '100%', width: `${replayTotal > 0 ? (replayProgress / replayTotal) * 100 : 0}%`, background: 'linear-gradient(90deg, #3b82f6, #a855f7)', transition: 'width 0.1s' }} />
        </div>
      )}

      <PerfPanel open={perfOpen} onClose={() => setPerfOpen(false)} />

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </>
  )
}

const btnStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.15)',
  borderRadius: 4, color: '#94a3b8', padding: '4px 10px', cursor: 'pointer',
  fontSize: 11, fontFamily: 'monospace',
}

// Replay engine
async function replayPipeline(commands: Array<{ ts: number; cmd: string; payload: Record<string, unknown> }>) {
  const { handleCommand } = await import('./command-handler')
  const store = useConstruction.getState()
  const { useScene } = await import('@pascal-app/core')

  useScene.getState().clearScene()
  store.clear()
  store.setReplaying(true)
  store.setReplayProgress(0, commands.length)
  store.addEntry({ type: 'info', message: `Replaying ${commands.length} commands...` })

  await new Promise((r) => setTimeout(r, 500))

  let lastTs = 0
  for (let i = 0; i < commands.length; i++) {
    const cmd = commands[i]
    const speed = useConstruction.getState().replaySpeed
    const delay = Math.max(0, (cmd.ts - lastTs) / speed)
    if (delay > 0 && delay < 5000) {
      await new Promise((r) => setTimeout(r, Math.min(delay, 500 / speed)))
    }
    lastTs = cmd.ts

    try {
      handleCommand({ cmd: cmd.cmd, id: `replay_${i}`, ...cmd.payload } as any)
    } catch { /* continue */ }

    store.setReplayProgress(i + 1, commands.length)
  }

  store.setReplaying(false)
  store.addEntry({ type: 'done', message: 'Replay complete!' })
}
