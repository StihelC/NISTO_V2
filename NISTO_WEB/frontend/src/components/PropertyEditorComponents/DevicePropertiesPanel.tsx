import type { ChangeEvent } from 'react'

import DeviceGeneralTab from './DeviceGeneralTab'
import DeviceSecurityTab from './DeviceSecurityTab'
import DeviceControlsTab from './DeviceControlsTab'
import DeviceRiskTab from './DeviceRiskTab'
import DeviceTabs from './DeviceTabs'
import type { DeviceSecurityConfig, DeviceTab, SecurityControl } from './types'

interface DevicePropertiesPanelProps {
  name: string
  type: string
  securityConfig: DeviceSecurityConfig
  activeTab: DeviceTab
  onTabChange: (tab: DeviceTab) => void
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void
  onControlUpdate: (controlId: string, updates: Partial<SecurityControl>) => void
}

const DevicePropertiesPanel = ({
  name,
  type,
  securityConfig,
  activeTab,
  onTabChange,
  onChange,
  onControlUpdate,
}: DevicePropertiesPanelProps) => (
  <div className="panel">
    <header className="panel-header">
      <h3>Device Properties</h3>
    </header>
    <DeviceTabs activeTab={activeTab} onTabChange={onTabChange} />
    <div className="panel-content">
      {activeTab === 'general' && (
        <DeviceGeneralTab
          name={name}
          type={type as any}
          categorizationType={securityConfig.categorizationType}
          onChange={onChange}
        />
      )}
      {activeTab === 'security' && (
        <DeviceSecurityTab
          patchLevel={securityConfig.patchLevel}
          encryptionStatus={securityConfig.encryptionStatus}
          accessControlPolicy={securityConfig.accessControlPolicy}
          monitoringEnabled={securityConfig.monitoringEnabled}
          backupPolicy={securityConfig.backupPolicy}
          onChange={onChange}
        />
      )}
      {activeTab === 'controls' && (
        <DeviceControlsTab controls={securityConfig.securityControls} onUpdate={onControlUpdate} />
      )}
      {activeTab === 'risk' && (
        <DeviceRiskTab
          riskLevel={securityConfig.riskLevel}
          confidentialityImpact={securityConfig.confidentialityImpact}
          integrityImpact={securityConfig.integrityImpact}
          availabilityImpact={securityConfig.availabilityImpact}
          complianceStatus={securityConfig.complianceStatus}
          vulnerabilities={securityConfig.vulnerabilities}
          authorizer={securityConfig.authorizer}
          lastAssessment={securityConfig.lastAssessment}
          nextAssessment={securityConfig.nextAssessment}
          onChange={onChange}
        />
      )}
    </div>
  </div>
)

export default DevicePropertiesPanel

