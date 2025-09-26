import type { DeviceDisplayPreferences } from '../../store/types'

interface DeviceDisplayTabProps {
  displayPreferences: DeviceDisplayPreferences
  onChange: (preferences: Partial<DeviceDisplayPreferences>) => void
}

const DeviceDisplayTab = ({ displayPreferences, onChange }: DeviceDisplayTabProps) => {
  const handleToggle = (key: keyof DeviceDisplayPreferences) => {
    onChange({
      [key]: !displayPreferences[key]
    })
  }

  return (
    <div className="property-section">
      <h4>Display Properties</h4>
      <p className="section-description">
        Choose which properties to display below this device's icon on the topology canvas.
      </p>
      
      <div className="settings-section">
        <h5>General Properties</h5>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showDeviceName}
              onChange={() => handleToggle('showDeviceName')}
            />
            <span className="checkbox-text">Device Name</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showDeviceType}
              onChange={() => handleToggle('showDeviceType')}
            />
            <span className="checkbox-text">Device Type</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showCategorizationType}
              onChange={() => handleToggle('showCategorizationType')}
            />
            <span className="checkbox-text">System Categorization</span>
          </label>
        </div>
      </div>

      <div className="settings-section">
        <h5>Security Properties</h5>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showPatchLevel}
              onChange={() => handleToggle('showPatchLevel')}
            />
            <span className="checkbox-text">Patch Level</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showEncryptionStatus}
              onChange={() => handleToggle('showEncryptionStatus')}
            />
            <span className="checkbox-text">Encryption Status</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showAccessControlPolicy}
              onChange={() => handleToggle('showAccessControlPolicy')}
            />
            <span className="checkbox-text">Access Control Policy</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showMonitoringEnabled}
              onChange={() => handleToggle('showMonitoringEnabled')}
            />
            <span className="checkbox-text">Security Monitoring</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showBackupPolicy}
              onChange={() => handleToggle('showBackupPolicy')}
            />
            <span className="checkbox-text">Backup Policy</span>
          </label>
        </div>
      </div>

      <div className="settings-section">
        <h5>Risk & Assessment Properties</h5>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showRiskLevel}
              onChange={() => handleToggle('showRiskLevel')}
            />
            <span className="checkbox-text">Risk Level</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showConfidentialityImpact}
              onChange={() => handleToggle('showConfidentialityImpact')}
            />
            <span className="checkbox-text">Confidentiality Impact</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showIntegrityImpact}
              onChange={() => handleToggle('showIntegrityImpact')}
            />
            <span className="checkbox-text">Integrity Impact</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showAvailabilityImpact}
              onChange={() => handleToggle('showAvailabilityImpact')}
            />
            <span className="checkbox-text">Availability Impact</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showComplianceStatus}
              onChange={() => handleToggle('showComplianceStatus')}
            />
            <span className="checkbox-text">Compliance Status</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showVulnerabilities}
              onChange={() => handleToggle('showVulnerabilities')}
            />
            <span className="checkbox-text">Known Vulnerabilities</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showAuthorizer}
              onChange={() => handleToggle('showAuthorizer')}
            />
            <span className="checkbox-text">Authorizing Official</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showLastAssessment}
              onChange={() => handleToggle('showLastAssessment')}
            />
            <span className="checkbox-text">Last Assessment Date</span>
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={displayPreferences.showNextAssessment}
              onChange={() => handleToggle('showNextAssessment')}
            />
            <span className="checkbox-text">Next Assessment Due</span>
          </label>
        </div>
      </div>
    </div>
  )
}

export default DeviceDisplayTab
