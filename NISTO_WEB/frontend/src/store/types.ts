export type DeviceType = 'switch' | 'router' | 'firewall' | 'server' | 'workstation' | 'generic'

export interface Device {
  id: string
  name: string
  type: DeviceType
  config: Record<string, string>
  position?: {
    x: number
    y: number
  }
}

export interface DevicesState {
  items: Device[]
}

export interface Connection {
  id: string
  sourceDeviceId: string
  targetDeviceId: string
  linkType: string
  properties: Record<string, string>
}

export interface ConnectionsState {
  items: Connection[]
}

export type SelectedEntity =
  | { kind: 'device'; id: string }
  | { kind: 'connection'; id: string }
  | null

export interface MultiSelection {
  kind: 'device' | 'connection'
  ids: string[]
}

export interface HistoryState {
  canUndo: boolean
  canRedo: boolean
}

export interface UiState {
  selected: SelectedEntity
  multiSelected: MultiSelection | null
  history: HistoryState
}

export interface ProjectsState {
  projects: any[]
  currentProject: any | null
  isLoading: boolean
  error: string | null
  autoSaving: boolean
  lastAutoSave: string | null
}

export interface RootState {
  devices: DevicesState
  connections: ConnectionsState
  ui: UiState
  projects: ProjectsState
}

