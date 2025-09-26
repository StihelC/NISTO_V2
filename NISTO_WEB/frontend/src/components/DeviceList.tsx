import type { FormEvent } from 'react'
import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { createDeviceAsync, deleteDeviceAsync, createBulkDevicesAsync } from '../store/devicesSlice'
import { selectEntity, toggleMultiSelect, clearMultiSelection } from '../store/uiSlice'
import type { DeviceType, RootState } from '../store'
import { DEVICE_LABELS } from '../constants/deviceTypes'
import DeviceIcon from './DeviceIcon'
import DeviceIconPreview from './DeviceIconPreview'
const ARRANGEMENT_TYPES = [
  { value: 'grid', label: 'Grid' },
  { value: 'circle', label: 'Circle' },
  { value: 'line', label: 'Line' },
  { value: 'random', label: 'Random' }
] as const

type ArrangementType = typeof ARRANGEMENT_TYPES[number]['value']

const DeviceList = () => {
  const dispatch = useDispatch()
  const devices = useSelector((state: RootState) => state.devices.items)
  const selected = useSelector((state: RootState) => state.ui.selected)
  const multiSelected = useSelector((state: RootState) => state.ui.multiSelected)

  const [name, setName] = useState('')
  const [type, setType] = useState<DeviceType>('switch')
  const [error, setError] = useState<string | null>(null)
  
  // Bulk creation state
  const [showBulkForm, setShowBulkForm] = useState(false)
  const [bulkQuantity, setBulkQuantity] = useState(5)
  const [bulkBaseName, setBulkBaseName] = useState('')
  const [bulkType, setBulkType] = useState<DeviceType>('switch')
  const [arrangement, setArrangement] = useState<ArrangementType>('grid')
  const [bulkError, setBulkError] = useState<string | null>(null)
  const [showIconPreview, setShowIconPreview] = useState(false)
  const [showDeviceSelector, setShowDeviceSelector] = useState(false)
  const [selectorMode, setSelectorMode] = useState<'single' | 'bulk'>('single')

  const handleDeviceTypeSelect = (deviceType: DeviceType) => {
    if (selectorMode === 'single') {
      setType(deviceType)
    } else {
      setBulkType(deviceType)
    }
  }

  const openDeviceSelector = (mode: 'single' | 'bulk') => {
    setSelectorMode(mode)
    setShowDeviceSelector(true)
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim()) {
      setError('Name is required')
      return
    }

    // Only create device in backend - it will update local state when successful
    dispatch(createDeviceAsync({ name, type }) as any)
    setName('')
    setType('switch')
    setError(null)
  }

  const handleDelete = (id: string) => {
    // Only delete from backend - it will update local state when successful
    dispatch(deleteDeviceAsync(id) as any)
  }

  const handleSelect = (id: string, ctrlKey: boolean = false) => {
    if (ctrlKey) {
      dispatch(toggleMultiSelect({ kind: 'device', id }))
    } else {
      dispatch(selectEntity({ kind: 'device', id }))
    }
  }

  const handleBulkSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!bulkBaseName.trim()) {
      setBulkError('Base name is required')
      return
    }
    if (bulkQuantity < 1 || bulkQuantity > 50) {
      setBulkError('Quantity must be between 1 and 50')
      return
    }

    // Dispatch bulk creation
    dispatch(createBulkDevicesAsync({
      baseName: bulkBaseName,
      type: bulkType,
      quantity: bulkQuantity,
      arrangement: arrangement
    }) as any)
    
    // Reset form
    setBulkBaseName('')
    setBulkQuantity(5)
    setBulkType('switch')
    setArrangement('grid')
    setBulkError(null)
    setShowBulkForm(false)
  }

  return (
    <div className="device-list">
      <header className="panel-header">
        <div>
          <h3>Devices</h3>
          <p className="panel-subtitle">Manage network devices.</p>
        </div>
      </header>
      <div className="panel-content">
        <div className="panel-actions">
          <div className="form-tabs">
            <button 
              className={`form-tab ${!showBulkForm ? 'active' : ''}`}
              onClick={() => setShowBulkForm(false)}
            >
              Single Device
            </button>
            <button 
              className={`form-tab ${showBulkForm ? 'active' : ''}`}
              onClick={() => setShowBulkForm(true)}
            >
              Multiple Devices
            </button>
          </div>
          <button
            type="button"
            className="secondary-button icon-preview-button"
            onClick={() => setShowIconPreview(true)}
            title="Preview device icons"
          >
            🎨 Icons
          </button>
        </div>

        {!showBulkForm ? (
          <form className="form" onSubmit={handleSubmit}>
            <label className="form-field">
              <span>Name</span>
              <input
                type="text"
                value={name}
                onChange={(event) => {
                  setName(event.target.value)
                  if (error) {
                    setError(null)
                  }
                }}
                placeholder="Device name"
              />
            </label>
            <label className="form-field">
              <span>Type</span>
              <div className="device-type-selector">
                <div className="selected-device-type" onClick={() => openDeviceSelector('single')}>
                  <DeviceIcon deviceType={type} size={20} />
                  <span>{DEVICE_LABELS[type]}</span>
                  <span className="selector-arrow">▼</span>
                </div>
              </div>
            </label>
            {error && <p className="form-error">{error}</p>}
            <button type="submit" className="primary-button">
              Add Device
            </button>
          </form>
        ) : (
          <form className="form" onSubmit={handleBulkSubmit}>
            <label className="form-field">
              <span>Base Name</span>
              <input
                type="text"
                value={bulkBaseName}
                onChange={(event) => {
                  setBulkBaseName(event.target.value)
                  if (bulkError) {
                    setBulkError(null)
                  }
                }}
                placeholder="e.g., Switch (will create Switch-1, Switch-2, ...)"
              />
            </label>
            <label className="form-field">
              <span>Type</span>
              <div className="device-type-selector">
                <div className="selected-device-type" onClick={() => openDeviceSelector('bulk')}>
                  <DeviceIcon deviceType={bulkType} size={20} />
                  <span>{DEVICE_LABELS[bulkType]}</span>
                  <span className="selector-arrow">▼</span>
                </div>
              </div>
            </label>
            <label className="form-field">
              <span>Quantity</span>
              <input
                type="number"
                min="1"
                max="50"
                value={bulkQuantity}
                onChange={(event) => setBulkQuantity(parseInt(event.target.value) || 1)}
              />
            </label>
            <label className="form-field">
              <span>Arrangement</span>
              <select value={arrangement} onChange={(event) => setArrangement(event.target.value as ArrangementType)}>
                {ARRANGEMENT_TYPES.map((arrangementType) => (
                  <option key={arrangementType.value} value={arrangementType.value}>
                    {arrangementType.label}
                  </option>
                ))}
              </select>
            </label>
            {bulkError && <p className="form-error">{bulkError}</p>}
            <button type="submit" className="primary-button">
              Add {bulkQuantity} Devices
            </button>
          </form>
        )}
        
        {/* Multi-selection info */}
        {multiSelected && multiSelected.ids.length > 0 && (
          <div className="multi-select-info">
            <span>{multiSelected.ids.length} device{multiSelected.ids.length > 1 ? 's' : ''} selected</span>
            <button 
              type="button" 
              className="btn btn-small" 
              onClick={() => dispatch(clearMultiSelection())}
            >
              Clear Selection
            </button>
          </div>
        )}
        
        <div className="multi-select-hint">
          Hold Ctrl (or Cmd on Mac) and click to select multiple devices
          <br />
          Drag any selected device to move the entire group together
        </div>
        
        <ul className="list">
          {devices.length === 0 && <li className="panel-placeholder">No devices yet.</li>}
          {devices.map((device) => {
            const isSingleSelected = selected?.kind === 'device' && selected.id === device.id
            const isMultiSelected = multiSelected?.kind === 'device' && multiSelected.ids.includes(device.id)
            const isSelected = isSingleSelected || isMultiSelected
            
            return (
              <li
                key={device.id}
                className={`list-item ${isSelected ? 'is-selected' : ''} ${isMultiSelected ? 'is-multi-selected' : ''}`}
              >
                <button 
                  type="button" 
                  className="list-row" 
                  onClick={(e) => handleSelect(device.id, e.ctrlKey || e.metaKey)}
                >
                  <span className="list-title">
                    <DeviceIcon deviceType={device.type} size={16} className="device-icon" />
                    {device.name}
                  </span>
                  <span className="list-caption">{DEVICE_LABELS[device.type] || device.type}</span>
                  {isMultiSelected && <span className="multi-select-indicator">✓</span>}
                </button>
                <button type="button" className="danger-button" onClick={() => handleDelete(device.id)}>
                  Delete
                </button>
              </li>
            )
          })}
        </ul>
      </div>
      
      {showIconPreview && (
        <DeviceIconPreview onClose={() => setShowIconPreview(false)} />
      )}
      
      {showDeviceSelector && (
        <DeviceIconPreview 
          mode="selector"
          selectedDeviceType={selectorMode === 'single' ? type : bulkType}
          onSelectDeviceType={handleDeviceTypeSelect}
          onClose={() => setShowDeviceSelector(false)} 
        />
      )}
    </div>
  )
}

export default DeviceList

