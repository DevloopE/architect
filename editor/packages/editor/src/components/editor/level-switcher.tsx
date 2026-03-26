'use client'

import {
  type AnyNodeId,
  type BuildingNode,
  type LevelNode,
  useScene,
} from '@pascal-app/core'
import { useViewer } from '@pascal-app/viewer'
import { Layers } from 'lucide-react'
import { useCallback, useMemo } from 'react'
import { cn } from '../../lib/utils'

export function EditorLevelSwitcher() {
  const selection = useViewer((s) => s.selection)
  const levelMode = useViewer((s) => s.levelMode)
  const nodes = useScene((s) => s.nodes)

  const building = selection.buildingId
    ? (nodes[selection.buildingId] as BuildingNode | undefined)
    : null

  const levels = useMemo(
    () =>
      building?.children
        .map((id) => nodes[id as AnyNodeId] as LevelNode | undefined)
        .filter((n): n is LevelNode => n?.type === 'level')
        .sort((a, b) => b.level - a.level) ?? [],
    [building?.children, nodes],
  )

  const handleLevelClick = useCallback(
    (levelId: LevelNode['id']) => {
      const viewer = useViewer.getState()
      viewer.setSelection({ levelId })
      if (levelMode === 'stacked' || levelMode === 'manual') {
        viewer.setLevelMode('solo')
      }
    },
    [levelMode],
  )

  const handleShowAll = useCallback(() => {
    const viewer = useViewer.getState()
    viewer.setLevelMode(levelMode === 'solo' ? 'stacked' : 'solo')
  }, [levelMode])

  if (!building || levels.length < 2) return null

  const isSolo = levelMode === 'solo'

  return (
    <div className="fixed top-1/2 right-4 z-30 -translate-y-1/2 text-foreground">
      <div className="pointer-events-auto flex flex-col items-center gap-1 rounded-2xl border border-border/40 bg-background/95 p-1.5 shadow-lg backdrop-blur-xl">
        <button
          className={cn(
            'flex h-7 w-full items-center justify-center rounded-lg px-2 text-[10px] font-semibold uppercase tracking-wider transition-colors',
            isSolo
              ? 'bg-violet-500/20 text-violet-400'
              : 'text-muted-foreground hover:bg-white/10 hover:text-foreground',
          )}
          onClick={handleShowAll}
          title={isSolo ? 'Show all floors (stacked)' : 'Isolate selected floor (solo)'}
        >
          {isSolo ? 'Solo' : 'All'}
        </button>

        <div className="my-0.5 h-px w-full bg-border/40" />

        {levels.map((lvl) => {
          const isSelected = lvl.id === selection.levelId
          const label = lvl.name || `L${lvl.level}`
          return (
            <button
              className={cn(
                'group relative flex h-8 w-12 items-center justify-center rounded-lg text-xs font-medium transition-all duration-150',
                isSelected
                  ? 'bg-white/15 text-foreground shadow-sm'
                  : 'text-muted-foreground hover:bg-white/10 hover:text-foreground',
              )}
              key={lvl.id}
              onClick={() => handleLevelClick(lvl.id)}
              title={lvl.name || `Level ${lvl.level}`}
            >
              <div className="flex flex-col items-center gap-0.5">
                <Layers
                  className={cn(
                    'h-3 w-3 transition-opacity',
                    isSelected ? 'opacity-100' : 'opacity-50',
                  )}
                />
                <span className="leading-none">{label}</span>
              </div>
              {isSelected && (
                <div className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-violet-400" />
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
