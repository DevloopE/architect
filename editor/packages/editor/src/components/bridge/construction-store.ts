'use client'

import { create } from 'zustand'

export type LogEntry = {
  id: number
  timestamp: number
  type: 'step' | 'create' | 'info' | 'error' | 'done'
  message: string
  nodeId?: string
  nodeType?: string
}

export type RecordedCommand = {
  ts: number // ms from build start
  cmd: string
  payload: Record<string, unknown>
}

type ConstructionStore = {
  // Log panel
  entries: LogEntry[]
  isBuilding: boolean

  // Recording
  isRecording: boolean
  recordStartTime: number
  recordedCommands: RecordedCommand[]

  // Replay
  isReplaying: boolean
  replaySpeed: number
  replayProgress: number // 0-1
  replayTotal: number

  // Sound
  soundEnabled: boolean

  // Actions
  addEntry: (entry: Omit<LogEntry, 'id' | 'timestamp'>) => void
  clear: () => void
  setBuilding: (v: boolean) => void

  startRecording: () => void
  recordCommand: (cmd: string, payload: Record<string, unknown>) => void
  stopRecording: () => RecordedCommand[]

  setReplaying: (v: boolean) => void
  setReplaySpeed: (s: number) => void
  setReplayProgress: (p: number, total: number) => void
  setSoundEnabled: (v: boolean) => void
}

let nextId = 0

export const useConstruction = create<ConstructionStore>((set, get) => ({
  entries: [],
  isBuilding: false,

  isRecording: false,
  recordStartTime: 0,
  recordedCommands: [],

  isReplaying: false,
  replaySpeed: 1,
  replayProgress: 0,
  replayTotal: 0,

  soundEnabled: true,

  addEntry: (entry) =>
    set((state) => ({
      entries: [
        ...state.entries.slice(-100),
        { ...entry, id: nextId++, timestamp: Date.now() },
      ],
    })),

  clear: () => set({ entries: [], recordedCommands: [] }),

  setBuilding: (v) => set({ isBuilding: v }),

  startRecording: () =>
    set({ isRecording: true, recordStartTime: Date.now(), recordedCommands: [] }),

  recordCommand: (cmd, payload) => {
    const state = get()
    if (!state.isRecording) return
    const ts = Date.now() - state.recordStartTime
    set((s) => ({
      recordedCommands: [...s.recordedCommands, { ts, cmd, payload }],
    }))
  },

  stopRecording: () => {
    const cmds = get().recordedCommands
    set({ isRecording: false })
    return cmds
  },

  setReplaying: (v) => set({ isReplaying: v }),
  setReplaySpeed: (s) => set({ replaySpeed: s }),
  setReplayProgress: (p, total) => set({ replayProgress: p, replayTotal: total }),
  setSoundEnabled: (v) => set({ soundEnabled: v }),
}))
