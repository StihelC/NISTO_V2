import type { ChangeEvent } from 'react'

import { DEVICE_CATEGORIES, DEVICE_LABELS } from '../../constants/deviceTypes'
import type { DeviceType } from '../../store'

interface DeviceGeneralTabProps {
  name: string
  type: DeviceType
  categorizationType: string
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
}

const DeviceGeneralTab = ({ name, type, categorizationType, onChange }: DeviceGeneralTabProps) => (
  <div className="property-section">
    <label className="form-field">
      <span>Name</span>
      <input name="name" value={name} onChange={onChange} />
    </label>
    <label className="form-field">
      <span>Type</span>
      <select name="type" value={type} onChange={onChange}>
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
      <select name="categorizationType" value={categorizationType} onChange={onChange}>
        <option value="Information System">Information System</option>
        <option value="Platform IT System">Platform IT System</option>
        <option value="Software as a Service">Software as a Service</option>
      </select>
    </label>
  </div>
)

export default DeviceGeneralTab

