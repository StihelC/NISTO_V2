export type DeviceType = 
  // Network Infrastructure
  | 'switch' | 'router' | 'firewall' | 'load-balancer' | 'proxy' | 'gateway' | 'modem' | 'access-point' | 'wireless-controller'
  // Security Devices
  | 'ids-ips' | 'waf' | 'vpn-concentrator' | 'security-appliance' | 'utm' | 'dlp' | 'siem'
  // Servers & Compute
  | 'server' | 'web-server' | 'database-server' | 'file-server' | 'mail-server' | 'dns-server' | 'dhcp-server' | 'domain-controller'
  | 'hypervisor' | 'vm' | 'container' | 'kubernetes-node' | 'docker-host'
  // Storage
  | 'nas' | 'san' | 'storage-array' | 'backup-server' | 'tape-library'
  // Endpoints
  | 'workstation' | 'laptop' | 'desktop' | 'thin-client' | 'tablet' | 'smartphone' | 'pos-terminal' | 'kiosk'
  // IoT & Embedded
  | 'iot-device' | 'sensor' | 'camera' | 'ip-phone' | 'printer' | 'scanner' | 'badge-reader' | 'smart-tv'
  // Cloud Services - AWS
  | 'aws-ec2' | 'aws-rds' | 'aws-s3' | 'aws-lambda' | 'aws-ecs' | 'aws-eks' | 'aws-elb' | 'aws-cloudfront' | 'aws-api-gateway'
  | 'aws-vpc' | 'aws-route53' | 'aws-iam' | 'aws-cloudwatch' | 'aws-sqs' | 'aws-sns' | 'aws-dynamodb'
  // Cloud Services - Azure
  | 'azure-vm' | 'azure-sql' | 'azure-storage' | 'azure-functions' | 'azure-aks' | 'azure-app-service' | 'azure-load-balancer'
  | 'azure-cdn' | 'azure-api-management' | 'azure-vnet' | 'azure-dns' | 'azure-ad' | 'azure-monitor' | 'azure-service-bus'
  // Cloud Services - GCP
  | 'gcp-compute' | 'gcp-cloud-sql' | 'gcp-storage' | 'gcp-functions' | 'gcp-gke' | 'gcp-app-engine' | 'gcp-load-balancer'
  // Operating Systems
  | 'windows-server' | 'linux-server' | 'ubuntu-server' | 'centos-server' | 'redhat-server' | 'debian-server'
  | 'windows-10' | 'windows-11' | 'macos' | 'ubuntu-desktop' | 'android' | 'ios'
  // Monitoring & Management
  | 'monitoring-server' | 'log-server' | 'nms' | 'orchestrator' | 'automation-server'
  // Legacy & Mainframe
  | 'mainframe' | 'as400' | 'legacy-system'
  // Generic
  | 'generic' | 'unknown'

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

export type BoundaryType = 'ato' | 'building' | 'network_segment' | 'security_zone' | 'physical_location' | 'logical_group'

export interface Boundary {
  id: string
  type: BoundaryType
  label: string
  points: Array<{ x: number; y: number }>
  closed: boolean
  style: {
    color: string
    strokeWidth: number
    dashArray?: string
    fill?: string
    fillOpacity?: number
  }
  created: string
  // New device-like properties
  position?: {
    x: number
    y: number
    width: number
    height: number
  }
  x?: number
  y?: number
  width?: number
  height?: number
  config: Record<string, string>
}

export interface ConnectionsState {
  items: Connection[]
}

export interface BoundariesState {
  items: Boundary[]
  isDrawing: boolean
  currentBoundaryType: BoundaryType | null
  drawingPoints: Array<{ x: number; y: number }>
}

export type SelectedEntity =
  | { kind: 'device'; id: string }
  | { kind: 'connection'; id: string }
  | { kind: 'boundary'; id: string }
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
  boundaries: BoundariesState
  ui: UiState
  projects: ProjectsState
}

