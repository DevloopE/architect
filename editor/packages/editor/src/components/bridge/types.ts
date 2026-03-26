import type { AnyNode, AnyNodeId, AnyNodeType } from '@pascal-app/core'

// ---------------------------------------------------------------------------
// Bridge Command Definitions
// ---------------------------------------------------------------------------
// Each command has a `cmd` discriminator and an `id` for request/response
// correlation over the WebSocket bridge.
// ---------------------------------------------------------------------------

// -- Read commands ----------------------------------------------------------

type ReadStateCommand = {
  cmd: 'read_state'
  id: string
}

type ReadNodesCommand = {
  cmd: 'read_nodes'
  id: string
  /** Optional filter — only return nodes of this type. */
  type?: AnyNodeType
}

type ReadNodeCommand = {
  cmd: 'read_node'
  id: string
  nodeId: AnyNodeId
}

type ReadViewerCommand = {
  cmd: 'read_viewer'
  id: string
}

type ReadEditorCommand = {
  cmd: 'read_editor'
  id: string
}

type ReadAssetsCommand = {
  cmd: 'read_assets'
  id: string
  /** Optional filter — only return assets in this category. */
  category?: string
}

// -- Mutation commands: nodes -----------------------------------------------

type CreateNodeCommand = {
  cmd: 'create_node'
  id: string
  node: AnyNode
  parentId?: AnyNodeId
}

type CreateNodesCommand = {
  cmd: 'create_nodes'
  id: string
  ops: { node: AnyNode; parentId?: AnyNodeId }[]
}

type UpdateNodeCommand = {
  cmd: 'update_node'
  id: string
  nodeId: AnyNodeId
  data: Partial<AnyNode>
}

type UpdateNodesCommand = {
  cmd: 'update_nodes'
  id: string
  updates: { id: AnyNodeId; data: Partial<AnyNode> }[]
}

type DeleteNodeCommand = {
  cmd: 'delete_node'
  id: string
  nodeId: AnyNodeId
}

type DeleteNodesCommand = {
  cmd: 'delete_nodes'
  id: string
  nodeIds: AnyNodeId[]
}

// -- Viewer state commands --------------------------------------------------

type SetSelectionCommand = {
  cmd: 'set_selection'
  id: string
  selection: {
    buildingId?: string | null
    levelId?: string | null
    zoneId?: string | null
    selectedIds?: string[]
  }
}

type SetCameraCommand = {
  cmd: 'set_camera'
  id: string
  cameraMode?: 'perspective' | 'orthographic'
  levelMode?: 'stacked' | 'exploded' | 'solo' | 'manual'
  wallMode?: 'up' | 'cutaway' | 'down'
}

type SetDisplayCommand = {
  cmd: 'set_display'
  id: string
  showScans?: boolean
  showGuides?: boolean
  showGrid?: boolean
  theme?: 'light' | 'dark'
  unit?: 'metric' | 'imperial'
}

// -- Editor state commands --------------------------------------------------

type SetToolCommand = {
  cmd: 'set_tool'
  id: string
  phase?: 'site' | 'structure' | 'furnish'
  mode?: 'select' | 'edit' | 'delete' | 'build'
  tool?: string | null
}

// -- History commands -------------------------------------------------------

type UndoCommand = {
  cmd: 'undo'
  id: string
}

type RedoCommand = {
  cmd: 'redo'
  id: string
}

// -- Scene commands ---------------------------------------------------------

type ClearCommand = {
  cmd: 'clear'
  id: string
}

type ExportCommand = {
  cmd: 'export'
  id: string
}

// -- Collection commands ----------------------------------------------------

type CreateCollectionCommand = {
  cmd: 'create_collection'
  id: string
  name: string
  nodeIds?: AnyNodeId[]
}

type UpdateCollectionCommand = {
  cmd: 'update_collection'
  id: string
  collectionId: string
  data: { name?: string }
}

type DeleteCollectionCommand = {
  cmd: 'delete_collection'
  id: string
  collectionId: string
}

type AddToCollectionCommand = {
  cmd: 'add_to_collection'
  id: string
  collectionId: string
  nodeId: AnyNodeId
}

type RemoveFromCollectionCommand = {
  cmd: 'remove_from_collection'
  id: string
  collectionId: string
  nodeId: AnyNodeId
}

// ---------------------------------------------------------------------------
// Union type
// ---------------------------------------------------------------------------

export type BridgeCommand =
  | ReadStateCommand
  | ReadNodesCommand
  | ReadNodeCommand
  | ReadViewerCommand
  | ReadEditorCommand
  | ReadAssetsCommand
  | CreateNodeCommand
  | CreateNodesCommand
  | UpdateNodeCommand
  | UpdateNodesCommand
  | DeleteNodeCommand
  | DeleteNodesCommand
  | SetSelectionCommand
  | SetCameraCommand
  | SetDisplayCommand
  | SetToolCommand
  | UndoCommand
  | RedoCommand
  | ClearCommand
  | ExportCommand
  | CreateCollectionCommand
  | UpdateCollectionCommand
  | DeleteCollectionCommand
  | AddToCollectionCommand
  | RemoveFromCollectionCommand

// ---------------------------------------------------------------------------
// Bridge Response
// ---------------------------------------------------------------------------

export type BridgeResponse = {
  id: string
  ok: boolean
  data?: unknown
  error?: string
}
