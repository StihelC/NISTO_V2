import type { ChangeEvent } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { updateDeviceAsync, deleteDeviceAsync, updateDeviceDisplayPreferences } from '../store/devicesSlice'
import type { DeviceDisplayPreferences } from '../store/types'
import { updateConnection } from '../store/connectionsSlice'
import { updateBoundary, updateBoundaryAsync, deleteBoundaryAsync, BOUNDARY_LABELS } from '../store/boundariesSlice'
import { selectEntity, clearContextMenu } from '../store/uiSlice'
import type { AppDispatch, DeviceType, RootState } from '../store'
import type { Device } from '../store/types'
import { useAutoConnect } from '../hooks/useAutoConnect'
import {
  DevicePropertiesPanel,
  BulkDevicePropertiesPanel,
  type DeviceSecurityConfig,
  type SecurityControl,
  type DeviceTab,
  type BulkDeviceTab,
} from './PropertyEditorComponents/'

const PropertyEditor = () => {
  const dispatch = useDispatch<AppDispatch>()
  const selected = useSelector((state: RootState) => state.ui.selected)
  const multiSelected = useSelector((state: RootState) => state.ui.multiSelected)
  const devices = useSelector((state: RootState) => state.devices.items)
  const connections = useSelector((state: RootState) => state.connections.items)
  const boundaries = useSelector((state: RootState) => state.boundaries.items)

  const [activeTab, setActiveTab] = useState<DeviceTab>('general')
  const [bulkTab, setBulkTab] = useState<BulkDeviceTab>('general')
  const [connectionType, setConnectionType] = useState('ethernet')

  const device = selected?.kind === 'device' ? devices.find((item) => item.id === selected.id) : null
  const connection = selected?.kind === 'connection' ? connections.find((item) => item.id === selected.id) : null
  const boundary = selected?.kind === 'boundary' ? boundaries.find((item) => item.id === selected.id) : null

  const multiSelectedDevices = useMemo<Device[]>(
    () => (multiSelected?.kind === 'device' ? devices.filter((item) => multiSelected.ids.includes(item.id)) : []),
    [devices, multiSelected],
  )

  const { connectNearestNeighbor, connectStar, connectChain, connectMesh, connectSelection } = useAutoConnect({
    multiSelectedDevices,
    connectionType,
  })

  const handleDrawConnections = async () => {
    const created = await connectSelection('chain')
    if (created === 0) {
      window.alert('All adjacent selected device pairs are already connected.')
    } else {
      window.alert(`Created ${created} chain connection${created === 1 ? '' : 's'} between selected devices.`)
    }
    dispatch(clearContextMenu())
  }

  useEffect(() => {
    if (selected && !device && !connection && !boundary) {
      dispatch(selectEntity(null))
    }
  }, [selected, device, connection, boundary, dispatch])

  useEffect(() => {
    if (device || multiSelectedDevices.length > 0) {
      setActiveTab('general')
    }
  }, [device?.id, multiSelectedDevices.length])

  if (multiSelected?.kind === 'device' && multiSelectedDevices.length > 0) {
    const handleBulkChange = (field: string, value: unknown) => {
      multiSelectedDevices.forEach((item) => {
        if (field === 'type') {
          dispatch(updateDeviceAsync({ id: item.id, type: value as DeviceType }))
        } else {
          const updatedConfig = { ...(item.config || {}), [field]: String(value) }
          dispatch(updateDeviceAsync({ id: item.id, config: updatedConfig }))
        }
      })
    }

    const handleDeleteAll = () => {
      if (window.confirm(`Delete ${multiSelectedDevices.length} selected devices?`)) {
        multiSelectedDevices.forEach((item) => {
          dispatch(deleteDeviceAsync(item.id))
        })
      }
    }

    return (
      <BulkDevicePropertiesPanel
        devices={multiSelectedDevices}
        activeTab={bulkTab}
        connectionType={connectionType}
        onTabChange={setBulkTab}
        onBulkChange={handleBulkChange}
        onDeleteAll={handleDeleteAll}
        onConnectionTypeChange={setConnectionType}
        onConnectNearest={connectNearestNeighbor}
        onConnectStar={connectStar}
        onConnectChain={connectChain}
        onConnectMesh={connectMesh}
        onDrawConnections={handleDrawConnections}
      />
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
    const securityConfig: DeviceSecurityConfig = {
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
      incidentResponsePlan: device.config.incidentResponsePlan || 'Corporate Standard',
    }

    const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const { name, value, type } = event.target
      const checked = (event.target as HTMLInputElement).checked

      if (name === 'name' || name === 'type') {
        const updateData = {
          id: device.id,
          [name]: name === 'type' ? (value as DeviceType) : value,
        }
        dispatch(updateDeviceAsync(updateData))
      } else {
        const newConfig = {
          ...device.config,
          [name]: type === 'checkbox' ? checked.toString() : value,
        }
        dispatch(updateDeviceAsync({ id: device.id, config: newConfig }))
      }
    }

    const handleControlUpdate = (controlId: string, updates: Partial<SecurityControl>) => {
      const controls = [...securityConfig.securityControls]
      const index = controls.findIndex((entry) => entry.id === controlId)

      if (index >= 0) {
        controls[index] = { ...controls[index], ...updates }
      } else {
        controls.push({
          id: controlId,
          category: updates.category || '',
          name: updates.name || '',
          status: updates.status || 'not_implemented',
          notes: updates.notes || '',
        })
      }

      const newConfig = {
        ...device.config,
        securityControls: JSON.stringify(controls),
      }
      dispatch(updateDeviceAsync({ id: device.id, config: newConfig }))
    }

    const handleDisplayPreferencesChange = (preferences: Partial<DeviceDisplayPreferences>) => {
      const currentPreferences = device.displayPreferences || {
        // General Properties
        showDeviceName: true,
        showDeviceType: true,
        showCategorizationType: false,
        
        // Security Properties
        showPatchLevel: false,
        showEncryptionStatus: false,
        showAccessControlPolicy: false,
        showMonitoringEnabled: false,
        showBackupPolicy: false,
        
        // Risk Properties
        showRiskLevel: true,
        showConfidentialityImpact: false,
        showIntegrityImpact: false,
        showAvailabilityImpact: false,
        showComplianceStatus: false,
        showVulnerabilities: false,
        showAuthorizer: false,
        showLastAssessment: false,
        showNextAssessment: false,
      }
      
      const newPreferences = { ...currentPreferences, ...preferences }
      dispatch(updateDeviceDisplayPreferences({ id: device.id, displayPreferences: newPreferences }))
    }

    const deviceDisplayPreferences = device.displayPreferences || {
      // General Properties
      showDeviceName: true,
      showDeviceType: true,
      showCategorizationType: false,
      
      // Security Properties
      showPatchLevel: false,
      showEncryptionStatus: false,
      showAccessControlPolicy: false,
      showMonitoringEnabled: false,
      showBackupPolicy: false,
      
      // Risk Properties
      showRiskLevel: true,
      showConfidentialityImpact: false,
      showIntegrityImpact: false,
      showAvailabilityImpact: false,
      showComplianceStatus: false,
      showVulnerabilities: false,
      showAuthorizer: false,
      showLastAssessment: false,
      showNextAssessment: false,
    }

    return (
      <DevicePropertiesPanel
        name={device.name}
        type={device.type}
        securityConfig={securityConfig}
        displayPreferences={deviceDisplayPreferences}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onChange={handleChange}
        onControlUpdate={handleControlUpdate}
        onDisplayPreferencesChange={handleDisplayPreferencesChange}
      />
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
            <input name="sourceDeviceId" value={connection.sourceDeviceId} onChange={handleConnectionChange} />
          </label>
          <label className="form-field">
            <span>Target</span>
            <input name="targetDeviceId" value={connection.targetDeviceId} onChange={handleConnectionChange} />
          </label>
          <label className="form-field">
            <span>Link type</span>
            <input name="linkType" value={connection.linkType} onChange={handleConnectionChange} />
          </label>
        </div>
      </div>
    )
  }

  if (boundary) {
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
    }

    const handleBoundaryChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      const { name, value } = event.target

      if (name === 'label') {
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { label: value } }))
      } else if (name === 'color') {
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { style: { ...boundary.style, color: value } } }))
      } else if (name === 'strokeWidth') {
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { style: { ...boundary.style, strokeWidth: parseInt(value, 10) || 1 } } }))
      } else if (name === 'fillOpacity') {
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { style: { ...boundary.style, fillOpacity: parseFloat(value) || 0 } } }))
      } else if (name === 'dashArray') {
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { style: { ...boundary.style, dashArray: value || 'none' } } }))
      } else if (name === 'x' || name === 'y' || name === 'width' || name === 'height') {
        const parsedValue = Number.parseFloat(value)
        const numericValue = Number.isFinite(parsedValue) ? parsedValue : 0

        const basePosition = {
          x: boundary.position?.x ?? boundary.x ?? 0,
          y: boundary.position?.y ?? boundary.y ?? 0,
          width: boundary.position?.width ?? boundary.width ?? 200,
          height: boundary.position?.height ?? boundary.height ?? 200,
        }

        const nextPosition = {
          ...basePosition,
          [name]: numericValue,
        }

        const sanitizedPosition = {
          x: nextPosition.x,
          y: nextPosition.y,
          width: Math.max(nextPosition.width, 20),
          height: Math.max(nextPosition.height, 20),
        }

        const updatedPoints = [
          { x: sanitizedPosition.x, y: sanitizedPosition.y },
          { x: sanitizedPosition.x + sanitizedPosition.width, y: sanitizedPosition.y },
          { x: sanitizedPosition.x + sanitizedPosition.width, y: sanitizedPosition.y + sanitizedPosition.height },
          { x: sanitizedPosition.x, y: sanitizedPosition.y + sanitizedPosition.height },
        ]

        dispatch(updateBoundary({
          id: boundary.id,
          updates: {
            position: sanitizedPosition,
            x: sanitizedPosition.x,
            y: sanitizedPosition.y,
            width: sanitizedPosition.width,
            height: sanitizedPosition.height,
            points: updatedPoints,
          },
        }))

        dispatch(updateBoundaryAsync({
          id: boundary.id,
          updates: {
            position: sanitizedPosition,
            x: sanitizedPosition.x,
            y: sanitizedPosition.y,
            width: sanitizedPosition.width,
            height: sanitizedPosition.height,
            points: updatedPoints,
          },
        }))
      } else {
        const newConfig = { ...boundary.config, [name]: value }
        dispatch(updateBoundaryAsync({ id: boundary.id, updates: { config: newConfig } }))
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
        <div className="panel-content">
          <p className="panel-subtitle">{BOUNDARY_LABELS[boundary.type] ?? boundary.type}</p>
          <label className="form-field">
            <span>Label</span>
            <input name="label" value={boundary.label} onChange={handleBoundaryChange} placeholder="Boundary label" />
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
            <input name="owner" value={boundaryConfig.owner} onChange={handleBoundaryChange} placeholder="Boundary owner or responsible party" />
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

          <div className="form-actions">
            <button type="button" className="btn btn-danger" onClick={handleDeleteBoundary}>
              Delete Boundary
            </button>
          </div>
        </div>
      </div>
    )
  }

  return null
}

export default PropertyEditor
