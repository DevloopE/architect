import {
  useScene, generateId,
  SiteNode, BuildingNode, LevelNode, WallNode, SlabNode, CeilingNode,
  ZoneNode, RoofNode, RoofSegmentNode, ItemNode, DoorNode, WindowNode,
  ScanNode, GuideNode,
} from '@pascal-app/core'
import type { AnyNodeId, CollectionId } from '@pascal-app/core'
import { useViewer } from '@pascal-app/viewer'
import useEditor from '../../store/use-editor'
import { CATALOG_ITEMS } from '../ui/item-catalog/catalog-items'
import type { BridgeCommand, BridgeResponse } from './types'
import { useConstruction } from './construction-store'
import { playConstructionSound, playStepSound, playCompleteSound } from './sound-engine'

// ---------------------------------------------------------------------------
// Zod schema lookup — parse incoming nodes to fill in all defaults
// ---------------------------------------------------------------------------

const NODE_SCHEMAS: Record<string, any> = {
  site: SiteNode,
  building: BuildingNode,
  level: LevelNode,
  wall: WallNode,
  slab: SlabNode,
  ceiling: CeilingNode,
  zone: ZoneNode,
  roof: RoofNode,
  'roof-segment': RoofSegmentNode,
  item: ItemNode,
  door: DoorNode,
  window: WindowNode,
  scan: ScanNode,
  guide: GuideNode,
}

function parseNode(raw: Record<string, unknown>): Record<string, unknown> {
  const nodeType = (raw.type as string) ?? 'node'
  const schema = NODE_SCHEMAS[nodeType]
  if (schema) {
    try {
      return schema.parse(raw)
    } catch {
      // If Zod parse fails, fall back to manual defaults
    }
  }
  // Fallback: add essential defaults manually
  return {
    object: 'node',
    visible: true,
    metadata: {},
    parentId: null,
    children: [],
    ...raw,
    id: raw.id ?? generateId(nodeType === 'roof-segment' ? 'rseg' : nodeType),
  }
}

// ---------------------------------------------------------------------------
// Helper: success / error response builders
// ---------------------------------------------------------------------------

function ok(id: string, data?: unknown): BridgeResponse {
  return { id, ok: true, data }
}

function err(id: string, error: string): BridgeResponse {
  return { id, ok: false, error }
}

// ---------------------------------------------------------------------------
// handleCommand — maps a BridgeCommand to Zustand store actions and returns
// a BridgeResponse.  This runs in the browser (called from BridgeProvider).
// ---------------------------------------------------------------------------

