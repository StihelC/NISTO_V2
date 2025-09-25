import type { ChangeEvent } from 'react'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { updateDevice, updateDeviceAsync, deleteDeviceAsync } from '../store/devicesSlice'
import { updateConnection, createConnectionAsync, fetchConnections } from '../store/connectionsSlice'
import { updateBoundaryAsync, deleteBoundaryAsync, BOUNDARY_LABELS } from '../store/boundariesSlice'
import { selectEntity } from '../store/uiSlice'
import type { DeviceType, RootState } from '../store'
import { DEVICE_CATEGORIES, DEVICE_LABELS } from '../constants/deviceTypes'
import DeviceIcon from './DeviceIcon'

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
  const boundaries = useSelector((state: RootState) => state.boundaries.items)
  
  // Move useState to top level to follow Rules of Hooks
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'controls' | 'risk'>('general')
  const [connectionType, setConnectionType] = useState('ethernet')

  const device = selected?.kind === 'device' ? devices.find((item) => item.id === selected.id) : null
  const connection =
    selected?.kind === 'connection' ? connections.find((item) => item.id === selected.id) : null
  const boundary = selected?.kind === 'boundary' ? boundaries.find((item) => item.id === selected.id) : null
  
  // Handle multi-selected devices
  const multiSelectedDevices = multiSelected?.kind === 'device' 
    ? devices.filter(device => multiSelected.ids.includes(device.id))
    : []

  // Debug boundary selection
  console.log('🔍 PropertyEditor render - selected:', selected)
  console.log('🔍 PropertyEditor render - boundaries.length:', boundaries.length)
  if (selected?.kind === 'boundary') {
    console.log('🎯 PropertyEditor sees boundary selection:', selected)
    console.log('🎯 Found boundary object:', boundary)
    console.log('🎯 boundary config:', boundary?.config)
    console.log('🎯 device:', device)
    console.log('🎯 connection:', connection)
    console.log('🎯 multiSelectedDevices.length:', multiSelectedDevices.length)
  }

  // Auto-connect functions
  const calculateDistance = (device1: any, device2: any) => {
    if (!device1.position || !device2.position) return Infinity
    const dx = device1.position.x - device2.position.x
    const dy = device1.position.y - device2.position.y
    return Math.sqrt(dx * dx + dy * dy)
  }

  const connectNearestNeighbor = async () => {
    if (multiSelectedDevices.length < 2) return
    
    const connectionPromises: Promise<any>[] = []
    
    multiSelectedDevices.forEach((device, index) => {
      if (index === multiSelectedDevices.length - 1) return // Skip last device
      
      // Find nearest unconnected device
      let nearestDevice = null
      let nearestDistance = Infinity
      
      for (let i = index + 1; i < multiSelectedDevices.length; i++) {
        const otherDevice = multiSelectedDevices[i]
        const distance = calculateDistance(device, otherDevice)
        
        if (distance < nearestDistance) {
          nearestDistance = distance
          nearestDevice = otherDevice
        }
      }
      
      if (nearestDevice) {
        connectionPromises.push(
          dispatch(createConnectionAsync({
            sourceDeviceId: device.id,
            targetDeviceId: nearestDevice.id,
            linkType: connectionType
          }))
        )
      }
    })
    
    // Wait for all connections to be created (but don't auto-draw)
    await Promise.all(connectionPromises)
  }

  const connectStar = async () => {
    if (multiSelectedDevices.length < 2) return
    
    const centerDevice = multiSelectedDevices[0] // Use first as center
    const connectionPromises: Promise<any>[] = []
    
    for (let i = 1; i < multiSelectedDevices.length; i++) {
      connectionPromises.push(
        dispatch(createConnectionAsync({
          sourceDeviceId: centerDevice.id,
          targetDeviceId: multiSelectedDevices[i].id,
          linkType: connectionType
        }))
      )
    }
    
    await Promise.all(connectionPromises)
  }

  const connectChain = async () => {
    if (multiSelectedDevices.length < 2) return
    
    const connectionPromises: Promise<any>[] = []
    
    for (let i = 0; i < multiSelectedDevices.length - 1; i++) {
      connectionPromises.push(
        dispatch(createConnectionAsync({
          sourceDeviceId: multiSelectedDevices[i].id,
          targetDeviceId: multiSelectedDevices[i + 1].id,
          linkType: connectionType
        }))
      )
    }
    
    await Promise.all(connectionPromises)
  }

  const connectMesh = async () => {
    if (multiSelectedDevices.length < 2) return
    
    const connectionPromises: Promise<any>[] = []
    
    for (let i = 0; i < multiSelectedDevices.length; i++) {
      for (let j = i + 1; j < multiSelectedDevices.length; j++) {
        connectionPromises.push(
          dispatch(createConnectionAsync({
            sourceDeviceId: multiSelectedDevices[i].id,
            targetDeviceId: multiSelectedDevices[j].id,
            linkType: connectionType
          }))
        )
      }
    }
    
    await Promise.all(connectionPromises)
  }

  const drawConnections = () => {
    // Force refresh connections to ensure visual lines are drawn
    dispatch(fetchConnections())
  }

  useEffect(() => {
    if (selected && !device && !connection && !boundary) {
      dispatch(selectEntity(null))
    }
  }, [selected, device, connection, boundary, dispatch])

  // Reset tab to 'general' when switching devices
  useEffect(() => {
    if (device || multiSelectedDevices.length > 0) {
      setActiveTab('general')
    }
  }, [device?.id, multiSelectedDevices.length])

  // Show multi-selection editor if multiple devices are selected
  if (multiSelected?.kind === 'device' && multiSelectedDevices.length > 0) {
    // Multi-device bulk editing handler
    const handleBulkChange = (field: string, value: any) => {
      multiSelectedDevices.forEach(device => {
        if (field === 'type') {
          dispatch(updateDeviceAsync({ id: device.id, type: value as DeviceType }))
        } else {
          const currentConfig = device.config || {}
          const updatedConfig = { ...currentConfig, [field]: value }
          dispatch(updateDeviceAsync({ id: device.id, config: updatedConfig }))
        }
      })
    }

    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Bulk Properties ({multiSelectedDevices.length} devices)</h3>
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
            className={`tab ${activeTab === 'risk' ? 'active' : ''}`}
            onClick={() => setActiveTab('risk')}
          >
            Risk
          </button>
          <button 
            className={`tab ${activeTab === 'connections' ? 'active' : ''}`}
            onClick={() => setActiveTab('connections')}
          >
            Connections
          </button>
        </div>
        
        <div className="panel-content">
          <div className="multi-edit-info">
            <p><strong>Bulk editing {multiSelectedDevices.length} devices:</strong></p>
            <div className="selected-devices-grid">
              {multiSelectedDevices.map(device => (
                <div key={device.id} className="selected-device-item">
                  <DeviceIcon deviceType={device.type} size={16} className="device-icon" />
                  <span className="device-name">{device.name}</span>
                  <span className="device-type-label">{DEVICE_LABELS[device.type] || device.type}</span>
                </div>
              ))}
            </div>
          </div>

          {activeTab === 'general' && (
            <div className="property-section">
              <h4>General Properties (applies to all selected)</h4>
              
              <label className="form-field">
                <span>Device Type</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('type', e.target.value)
                      e.target.value = '' // Reset dropdown
                    }
                  }}
                >
                  <option value="">-- Change Type for All --</option>
                  {Object.entries(DEVICE_CATEGORIES).map(([category, deviceTypes]) => (
                    <optgroup key={category} label={category}>
                      {deviceTypes.map((deviceType) => (
                        <option key={deviceType} value={deviceType}>
                          {DEVICE_LABELS[deviceType]}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span>System Categorization</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('categorizationType', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">-- Set for All --</option>
                  {CATEGORIZATION_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="property-section">
              <h4>Security Configuration (applies to all selected)</h4>
              
              <label className="form-field">
                <span>Patch Level</span>
                <input 
                  type="text"
                  placeholder="e.g., Current, 30 days behind - applies to all"
                  onBlur={(e) => {
                    if (e.target.value) {
                      handleBulkChange('patchLevel', e.target.value)
                      e.target.value = ''
                    }
                  }}
                />
              </label>

              <label className="form-field">
                <span>Encryption Status</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('encryptionStatus', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">-- Set for All --</option>
                  <option value="Not Configured">Not Configured</option>
                  <option value="Configured">Configured</option>
                  <option value="Full Disk Encryption">Full Disk Encryption</option>
                  <option value="Transit Only">Transit Only</option>
                  <option value="At Rest Only">At Rest Only</option>
                </select>
              </label>

              <label className="form-field">
                <span>Access Control Policy</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('accessControlPolicy', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">-- Set for All --</option>
                  <option value="Standard">Standard</option>
                  <option value="Privileged">Privileged</option>
                  <option value="High Security">High Security</option>
                  <option value="Guest">Guest</option>
                </select>
              </label>

              <div className="bulk-checkbox-actions">
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => handleBulkChange('monitoringEnabled', 'true')}
                >
                  Enable Monitoring for All
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => handleBulkChange('monitoringEnabled', 'false')}
                >
                  Disable Monitoring for All
                </button>
              </div>

              <label className="form-field">
                <span>Backup Policy</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('backupPolicy', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">-- Set for All --</option>
                  <option value="Standard">Standard (Daily)</option>
                  <option value="Critical">Critical (Real-time)</option>
                  <option value="Weekly">Weekly</option>
                  <option value="None">None</option>
                </select>
              </label>
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="property-section">
              <h4>Risk Assessment (applies to all selected)</h4>
              
              <label className="form-field">
                <span>Overall Risk Level</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('riskLevel', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">-- Set for All --</option>
                  {RISK_LEVELS.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </label>

              <div className="impact-levels">
                <h5>Impact Levels (FIPS 199)</h5>
                <label className="form-field">
                  <span>Confidentiality Impact</span>
                  <select 
                    defaultValue=""
                    onChange={(e) => {
                      if (e.target.value) {
                        handleBulkChange('confidentialityImpact', e.target.value)
                        e.target.value = ''
                      }
                    }}
                  >
                    <option value="">-- Set for All --</option>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Integrity Impact</span>
                  <select 
                    defaultValue=""
                    onChange={(e) => {
                      if (e.target.value) {
                        handleBulkChange('integrityImpact', e.target.value)
                        e.target.value = ''
                      }
                    }}
                  >
                    <option value="">-- Set for All --</option>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Availability Impact</span>
                  <select 
                    defaultValue=""
                    onChange={(e) => {
                      if (e.target.value) {
                        handleBulkChange('availabilityImpact', e.target.value)
                        e.target.value = ''
                      }
                    }}
                  >
                    <option value="">-- Set for All --</option>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="form-field">
                <span>Compliance Status</span>
                <select 
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) {
                      handleBulkChange('complianceStatus', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">-- Set for All --</option>
                  {COMPLIANCE_STATUS.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span>Known Vulnerabilities (number)</span>
                <input 
                  type="number"
                  min="0"
                  placeholder="Set vulnerability count for all"
                  onBlur={(e) => {
                    if (e.target.value) {
                      handleBulkChange('vulnerabilities', e.target.value)
                      e.target.value = ''
                    }
                  }}
                />
              </label>
            </div>
          )}

          {activeTab === 'connections' && (
            <div className="property-section">
              <h4>Auto-Connect Selected Devices</h4>
              
              <label className="form-field">
                <span>Connection Type</span>
                <select 
                  value={connectionType}
                  onChange={(e) => setConnectionType(e.target.value)}
                >
                  <option value="ethernet">Ethernet</option>
                  <option value="fiber">Fiber Optic</option>
                  <option value="wireless">Wireless</option>
                  <option value="vpn">VPN</option>
                  <option value="serial">Serial</option>
                  <option value="usb">USB</option>
                  <option value="coax">Coaxial</option>
                  <option value="bluetooth">Bluetooth</option>
                  <option value="infrared">Infrared</option>
                  <option value="custom">Custom</option>
                </select>
              </label>
              
              <div className="draw-connections-section">
                <button 
                  type="button" 
                  className="btn btn-success btn-draw-connections" 
                  onClick={drawConnections}
                  title="Draw/refresh all connection lines on the canvas"
                >
                  🎨 Draw Connections
                </button>
              </div>

              <div className="connection-buttons">
                <button 
                  type="button" 
                  className="btn btn-primary btn-small" 
                  onClick={connectNearestNeighbor}
                  title="Connect each device to its nearest neighbor"
                >
                  📍 Nearest Neighbor
                </button>
                
                <button 
                  type="button" 
                  className="btn btn-primary btn-small" 
                  onClick={connectStar}
                  title="Connect all devices to the first selected device (hub)"
                >
                  ⭐ Star Pattern
                </button>
                
                <button 
                  type="button" 
                  className="btn btn-primary btn-small" 
                  onClick={connectChain}
                  title="Connect devices in sequence (chain)"
                >
                  🔗 Chain Pattern
                </button>
                
                <button 
                  type="button" 
                  className="btn btn-primary btn-small" 
                  onClick={connectMesh}
                  title="Connect every device to every other device"
                >
                  🕸️ Full Mesh
                </button>
              </div>
            </div>
          )}

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
              Delete All Selected ({multiSelectedDevices.length})
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!selected || (!device && !connection && !boundary)) {
    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Properties</h3>
        </header>
        <p className="panel-placeholder">Select a device, connection, or boundary, or Ctrl+click multiple devices.</p>
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
                  {Object.entries(DEVICE_CATEGORIES).map(([category, deviceTypes]) => (
                    <optgroup key={category} label={category}>
                      {deviceTypes.map((deviceType) => (
                        <option key={deviceType} value={deviceType}>
                          {DEVICE_LABELS[deviceType]}
                        </option>
                      ))}
                    </optgroup>
                  ))}
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

  if (connection) {
    const handleConnectionChange = (event: ChangeEvent<HTMLInputElement>) => {
      const { name, value } = event.target
      dispatch(updateConnection({ id: connection.id, [name]: value }))
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
            value={connection.sourceDeviceId}
            onChange={handleConnectionChange}
          />
        </label>
        <label className="form-field">
          <span>Target</span>
          <input
            name="targetDeviceId"
            value={connection.targetDeviceId}
            onChange={handleConnectionChange}
          />
        </label>
        <label className="form-field">
          <span>Link type</span>
          <input name="linkType" value={connection.linkType} onChange={handleConnectionChange} />
        </label>
      </div>
    </div>
  )
  }

  // Boundary properties
  if (boundary) {
    // Parse security config from boundary.config 
    const boundaryConfig = {
      description: boundary.config?.description || '',
      owner: boundary.config?.owner || '',
      criticality: boundary.config?.criticality || 'Medium',
      accessLevel: boundary.config?.accessLevel || 'Internal',
      complianceFramework: boundary.config?.complianceFramework || '',
      dataClassification: boundary.config?.dataClassification || 'Internal',
      riskLevel: boundary.config?.riskLevel || 'Moderate',
      confidentialityImpact: boundary.config?.confidentialityImpact || 'Moderate',
      integrityImpact: boundary.config?.integrityImpact || 'Moderate',
      availabilityImpact: boundary.config?.availabilityImpact || 'Moderate',
      complianceStatus: boundary.config?.complianceStatus || 'Not Assessed',
      authorizer: boundary.config?.authorizer || '',
      lastAssessment: boundary.config?.lastAssessment || '',
      nextAssessment: boundary.config?.nextAssessment || '',
      securityControls: boundary.config?.securityControls ? JSON.parse(boundary.config.securityControls) : [],
    }

    const getBoundaryBoundingBox = () => {
      if (!boundary.points || boundary.points.length === 0) {
        return {
          x: boundary.x ?? 0,
          y: boundary.y ?? 0,
          width: boundary.width ?? 200,
          height: boundary.height ?? 200
        }
      }

      const xs = boundary.points.map(point => point.x)
      const ys = boundary.points.map(point => point.y)
      const minX = Math.min(...xs)
      const maxX = Math.max(...xs)
      const minY = Math.min(...ys)
      const maxY = Math.max(...ys)

      return {
        x: minX,
        y: minY,
        width: Math.max(maxX - minX, 20),
        height: Math.max(maxY - minY, 20)
      }
    }

    const currentPositionFromBoundary = () => {
      if (boundary.position && boundary.position.width !== undefined && boundary.position.height !== undefined) {
        return {
          x: boundary.position.x,
          y: boundary.position.y,
          width: boundary.position.width,
          height: boundary.position.height
        }
      }

      if (
        boundary.x !== undefined &&
        boundary.y !== undefined &&
        boundary.width !== undefined &&
        boundary.height !== undefined
      ) {
        return {
          x: boundary.x,
          y: boundary.y,
          width: boundary.width,
          height: boundary.height
        }
      }

      return getBoundaryBoundingBox()
    }

    const handleBoundaryChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const { name, value } = event.target
      
      if (name === 'label') {
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { label: value } }))
      } else if (name === 'color') {
        dispatch(updateBoundaryAsync({ 
          id: boundary.id, 
          updates: { style: { ...boundary.style, color: value } }
        }))
      } else if (name === 'strokeWidth') {
        dispatch(updateBoundaryAsync({ 
          id: boundary.id, 
          updates: { style: { ...boundary.style, strokeWidth: parseInt(value) || 1 } }
        }))
      } else if (name === 'fillOpacity') {
        dispatch(updateBoundaryAsync({ 
          id: boundary.id, 
          updates: { style: { ...boundary.style, fillOpacity: parseFloat(value) || 0 } }
        }))
      } else if (name === 'dashArray') {
        dispatch(updateBoundaryAsync({ 
          id: boundary.id, 
          updates: { style: { ...boundary.style, dashArray: value || 'none' } }
        }))
      } else if (name === 'x' || name === 'y' || name === 'width' || name === 'height') {
        const parsed = parseFloat(value)
        const numValue = Number.isFinite(parsed) ? parsed : 0

        const basePosition = currentPositionFromBoundary()

        const rawPosition = { ...basePosition, [name]: numValue }
        const sanitizedPosition = {
          x: rawPosition.x ?? 0,
          y: rawPosition.y ?? 0,
          width: rawPosition.width ?? boundary.position?.width ?? boundary.width ?? 200,
          height: rawPosition.height ?? boundary.position?.height ?? boundary.height ?? 200
        }

        const updatedPoints = [
          { x: sanitizedPosition.x, y: sanitizedPosition.y },
          { x: sanitizedPosition.x + sanitizedPosition.width, y: sanitizedPosition.y },
          { x: sanitizedPosition.x + sanitizedPosition.width, y: sanitizedPosition.y + sanitizedPosition.height },
          { x: sanitizedPosition.x, y: sanitizedPosition.y + sanitizedPosition.height }
        ]

        dispatch(updateBoundary({
          id: boundary.id,
          updates: {
            position: sanitizedPosition,
            x: sanitizedPosition.x,
            y: sanitizedPosition.y,
            width: sanitizedPosition.width,
            height: sanitizedPosition.height,
            points: updatedPoints
          }
        }))

        dispatch(updateBoundaryAsync({
          id: boundary.id,
          updates: {
            position: sanitizedPosition,
            x: sanitizedPosition.x,
            y: sanitizedPosition.y,
            width: sanitizedPosition.width,
            height: sanitizedPosition.height,
            points: updatedPoints
          }
        }))
      } else {
        // Handle config properties
        const newConfig = { ...boundary.config, [name]: value }
        dispatch(updateBoundaryAsync({ 
          id: boundary.id, 
          updates: { config: newConfig }
        }))
      }
    }

    const handleDeleteBoundary = () => {
      if (window.confirm('Are you sure you want to delete this boundary?')) {
        dispatch(deleteBoundaryAsync(boundary.id))
        dispatch(selectEntity(null))
      }
    }

    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Boundary Properties</h3>
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
            className={`tab ${activeTab === 'risk' ? 'active' : ''}`}
            onClick={() => setActiveTab('risk')}
          >
            Risk
          </button>
        </div>
        <div className="panel-content">
          {activeTab === 'general' && (
            <>
              <div className="boundary-info">
                <p><strong>Type:</strong> {BOUNDARY_LABELS[boundary.type]}</p>
                <p><strong>Created:</strong> {new Date(boundary.created).toLocaleDateString()}</p>
                <p><strong>Points:</strong> {boundary.points.length}</p>
              </div>

              <label className="form-field">
                <span>Label</span>
                <input
                  name="label"
                  value={boundary.label}
                  onChange={handleBoundaryChange}
                  placeholder="Boundary label"
                />
              </label>

              <label className="form-field">
                <span>Description</span>
                <textarea
                  name="description"
                  value={boundaryConfig.description}
                  onChange={handleBoundaryChange}
                  placeholder="Boundary description and purpose"
                  rows={3}
                />
              </label>

              <label className="form-field">
                <span>Owner</span>
                <input
                  name="owner"
                  value={boundaryConfig.owner}
                  onChange={handleBoundaryChange}
                  placeholder="Boundary owner or responsible party"
                />
              </label>

              <label className="form-field">
                <span>Criticality</span>
                <select name="criticality" value={boundaryConfig.criticality} onChange={handleBoundaryChange}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </label>

              <label className="form-field">
                <span>Access Level</span>
                <select name="accessLevel" value={boundaryConfig.accessLevel} onChange={handleBoundaryChange}>
                  <option value="Public">Public</option>
                  <option value="Internal">Internal</option>
                  <option value="Confidential">Confidential</option>
                  <option value="Restricted">Restricted</option>
                  <option value="Top Secret">Top Secret</option>
                </select>
              </label>

              <h4>Position & Size</h4>
              <div className="position-grid">
                <label className="form-field">
                  <span>X Position</span>
                  <input
                    type="number"
                    name="x"
                    value={boundary.position?.x || boundary.x || 0}
                    onChange={handleBoundaryChange}
                  />
                </label>
                <label className="form-field">
                  <span>Y Position</span>
                  <input
                    type="number"
                    name="y"
                    value={boundary.position?.y || boundary.y || 0}
                    onChange={handleBoundaryChange}
                  />
                </label>
                <label className="form-field">
                  <span>Width</span>
                  <input
                    type="number"
                    name="width"
                    value={boundary.position?.width || boundary.width || 200}
                    onChange={handleBoundaryChange}
                    min="50"
                  />
                </label>
                <label className="form-field">
                  <span>Height</span>
                  <input
                    type="number"
                    name="height"
                    value={boundary.position?.height || boundary.height || 200}
                    onChange={handleBoundaryChange}
                    min="50"
                  />
                </label>
              </div>

              <h4>Appearance</h4>
              <label className="form-field">
                <span>Border Color</span>
                <input
                  type="color"
                  name="color"
                  value={boundary.style.color}
                  onChange={handleBoundaryChange}
                />
              </label>

              <label className="form-field">
                <span>Border Width</span>
                <input
                  type="number"
                  name="strokeWidth"
                  value={boundary.style.strokeWidth}
                  onChange={handleBoundaryChange}
                  min="1"
                  max="10"
                />
              </label>

              <label className="form-field">
                <span>Fill Opacity</span>
                <input
                  type="range"
                  name="fillOpacity"
                  value={boundary.style.fillOpacity || 0}
                  onChange={handleBoundaryChange}
                  min="0"
                  max="1"
                  step="0.1"
                />
                <span>{Math.round((boundary.style.fillOpacity || 0) * 100)}%</span>
              </label>

              <label className="form-field">
                <span>Border Style</span>
                <select name="dashArray" value={boundary.style.dashArray || 'none'} onChange={handleBoundaryChange}>
                  <option value="none">Solid</option>
                  <option value="5,5">Dashed</option>
                  <option value="3,3">Dotted</option>
                  <option value="10,5">Long Dash</option>
                  <option value="8,4,2,4">Dash-Dot</option>
                </select>
              </label>

              <button 
                className="danger-button" 
                onClick={handleDeleteBoundary}
                style={{ marginTop: '1rem' }}
              >
                Delete Boundary
              </button>
            </>
          )}

          {activeTab === 'security' && (
            <div className="property-section">
              <h4>Security Properties</h4>
              
              <label className="form-field">
                <span>Data Classification</span>
                <select name="dataClassification" value={boundaryConfig.dataClassification} onChange={handleBoundaryChange}>
                  <option value="Public">Public</option>
                  <option value="Internal">Internal</option>
                  <option value="Confidential">Confidential</option>
                  <option value="Restricted">Restricted</option>
                  <option value="Top Secret">Top Secret</option>
                </select>
              </label>

              <label className="form-field">
                <span>Compliance Framework</span>
                <input
                  name="complianceFramework"
                  value={boundaryConfig.complianceFramework}
                  onChange={handleBoundaryChange}
                  placeholder="e.g., NIST SP 800-53, ISO 27001, FedRAMP"
                />
              </label>

              <label className="form-field">
                <span>Authorizer</span>
                <input
                  name="authorizer"
                  value={boundaryConfig.authorizer}
                  onChange={handleBoundaryChange}
                  placeholder="Authorizing Official"
                />
              </label>

              <label className="form-field">
                <span>Last Assessment</span>
                <input
                  type="date"
                  name="lastAssessment"
                  value={boundaryConfig.lastAssessment}
                  onChange={handleBoundaryChange}
                />
              </label>

              <label className="form-field">
                <span>Next Assessment</span>
                <input
                  type="date"
                  name="nextAssessment"
                  value={boundaryConfig.nextAssessment}
                  onChange={handleBoundaryChange}
                />
              </label>
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="property-section">
              <h4>Risk Assessment</h4>
              
              <label className="form-field">
                <span>Overall Risk Level</span>
                <select name="riskLevel" value={boundaryConfig.riskLevel} onChange={handleBoundaryChange}>
                  {RISK_LEVELS.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </label>

              <div className="impact-levels">
                <h5>Impact Levels (FIPS 199)</h5>
                <label className="form-field">
                  <span>Confidentiality Impact</span>
                  <select name="confidentialityImpact" value={boundaryConfig.confidentialityImpact} onChange={handleBoundaryChange}>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Integrity Impact</span>
                  <select name="integrityImpact" value={boundaryConfig.integrityImpact} onChange={handleBoundaryChange}>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>Availability Impact</span>
                  <select name="availabilityImpact" value={boundaryConfig.availabilityImpact} onChange={handleBoundaryChange}>
                    {IMPACT_LEVELS.map(level => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="form-field">
                <span>Compliance Status</span>
                <select name="complianceStatus" value={boundaryConfig.complianceStatus} onChange={handleBoundaryChange}>
                  {COMPLIANCE_STATUS.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </label>
            </div>
          )}
        </div>
      </div>
    )
  }
}

export default PropertyEditor

