import type { ChangeEvent } from 'react'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { updateDevice, updateDeviceAsync, deleteDeviceAsync } from '../store/devicesSlice'
import { updateConnection } from '../store/connectionsSlice'
import { selectEntity } from '../store/uiSlice'
import type { DeviceType, RootState } from '../store'

// NIST RMF Security Categories and Controls
const NIST_CATEGORIES = {
  'AC': 'Access Control',
  'AU': 'Audit and Accountability',
  'AT': 'Awareness and Training',
  'CM': 'Configuration Management',
  'CP': 'Contingency Planning',
  'IA': 'Identification and Authentication',
  'IR': 'Incident Response',
  'MA': 'Maintenance',
  'MP': 'Media Protection',
  'PS': 'Personnel Security',
  'PE': 'Physical and Environmental Protection',
  'PL': 'Planning',
  'PM': 'Program Management',
  'RA': 'Risk Assessment',
  'CA': 'Security Assessment and Authorization',
  'SC': 'System and Communications Protection',
  'SI': 'System and Information Integrity',
  'SA': 'System and Services Acquisition'
}

const RISK_LEVELS = ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
const IMPACT_LEVELS = ['Low', 'Moderate', 'High']
const COMPLIANCE_STATUS = ['Not Assessed', 'Compliant', 'Non-Compliant', 'Partially Compliant']
const CATEGORIZATION_TYPES = ['Information System', 'Platform IT System', 'Software as a Service']

interface SecurityControl {
  id: string
  category: string
  name: string
  status: 'implemented' | 'planned' | 'not_applicable' | 'not_implemented'
  notes: string
}

