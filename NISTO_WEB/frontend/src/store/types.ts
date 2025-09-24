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

export interface HistoryState {
  canUndo: boolean
  canRedo: boolean
}

export interface UiState {
  selected: SelectedEntity
  history: HistoryState
}

export interface RootState {
  devices: DevicesState
  connections: ConnectionsState
  ui: UiState
}

