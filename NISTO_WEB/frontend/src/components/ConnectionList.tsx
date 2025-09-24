import type { FormEvent } from 'react'
import { useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { createConnection, deleteConnection } from '../store/connectionsSlice'
import type { RootState } from '../store/types'
import { selectEntity } from '../store/uiSlice'

const ConnectionList = () => {
  const dispatch = useDispatch()
  const connections = useSelector((state: RootState) => state.connections.items)
  const devices = useSelector((state: RootState) => state.devices.items)
  const selected = useSelector((state: RootState) => state.ui.selected)

  const [sourceDeviceId, setSourceDeviceId] = useState('')
  const [targetDeviceId, setTargetDeviceId] = useState('')
  const [linkType, setLinkType] = useState('ethernet')
  const [error, setError] = useState<string | null>(null)

  const deviceNameById = useMemo(() => {
    return devices.reduce<Record<string, string>>((acc, device) => {
      acc[device.id] = device.name
      return acc
    }, {})
  }, [devices])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!sourceDeviceId || !targetDeviceId) {
      setError('Source and target are required')
      return
    }

    if (sourceDeviceId === targetDeviceId) {
      setError('Source and target must be different devices')
      return
    }

    dispatch(createConnection({ sourceDeviceId, targetDeviceId, linkType }))
    setSourceDeviceId('')
    setTargetDeviceId('')
    setLinkType('ethernet')
    setError(null)
  }

  const handleDelete = (id: string) => {
    dispatch(deleteConnection(id))
  }

  const handleSelect = (id: string) => {
    dispatch(selectEntity({ kind: 'connection', id }))
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <div>
          <h3>Connections</h3>
          <p className="panel-subtitle">Link devices together.</p>
        </div>
      </header>
      <div className="panel-content">
        <form className="form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Source</span>
            <select
              value={sourceDeviceId}
              onChange={(event) => {
                setSourceDeviceId(event.target.value)
                if (error) {
                  setError(null)
                }
              }}
            >
              <option value="">Select device</option>
              {devices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Target</span>
            <select
              value={targetDeviceId}
              onChange={(event) => {
                setTargetDeviceId(event.target.value)
                if (error) {
                  setError(null)
                }
              }}
            >
              <option value="">Select device</option>
              {devices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Link type</span>
            <input
              type="text"
              value={linkType}
              onChange={(event) => setLinkType(event.target.value)}
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button type="submit" className="primary-button" disabled={devices.length < 2}>
            Add Connection
          </button>
        </form>
        <ul className="list">
          {connections.length === 0 && <li className="panel-placeholder">No connections yet.</li>}
          {connections.map((connection) => (
            <li
              key={connection.id}
              className={`list-item ${
                selected?.kind === 'connection' && selected.id === connection.id ? 'is-selected' : ''
              }`}
            >
              <button type="button" className="list-row" onClick={() => handleSelect(connection.id)}>
                <span className="list-title">
                  {deviceNameById[connection.sourceDeviceId] ?? connection.sourceDeviceId} →{' '}
                  {deviceNameById[connection.targetDeviceId] ?? connection.targetDeviceId}
                </span>
                <span className="list-caption">{connection.linkType}</span>
              </button>
              <button type="button" className="danger-button" onClick={() => handleDelete(connection.id)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default ConnectionList