const PropertyEditor = () => {
  const dispatch = useDispatch()
  const selected = useSelector((state: RootState) => state.ui.selected)
  const multiSelected = useSelector((state: RootState) => state.ui.multiSelected)
  const devices = useSelector((state: RootState) => state.devices.items)
  const connections = useSelector((state: RootState) => state.connections.items)
  
  // Move useState to top level to follow Rules of Hooks
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'controls' | 'risk'>('general')

  const device = selected?.kind === 'device' ? devices.find((item) => item.id === selected.id) : null
  const connection =
    selected?.kind === 'connection' ? connections.find((item) => item.id === selected.id) : null
  
  // Handle multi-selected devices
  const multiSelectedDevices = multiSelected?.kind === 'device' 
    ? devices.filter(device => multiSelected.ids.includes(device.id))
    : []

  useEffect(() => {
    if (selected && !device && !connection) {
      dispatch(selectEntity(null))
    }
  }, [selected, device, connection, dispatch])

  // Reset tab to 'general' when switching devices
  useEffect(() => {
    if (device || multiSelectedDevices.length > 0) {
      setActiveTab('general')
    }
  }, [device?.id, multiSelectedDevices.length])

  // Show multi-selection editor if multiple devices are selected
  if (multiSelected?.kind === 'device' && multiSelectedDevices.length > 0) {
    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Properties ({multiSelectedDevices.length} devices selected)</h3>
        </header>
        <div className="panel-content">
          <div className="multi-edit-info">
            <p>Editing {multiSelectedDevices.length} devices:</p>
            <ul className="selected-devices-list">
              {multiSelectedDevices.map(device => (
                <li key={device.id}>{device.name} ({device.type})</li>
              ))}
            </ul>
          </div>
          
          <div className="form">
            <label className="form-field">
              <span>Type (applies to all selected)</span>
              <select 
                value=""
                onChange={(e) => {
                  if (e.target.value) {
                    multiSelectedDevices.forEach(device => {
                      dispatch(updateDeviceAsync({ id: device.id, type: e.target.value as DeviceType }))
                    })
                  }
                }}
              >
                <option value="">-- Change Type --</option>
                <option value="switch">Switch</option>
                <option value="router">Router</option>
                <option value="firewall">Firewall</option>
                <option value="server">Server</option>
                <option value="workstation">Workstation</option>
                <option value="generic">Generic</option>
              </select>
            </label>
            
            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-danger" 
                onClick={() => {
                  if (window.confirm(`Delete ${multiSelectedDevices.length} selected devices?`)) {
                    multiSelectedDevices.forEach(device => {
                      dispatch(deleteDeviceAsync(device.id))
                    })
                  }
                }}
              >
                Delete Selected Devices
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!selected || (!device && !connection)) {
    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Properties</h3>
        </header>
        <p className="panel-placeholder">Select a device or connection, or Ctrl+click multiple devices.</p>
      </div>
    )
  }

  if (device) {
    
    // Parse security config from device.config
    const securityConfig = {
      riskLevel: device.config.riskLevel || 'Moderate',
      confidentialityImpact: device.config.confidentialityImpact || 'Moderate',
      integrityImpact: device.config.integrityImpact || 'Moderate',
      availabilityImpact: device.config.availabilityImpact || 'Moderate',
      complianceStatus: device.config.complianceStatus || 'Not Assessed',
      categorizationType: device.config.categorizationType || 'Information System',
      authorizer: device.config.authorizer || '',
      lastAssessment: device.config.lastAssessment || '',
      nextAssessment: device.config.nextAssessment || '',
      securityControls: device.config.securityControls ? JSON.parse(device.config.securityControls) : [],
      vulnerabilities: device.config.vulnerabilities || '0',
      patchLevel: device.config.patchLevel || 'Unknown',
      encryptionStatus: device.config.encryptionStatus || 'Not Configured',
      accessControlPolicy: device.config.accessControlPolicy || 'Standard',
      monitoringEnabled: device.config.monitoringEnabled === 'true',
      backupPolicy: device.config.backupPolicy || 'Standard',
      incidentResponsePlan: device.config.incidentResponsePlan || 'Corporate Standard'
    }

    const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const { name, value, type } = event.target
      const checked = (event.target as HTMLInputElement).checked
      
      if (name === 'name' || name === 'type') {
        const updateData = {
          id: device.id,
          [name]: name === 'type' ? (value as DeviceType) : value,
        }
        // Only update backend - it will update local state when successful
        dispatch(updateDeviceAsync(updateData))
      } else {
        // Update config for security properties
        const newConfig = {
          ...device.config,
          [name]: type === 'checkbox' ? checked.toString() : value
        }
        const updateData = { id: device.id, config: newConfig }
        // Only update backend - it will update local state when successful
        dispatch(updateDeviceAsync(updateData))
      }
    }

    const handleControlUpdate = (controlId: string, updates: Partial<SecurityControl>) => {
      const controls = [...securityConfig.securityControls]
      const index = controls.findIndex(c => c.id === controlId)
      
      if (index >= 0) {
        controls[index] = { ...controls[index], ...updates }
      } else {
        controls.push({
          id: controlId,
          category: updates.category || '',
          name: updates.name || '',
          status: updates.status || 'not_implemented',
          notes: updates.notes || ''
        })
      }
      
      const newConfig = {
        ...device.config,
        securityControls: JSON.stringify(controls)
      }
      const updateData = { id: device.id, config: newConfig }
      // Only update backend - it will update local state when successful
      dispatch(updateDeviceAsync(updateData))
    }

    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Device Properties</h3>
        </header>
        <div className="property-tabs">
          <button 
            className={`tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button 
            className={`tab ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            Security
          </button>
          <button 
            className={`tab ${activeTab === 'controls' ? 'active' : ''}`}
            onClick={() => setActiveTab('controls')}
          >
            Controls
          </button>
          <button 
            className={`tab ${activeTab === 'risk' ? 'active' : ''}`}
            onClick={() => setActiveTab('risk')}
          >
            Risk
          </button>
        </div>
        <div className="panel-content">
          {activeTab === 'general' && (
            <div className="property-section">
              <label className="form-field">
                <span>Name</span>
                <input name="name" value={device.name} onChange={handleChange} />
              </label>
              <label className="form-field">
                <span>Type</span>
                <select name="type" value={device.type} onChange={handleChange}>
                  <option value="switch">Switch</option>
                  <option value="router">Router</option>
                  <option value="firewall">Firewall</option>
                  <option value="server">Server</option>
                  <option value="workstation">Workstation</option>
                  <option value="generic">Generic</option>
                </select>
              </label>
              <label className="form-field">
                <span>System Categorization</span>
                <select name="categorizationType" value={securityConfig.categorizationType} onChange={handleChange}>
                  {CATEGORIZATION_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="property-section">
              <h4>Security Configuration</h4>
              <label className="form-field">
                <span>Patch Level</span>
                <input name="patchLevel" value={securityConfig.patchLevel} onChange={handleChange} placeholder="e.g., Current, 30 days behind" />
              </label>
              <label className="form-field">
                <span>Encryption Status</span>
                <select name="encryptionStatus" value={securityConfig.encryptionStatus} onChange={handleChange}>
                  <option value="Not Configured">Not Configured</option>
                  <option value="Configured">Configured</option>
                  <option value="Full Disk Encryption">Full Disk Encryption</option>
                  <option value="Transit Only">Transit Only</option>
                  <option value="At Rest Only">At Rest Only</option>
                </select>
              </label>
              <label className="form-field">
                <span>Access Control Policy</span>
                <select name="accessControlPolicy" value={securityConfig.accessControlPolicy} onChange={handleChange}>
                  <option value="Standard">Standard</option>
                  <option value="Privileged">Privileged</option>
                  <option value="High Security">High Security</option>
                  <option value="Guest">Guest</option>
                </select>
              </label>
              <label className="form-field checkbox-field">
                <input 
                  type="checkbox" 
                  name="monitoringEnabled" 
                  checked={securityConfig.monitoringEnabled} 
                  onChange={handleChange} 
                />
                <span>Security Monitoring Enabled</span>
              </label>
              <label className="form-field">
                <span>Backup Policy</span>
                <select name="backupPolicy" value={securityConfig.backupPolicy} onChange={handleChange}>
                  <option value="Standard">Standard (Daily)</option>
                  <option value="Critical">Critical (Real-time)</option>
                  <option value="Weekly">Weekly</option>
                  <option value="None">None</option>
                </select>
              </label>
            </div>
          )}

          {activeTab === 'controls' && (
            <div className="property-section">
              <h4>NIST Security Controls</h4>
              <div className="controls-grid">
                {Object.entries(NIST_CATEGORIES).map(([code, name]) => {
                  const control = securityConfig.securityControls.find((c: SecurityControl) => c.category === code)
                  return (
                    <div key={code} className="control-item">
                      <div className="control-header">
                        <strong>{code}</strong> - {name}
                      </div>
                      <select 
                        value={control?.status || 'not_implemented'}
                        onChange={(e) => handleControlUpdate(`${code}-1`, {
                          category: code,
                          name: name,
                          status: e.target.value as SecurityControl['status']
                        })}
                      >
                        <option value="not_implemented">Not Implemented</option>
                        <option value="planned">Planned</option>
                        <option value="implemented">Implemented</option>
                        <option value="not_applicable">Not Applicable</option>
                      </select>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="property-section">
              <h4>Risk Assessment & Impact</h4>
              <label className="form-field">
                <span>Overall Risk Level</span>
                <select name="riskLevel" value={securityConfig.riskLevel} onChange={handleChange}>
                  {RISK_LEVELS.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </label>
              
              <div className="impact-levels">
                <h5>Impact Levels (FIPS 199)</h5>
                <label className="form-field">
                  <span>Confidentiality Impact</span>
                  <select name="confidentialityImpact" value={securityConfig.confidentialityImpact} onChange={handleChange}>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Integrity Impact</span>
                  <select name="integrityImpact" value={securityConfig.integrityImpact} onChange={handleChange}>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Availability Impact</span>
                  <select name="availabilityImpact" value={securityConfig.availabilityImpact} onChange={handleChange}>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="form-field">
                <span>Compliance Status</span>
                <select name="complianceStatus" value={securityConfig.complianceStatus} onChange={handleChange}>
                  {COMPLIANCE_STATUS.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span>Known Vulnerabilities</span>
                <input 
                  name="vulnerabilities" 
                  type="number" 
                  min="0"
                  value={securityConfig.vulnerabilities} 
                  onChange={handleChange} 
                />
              </label>

              <label className="form-field">
                <span>Authorizing Official</span>
                <input name="authorizer" value={securityConfig.authorizer} onChange={handleChange} placeholder="Name of AO" />
              </label>

              <label className="form-field">
                <span>Last Assessment Date</span>
                <input name="lastAssessment" type="date" value={securityConfig.lastAssessment} onChange={handleChange} />
              </label>

              <label className="form-field">
                <span>Next Assessment Due</span>
                <input name="nextAssessment" type="date" value={securityConfig.nextAssessment} onChange={handleChange} />
              </label>
            </div>
          )}
        </div>
      </div>
    )
  }

  const handleConnectionChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target
    dispatch(updateConnection({ id: connection!.id, [name]: value }))
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <h3>Connection Properties</h3>
      </header>
      <div className="panel-content">
        <label className="form-field">
          <span>Source</span>
          <input
            name="sourceDeviceId"
            value={connection!.sourceDeviceId}
            onChange={handleConnectionChange}
          />
        </label>
        <label className="form-field">
          <span>Target</span>
          <input
            name="targetDeviceId"
            value={connection!.targetDeviceId}
            onChange={handleConnectionChange}
          />
        </label>
        <label className="form-field">
          <span>Link type</span>
          <input name="linkType" value={connection!.linkType} onChange={handleConnectionChange} />
        </label>
      </div>
    </div>
  )
}

export default PropertyEditor

