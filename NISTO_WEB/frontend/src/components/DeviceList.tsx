import type { FormEvent } from 'react'
import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { createDevice, createDeviceAsync, deleteDevice, deleteDeviceAsync } from '../store/devicesSlice'
import { selectEntity } from '../store/uiSlice'
import type { DeviceType, RootState } from '../store'

const DEVICE_TYPES: DeviceType[] = ['switch', 'router', 'firewall', 'server', 'workstation', 'generic']

const DeviceList = () => {
  const dispatch = useDispatch()
  const devices = useSelector((state: RootState) => state.devices.items)
  const selected = useSelector((state: RootState) => state.ui.selected)

  const [name, setName] = useState('')
  const [type, setType] = useState<DeviceType>('switch')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim()) {
      setError('Name is required')
      return
    }

    // Create device in local state immediately for UI responsiveness
    dispatch(createDevice({ name, type }))
    // Create device in backend asynchronously
    dispatch(createDeviceAsync({ name, type }))
    setName('')
    setType('switch')
    setError(null)
  }

  const handleDelete = (id: string) => {
    // Delete from local state immediately
    dispatch(deleteDevice(id))
    // Delete from backend asynchronously
    dispatch(deleteDeviceAsync(id))
  }

  const handleSelect = (id: string) => {
    dispatch(selectEntity({ kind: 'device', id }))
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <div>
          <h3>Devices</h3>
          <p className="panel-subtitle">Manage network devices.</p>
        </div>
      </header>
      <div className="panel-content">
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
            <select value={type} onChange={(event) => setType(event.target.value as DeviceType)}>
              {DEVICE_TYPES.map((deviceType) => (
                <option key={deviceType} value={deviceType}>
                  {deviceType}
                </option>
              ))}
            </select>
          </label>
          {error && <p className="form-error">{error}</p>}
          <button type="submit" className="primary-button">
            Add Device
          </button>
        </form>
        <ul className="list">
          {devices.length === 0 && <li className="panel-placeholder">No devices yet.</li>}
          {devices.map((device) => (
            <li
              key={device.id}
              className={`list-item ${
                selected?.kind === 'device' && selected.id === device.id ? 'is-selected' : ''
              }`}
            >
              <button type="button" className="list-row" onClick={() => handleSelect(device.id)}>
                <span className="list-title">{device.name}</span>
                <span className="list-caption">{device.type}</span>
              </button>
              <button type="button" className="danger-button" onClick={() => handleDelete(device.id)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default DeviceList

