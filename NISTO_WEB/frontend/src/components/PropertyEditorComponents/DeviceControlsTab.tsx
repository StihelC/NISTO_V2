import type { SecurityControl } from './types'
import { NIST_CATEGORIES } from './constants'

interface DeviceControlsTabProps {
  controls: SecurityControl[]
  onUpdate: (controlId: string, updates: Partial<SecurityControl>) => void
}

const DeviceControlsTab = ({ controls, onUpdate }: DeviceControlsTabProps) => (
  <div className="property-section">
    <h4>NIST Security Controls</h4>
    <div className="controls-grid">
      {Object.entries(NIST_CATEGORIES).map(([code, name]) => {
        const control = controls.find((c) => c.category === code)
        return (
          <div key={code} className="control-item">
            <div className="control-header">
              <strong>{code}</strong> - {name}
            </div>
            <select
              value={control?.status || 'not_implemented'}
              onChange={(event) =>
                onUpdate(`${code}-1`, {
                  category: code,
                  name,
                  status: event.target.value as SecurityControl['status'],
                })
              }
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
)

export default DeviceControlsTab

