'use client'

// Simple Web Audio construction sounds — no external files needed

let ctx: AudioContext | null = null

function getCtx(): AudioContext {
  if (!ctx) ctx = new AudioContext()
  return ctx
}

function playTone(freq: number, duration: number, type: OscillatorType = 'sine', volume = 0.15) {
  try {
    const c = getCtx()
    const osc = c.createOscillator()
    const gain = c.createGain()
    osc.type = type
    osc.frequency.value = freq
    gain.gain.setValueAtTime(volume, c.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + duration)
    osc.connect(gain)
    gain.connect(c.destination)
    osc.start()
    osc.stop(c.currentTime + duration)
  } catch {
    // Audio not available
  }
}

export function playConstructionSound(nodeType: string) {
  switch (nodeType) {
    case 'wall':
      playTone(120, 0.15, 'square', 0.1) // deep thud
      break
    case 'slab':
    case 'ceiling':
      playTone(80, 0.2, 'square', 0.08) // heavy thud
      break
    case 'door':
      playTone(800, 0.08, 'sine', 0.12) // click
      playTone(600, 0.06, 'sine', 0.08)
      break
    case 'window':
      playTone(2000, 0.1, 'sine', 0.06) // glass clink
      playTone(2500, 0.08, 'sine', 0.04)
      break
    case 'zone':
      playTone(440, 0.1, 'triangle', 0.06) // soft ping
      break
    case 'item':
      playTone(300, 0.1, 'triangle', 0.08) // soft place
      break
    case 'roof':
    case 'roof-segment':
      playTone(150, 0.3, 'sawtooth', 0.06) // heavy
      break
    default:
      playTone(500, 0.05, 'sine', 0.05)
  }
}

export function playStepSound() {
  playTone(660, 0.12, 'sine', 0.1)
  setTimeout(() => playTone(880, 0.12, 'sine', 0.08), 80)
}

export function playCompleteSound() {
  playTone(523, 0.15, 'sine', 0.12)
  setTimeout(() => playTone(659, 0.15, 'sine', 0.1), 100)
  setTimeout(() => playTone(784, 0.15, 'sine', 0.1), 200)
  setTimeout(() => playTone(1047, 0.3, 'sine', 0.12), 300)
}
