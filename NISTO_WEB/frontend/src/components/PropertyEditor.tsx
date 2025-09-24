import type { ChangeEvent } from 'react'
import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { updateDevice } from '../store/devicesSlice'
import { updateConnection } from '../store/connectionsSlice'
import type { DeviceType, RootState } from '../store/types'
import { selectEntity } from '../store/uiSlice'

const PropertyEditor = () => {
  const dispatch = useDispatch()
  const selected = useSelector((state: RootState) => state.ui.selected)
  const devices = useSelector((state: RootState) => state.devices.items)
  const connections = useSelector((state: RootState) => state.connections.items)

  const device = selected?.kind === 'device' ? devices.find((item) => item.id === selected.id) : null
  const connection =
    selected?.kind === 'connection' ? connections.find((item) => item.id === selected.id) : null

  useEffect(() => {
    if (selected && !device && !connection) {
      dispatch(selectEntity(null))
    }
  }, [selected, device, connection, dispatch])

  if (!selected || (!device && !connection)) {
    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Properties</h3>
        </header>
        <p className="panel-placeholder">Select a device or connection.</p>
      </div>
    )
  }

  if (device) {
    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
      const { name, value } = event.target
      dispatch(
        updateDevice({
          id: device.id,
          [name]: name === 'type' ? (value as DeviceType) : value,
        }),
      )
    }

    return (
      <div className="panel">
        <header className="panel-header">
          <h3>Device Properties</h3>
        </header>
        <div className="panel-content">
          <label className="form-field">
            <span>Name</span>
            <input name="name" value={device.name} onChange={handleChange} />
          </label>
          <label className="form-field">
            <span>Type</span>
            <input name="type" value={device.type} onChange={handleChange} />
          </label>
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

