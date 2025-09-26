import type { DeviceType } from '../../store'

export type DeviceTab = 'general' | 'security' | 'controls' | 'risk'
export type BulkDeviceTab = 'general' | 'security' | 'risk' | 'connections'
export type BoundaryTab = 'general' | 'security' | 'risk'

export interface SecurityControl {
  id: string
  category: string
  name: string
  status: 'implemented' | 'planned' | 'not_applicable' | 'not_implemented'
  notes: string
}

export interface DeviceSecurityConfig {
  riskLevel: string
  confidentialityImpact: string
  integrityImpact: string
  availabilityImpact: string
  complianceStatus: string
  categorizationType: string
  authorizer: string
  lastAssessment: string
  nextAssessment: string
  securityControls: SecurityControl[]
  vulnerabilities: string
  patchLevel: string
  encryptionStatus: string
  accessControlPolicy: string
  monitoringEnabled: boolean
  backupPolicy: string
  incidentResponsePlan: string
}

export interface BulkDeviceChange {
  field: string
  value: unknown
}

export interface DeviceTabProps {
  activeTab: DeviceTab
  onTabChange: (tab: DeviceTab) => void
}

export interface DeviceGeneralTabProps {
  name: string
  type: DeviceType
  categorizationType: string
  onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
}

