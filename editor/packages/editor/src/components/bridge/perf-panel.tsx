'use client'

import { useCallback, useEffect, useState } from 'react'

type GpuInfo = { vendor: string; name: string; isIntegrated: boolean }
type PerfPreset = 'ultra' | 'high' | 'medium' | 'low'

export default function PerfPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [gpu, setGpu] = useState<GpuInfo | null>(null)
  const [fps, setFps] = useState(0)
  const [preset, setPreset] = useState<PerfPreset>('high')
  const [pixelRatio, setPixelRatio] = useState(typeof window !== 'undefined' ? window.devicePixelRatio : 1)

  // Detect GPU
  useEffect(() => {
    (async () => {
      try {
        // WebGPU detection
        if (navigator.gpu) {
          const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' })
          if (adapter) {
            const info = (adapter as any).info || {}
            const name = info.device || info.description || 'Unknown'
            const vendor = info.vendor || 'Unknown'
            const isIntegrated = /intel|integrated/i.test(name + vendor)
            setGpu({ vendor, name, isIntegrated })
            return
          }
        }
        // WebGL fallback
        const canvas = document.createElement('canvas')
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
        if (gl) {
          const ext = gl.getExtension('WEBGL_debug_renderer_info')
          const vendor = ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : 'Unknown'
          const name = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'Unknown'
          const isIntegrated = /intel|integrated/i.test(name + vendor)
          setGpu({ vendor, name, isIntegrated })
        }
      } catch {
        setGpu({ vendor: 'Unknown', name: 'Detection failed', isIntegrated: false })
      }
    })()
  }, [])

  // FPS counter
  useEffect(() => {
    let frames = 0
    let last = performance.now()
    let raf: number
    const tick = () => {
      frames++
      const now = performance.now()
      if (now - last >= 1000) {
        setFps(frames)
        frames = 0
        last = now
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  // Apply preset
  const applyPreset = useCallback((p: PerfPreset) => {
    setPreset(p)
    const ratios: Record<PerfPreset, number> = { ultra: 2, high: 1.5, medium: 1, low: 0.75 }
    const ratio = ratios[p]
    setPixelRatio(ratio)

    // Find the Three.js canvas and adjust pixel ratio
    const canvas = document.querySelector('canvas')
    if (canvas) {
      const renderer = (canvas as any).__r3f?.store?.getState()?.gl
      if (renderer) {
        renderer.setPixelRatio(ratio)
        renderer.setSize(window.innerWidth, window.innerHeight - 40)
      }
    }
  }, [])

  if (!open) return null

  const fpsColor = fps >= 50 ? '#22c55e' : fps >= 30 ? '#f59e0b' : '#ef4444'

  return (
    <div
      style={{
        position: 'fixed',
        top: 44,
        right: 16,
        width: 320,
        background: 'rgba(10, 10, 15, 0.95)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 10,
        backdropFilter: 'blur(12px)',
        fontFamily: 'monospace',
        fontSize: 11,
        color: '#e2e8f0',
        zIndex: 10001,
        padding: 16,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{ fontWeight: 700, fontSize: 13 }}>Performance</span>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 14 }}
        >
          &#x2715;
        </button>
      </div>

      {/* FPS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, padding: '8px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
        <span style={{ color: '#94a3b8' }}>FPS</span>
        <span style={{ color: fpsColor, fontWeight: 700, fontSize: 18 }}>{fps}</span>
      </div>

      {/* GPU Info */}
      <div style={{ marginBottom: 12, padding: '8px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
        <div style={{ color: '#94a3b8', marginBottom: 4 }}>GPU</div>
        {gpu ? (
          <>
            <div style={{ color: gpu.isIntegrated ? '#f59e0b' : '#22c55e', fontSize: 12 }}>
              {gpu.name}
            </div>
            {gpu.isIntegrated && (
              <div style={{ color: '#ef4444', fontSize: 10, marginTop: 4 }}>
                &#x26A0; Integrated GPU detected. Set browser to use discrete GPU in Windows Settings &gt; Display &gt; Graphics
              </div>
            )}
          </>
        ) : (
          <div style={{ color: '#64748b' }}>Detecting...</div>
        )}
      </div>

      {/* Quality Presets */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ color: '#94a3b8', marginBottom: 6 }}>Quality Preset</div>
        <div style={{ display: 'flex', gap: 6 }}>
          {(['ultra', 'high', 'medium', 'low'] as PerfPreset[]).map((p) => (
            <button
              key={p}
              onClick={() => applyPreset(p)}
              style={{
                flex: 1,
                background: preset === p ? '#a855f7' : 'rgba(255,255,255,0.06)',
                border: '1px solid',
                borderColor: preset === p ? '#a855f7' : 'rgba(255,255,255,0.1)',
                borderRadius: 4,
                color: preset === p ? '#fff' : '#94a3b8',
                padding: '6px 0',
                cursor: 'pointer',
                fontSize: 10,
                fontFamily: 'monospace',
                textTransform: 'uppercase',
              }}
            >
              {p}
            </button>
          ))}
        </div>
        <div style={{ color: '#64748b', fontSize: 10, marginTop: 4 }}>
          Pixel ratio: {pixelRatio.toFixed(2)}
        </div>
      </div>

      {/* Browser settings links */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
        <div style={{ color: '#94a3b8', marginBottom: 6 }}>Browser GPU Settings</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <a
            href="edge://flags/#enable-unsafe-webgpu"
            style={{ color: '#3b82f6', fontSize: 10, textDecoration: 'none' }}
            onClick={(e) => { e.preventDefault(); navigator.clipboard.writeText('edge://flags/#enable-unsafe-webgpu'); alert('Copied to clipboard! Paste in address bar.') }}
          >
            edge://flags — WebGPU flags (click to copy)
          </a>
          <a
            href="edge://settings/system"
            style={{ color: '#3b82f6', fontSize: 10, textDecoration: 'none' }}
            onClick={(e) => { e.preventDefault(); navigator.clipboard.writeText('edge://settings/system'); alert('Copied to clipboard! Paste in address bar.') }}
          >
            edge://settings/system — Hardware acceleration (click to copy)
          </a>
          <a
            href="ms-settings:display"
            style={{ color: '#3b82f6', fontSize: 10, textDecoration: 'none' }}
            onClick={(e) => { e.preventDefault(); window.open('ms-settings:display'); }}
          >
            Windows Graphics Settings — GPU per app
          </a>
        </div>
      </div>
    </div>
  )
}
