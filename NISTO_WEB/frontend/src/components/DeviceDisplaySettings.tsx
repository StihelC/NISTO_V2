import React from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { RootState } from '../store'
import { updateDeviceDisplayPreferences, resetDeviceDisplayPreferences } from '../store/uiSlice'
import type { DeviceDisplayPreferences } from '../store/types'

interface DeviceDisplaySettingsProps {
  isOpen: boolean
  onClose: () => void
}

const DeviceDisplaySettings: React.FC<DeviceDisplaySettingsProps> = ({ isOpen, onClose }) => {
  const dispatch = useDispatch()
  const preferences = useSelector((state: RootState) => state.ui.deviceDisplayPreferences)

  const handleToggle = (key: keyof DeviceDisplayPreferences) => {
    dispatch(updateDeviceDisplayPreferences({
      [key]: !preferences[key]
    }))
  }

  const handleReset = () => {
    dispatch(resetDeviceDisplayPreferences())
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Device Display Settings</h2>
          <button type="button" className="close-button" onClick={onClose}>
            ×
          </button>
        </div>
        
        <div className="modal-content">
          <p className="modal-description">
            Choose which properties to display below device icons on the topology canvas.
          </p>
          
          <div className="settings-section">
            <h3>General Properties</h3>
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showDeviceName}
                  onChange={() => handleToggle('showDeviceName')}
                />
                <span className="checkbox-text">Device Name</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showDeviceType}
                  onChange={() => handleToggle('showDeviceType')}
                />
                <span className="checkbox-text">Device Type</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showCategorizationType}
                  onChange={() => handleToggle('showCategorizationType')}
                />
                <span className="checkbox-text">System Categorization</span>
              </label>
            </div>
          </div>

          <div className="settings-section">
            <h3>Security Properties</h3>
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showPatchLevel}
                  onChange={() => handleToggle('showPatchLevel')}
                />
                <span className="checkbox-text">Patch Level</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showEncryptionStatus}
                  onChange={() => handleToggle('showEncryptionStatus')}
                />
                <span className="checkbox-text">Encryption Status</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showAccessControlPolicy}
                  onChange={() => handleToggle('showAccessControlPolicy')}
                />
                <span className="checkbox-text">Access Control Policy</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showMonitoringEnabled}
                  onChange={() => handleToggle('showMonitoringEnabled')}
                />
                <span className="checkbox-text">Security Monitoring</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showBackupPolicy}
                  onChange={() => handleToggle('showBackupPolicy')}
                />
                <span className="checkbox-text">Backup Policy</span>
              </label>
            </div>
          </div>

          <div className="settings-section">
            <h3>Risk & Assessment Properties</h3>
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showRiskLevel}
                  onChange={() => handleToggle('showRiskLevel')}
                />
                <span className="checkbox-text">Risk Level</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showConfidentialityImpact}
                  onChange={() => handleToggle('showConfidentialityImpact')}
                />
                <span className="checkbox-text">Confidentiality Impact</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showIntegrityImpact}
                  onChange={() => handleToggle('showIntegrityImpact')}
                />
                <span className="checkbox-text">Integrity Impact</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showAvailabilityImpact}
                  onChange={() => handleToggle('showAvailabilityImpact')}
                />
                <span className="checkbox-text">Availability Impact</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showComplianceStatus}
                  onChange={() => handleToggle('showComplianceStatus')}
                />
                <span className="checkbox-text">Compliance Status</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showVulnerabilities}
                  onChange={() => handleToggle('showVulnerabilities')}
                />
                <span className="checkbox-text">Known Vulnerabilities</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showAuthorizer}
                  onChange={() => handleToggle('showAuthorizer')}
                />
                <span className="checkbox-text">Authorizing Official</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showLastAssessment}
                  onChange={() => handleToggle('showLastAssessment')}
                />
                <span className="checkbox-text">Last Assessment Date</span>
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.showNextAssessment}
                  onChange={() => handleToggle('showNextAssessment')}
                />
                <span className="checkbox-text">Next Assessment Due</span>
              </label>
            </div>
          </div>
          
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={handleReset}>
              Reset to Defaults
            </button>
            <button type="button" className="primary-button" onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DeviceDisplaySettings