export function handleCommand(cmd: BridgeCommand): BridgeResponse {
  try {
    switch (cmd.cmd) {
      // =====================================================================
      // READ
      // =====================================================================

      case 'read_state': {
        const scene = useScene.getState()
        const viewer = useViewer.getState()
        const editor = useEditor.getState()

        return ok(cmd.id, {
          nodes: scene.nodes,
          rootNodeIds: scene.rootNodeIds,
          collections: scene.collections,
          viewer: {
            selection: viewer.selection,
            cameraMode: viewer.cameraMode,
            theme: viewer.theme,
            unit: viewer.unit,
            levelMode: viewer.levelMode,
            wallMode: viewer.wallMode,
            showScans: viewer.showScans,
            showGuides: viewer.showGuides,
            showGrid: viewer.showGrid,
          },
          editor: {
            phase: editor.phase,
            mode: editor.mode,
            tool: editor.tool,
            structureLayer: editor.structureLayer,
          },
        })
      }

      case 'read_nodes': {
        const { nodes } = useScene.getState()

        if (cmd.type) {
          const filtered: Record<string, unknown> = {}
          for (const [id, node] of Object.entries(nodes)) {
            if (node.type === cmd.type) {
              filtered[id] = node
            }
          }
          return ok(cmd.id, filtered)
        }

        return ok(cmd.id, nodes)
      }

      case 'read_node': {
        const node = useScene.getState().nodes[cmd.nodeId]
        if (!node) {
          return err(cmd.id, `Node not found: ${cmd.nodeId}`)
        }
        return ok(cmd.id, node)
      }

      case 'read_viewer': {
        const viewer = useViewer.getState()
        return ok(cmd.id, {
          selection: viewer.selection,
          cameraMode: viewer.cameraMode,
          theme: viewer.theme,
          unit: viewer.unit,
          levelMode: viewer.levelMode,
          wallMode: viewer.wallMode,
          showScans: viewer.showScans,
          showGuides: viewer.showGuides,
          showGrid: viewer.showGrid,
        })
      }

      case 'read_editor': {
        const editor = useEditor.getState()
        return ok(cmd.id, {
          phase: editor.phase,
          mode: editor.mode,
          tool: editor.tool,
          structureLayer: editor.structureLayer,
        })
      }

      case 'read_assets': {
        if (cmd.category) {
          return ok(
            cmd.id,
            CATALOG_ITEMS.filter((item) => item.category === cmd.category),
          )
        }
        return ok(cmd.id, CATALOG_ITEMS)
      }

      // =====================================================================
      // CREATE
      // =====================================================================

      case 'create_node': {
        const scene = useScene.getState()
        const node = parseNode(cmd.node as any)
        scene.createNode(node as any, cmd.parentId)

        const cStore = useConstruction.getState()
        const nodeType = (node as any).type ?? 'node'
        const nodeName = (node as any).name ?? ''
        const label = nodeName ? `${nodeName} (${nodeType})` : nodeType

        cStore.addEntry({ type: 'create', message: label, nodeId: node.id as string, nodeType })
        cStore.recordCommand('create_node', { node: cmd.node, parentId: cmd.parentId })
        if (cStore.soundEnabled) playConstructionSound(nodeType)

        return ok(cmd.id, { nodeId: node.id })
      }

      case 'create_nodes': {
        const scene = useScene.getState()
        const keysBefore = new Set(Object.keys(scene.nodes))

        scene.createNodes(cmd.ops)

        const keysAfter = Object.keys(useScene.getState().nodes)
        const newIds = keysAfter.filter((k) => !keysBefore.has(k))

        return ok(cmd.id, { nodeIds: newIds })
      }

      // =====================================================================
      // UPDATE
      // =====================================================================

      case 'update_node': {
        useScene.getState().updateNode(cmd.nodeId, cmd.data)
        return ok(cmd.id)
      }

      case 'update_nodes': {
        useScene.getState().updateNodes(cmd.updates)
        return ok(cmd.id)
      }

      // =====================================================================
      // DELETE
      // =====================================================================

      case 'delete_node': {
        useScene.getState().deleteNode(cmd.nodeId)
        return ok(cmd.id)
      }

      case 'delete_nodes': {
        useScene.getState().deleteNodes(cmd.nodeIds)
        return ok(cmd.id)
      }

      // =====================================================================
      // VIEWER STATE
      // =====================================================================

      case 'set_selection': {
        // Cast plain strings from JSON to the branded ID types expected by the store
        useViewer.getState().setSelection(cmd.selection as Parameters<ReturnType<typeof useViewer.getState>['setSelection']>[0])
        return ok(cmd.id)
      }

      case 'set_camera': {
        const viewer = useViewer.getState()
        if (cmd.cameraMode !== undefined) viewer.setCameraMode(cmd.cameraMode)
        if (cmd.levelMode !== undefined) viewer.setLevelMode(cmd.levelMode)
        if (cmd.wallMode !== undefined) viewer.setWallMode(cmd.wallMode)
        return ok(cmd.id)
      }

      case 'set_display': {
        const viewer = useViewer.getState()
        if (cmd.showScans !== undefined) viewer.setShowScans(cmd.showScans)
        if (cmd.showGuides !== undefined) viewer.setShowGuides(cmd.showGuides)
        if (cmd.showGrid !== undefined) viewer.setShowGrid(cmd.showGrid)
        if (cmd.theme !== undefined) viewer.setTheme(cmd.theme)
        if (cmd.unit !== undefined) viewer.setUnit(cmd.unit)
        return ok(cmd.id)
      }

      // =====================================================================
      // EDITOR STATE
      // =====================================================================

      case 'set_tool': {
        const editor = useEditor.getState()
        if (cmd.phase !== undefined) editor.setPhase(cmd.phase)
        if (cmd.mode !== undefined) editor.setMode(cmd.mode)
        if (cmd.tool !== undefined) editor.setTool(cmd.tool as any)
        return ok(cmd.id)
      }

      // =====================================================================
      // HISTORY
      // =====================================================================

      case 'undo': {
        useScene.temporal.getState().undo()
        return ok(cmd.id)
      }

      case 'redo': {
        useScene.temporal.getState().redo()
        return ok(cmd.id)
      }

      // =====================================================================
      // SCENE
      // =====================================================================

      case 'clear': {
        useScene.getState().clearScene()
        useConstruction.getState().clear()
        setTimeout(() => window.location.reload(), 500)
        return ok(cmd.id)
      }

      case 'log' as any: {
        const c = cmd as any
        const cStore = useConstruction.getState()
        cStore.addEntry({ type: c.level ?? 'step', message: c.message ?? '' })
        cStore.recordCommand('log', { message: c.message, level: c.level })
        if (cStore.soundEnabled && (c.level === 'step' || !c.level)) playStepSound()
        return ok(c.id)
      }

      case 'build_start' as any: {
        const cStore = useConstruction.getState()
        cStore.clear()
        cStore.setBuilding(true)
        cStore.startRecording()
        cStore.addEntry({ type: 'info', message: 'Build started' })
        return ok((cmd as any).id)
      }

      case 'build_end' as any: {
        const cStore = useConstruction.getState()
        cStore.setBuilding(false)
        cStore.addEntry({ type: 'done', message: 'Build complete!' })
        if (cStore.soundEnabled) playCompleteSound()
        // Stop recording and make pipeline available for save
        const pipeline = cStore.stopRecording()
        ;(window as any).__lastPipeline = pipeline
        return ok((cmd as any).id, { pipelineLength: pipeline.length })
      }

      case 'get_pipeline' as any: {
        const pipeline = (window as any).__lastPipeline ?? []
        return ok((cmd as any).id, { pipeline })
      }

      case 'export_gltf' as any: {
        try {
          const { exportScene } = useViewer.getState()
          if (exportScene) exportScene()
          return ok((cmd as any).id)
        } catch (e) {
          return err((cmd as any).id, String(e))
        }
      }

      case 'export': {
        const scene = useScene.getState()
        return ok(cmd.id, {
          nodes: scene.nodes,
          rootNodeIds: scene.rootNodeIds,
          collections: scene.collections,
        })
      }

      case 'import' as any: {
        const c = cmd as any
        if (c.nodes && c.rootNodeIds) {
          useScene.getState().setScene(c.nodes, c.rootNodeIds)
        }
        return ok(c.id)
      }

      // =====================================================================
      // COLLECTIONS
      // =====================================================================

      case 'create_collection': {
        const collectionId = useScene
          .getState()
          .createCollection(cmd.name, cmd.nodeIds as AnyNodeId[] | undefined)
        return ok(cmd.id, { collectionId })
      }

      case 'update_collection': {
        useScene.getState().updateCollection(cmd.collectionId as CollectionId, cmd.data)
        return ok(cmd.id)
      }

      case 'delete_collection': {
        useScene.getState().deleteCollection(cmd.collectionId as CollectionId)
        return ok(cmd.id)
      }

      case 'add_to_collection': {
        useScene.getState().addToCollection(cmd.collectionId as CollectionId, cmd.nodeId)
        return ok(cmd.id)
      }

      case 'remove_from_collection': {
        useScene.getState().removeFromCollection(cmd.collectionId as CollectionId, cmd.nodeId)
        return ok(cmd.id)
      }

      default: {
        const exhaustive: never = cmd
        return err((exhaustive as any).id, `Unknown command: ${(exhaustive as any).cmd}`)
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return err(cmd.id, message)
  }
}
