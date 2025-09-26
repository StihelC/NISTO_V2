import DeviceIcon from '../DeviceIcon'
import { DEVICE_CATEGORIES, DEVICE_LABELS } from '../../constants/deviceTypes'
import { CATEGORIZATION_TYPES, RISK_LEVELS, IMPACT_LEVELS, COMPLIANCE_STATUS } from './constants'
import BulkDeviceTabs from './BulkDeviceTabs'
import type { BulkDeviceTab } from './types'
import type { DeviceType } from '../../store'
import type { Device } from '../../store/types'

interface BulkDevicePropertiesPanelProps {
  devices: Device[]
  activeTab: BulkDeviceTab
  connectionType: string
  onTabChange: (tab: BulkDeviceTab) => void
  onBulkChange: (field: string, value: unknown) => void
  onDeleteAll: () => void
  onConnectionTypeChange: (value: string) => void
  onConnectNearest: () => void
  onConnectStar: () => void
  onConnectChain: () => void
  onConnectMesh: () => void
  onDrawConnections: () => void
}

const BulkDevicePropertiesPanel = ({
  devices,
  activeTab,
  connectionType,
  onTabChange,
  onBulkChange,
  onDeleteAll,
  onConnectionTypeChange,
  onConnectNearest,
  onConnectStar,
  onConnectChain,
  onConnectMesh,
  onDrawConnections,
}: BulkDevicePropertiesPanelProps) => (
  <div className="panel">
    <header className="panel-header">
      <h3>Bulk Properties ({devices.length} devices)</h3>
    </header>
    <BulkDeviceTabs activeTab={activeTab} onTabChange={onTabChange} />
    <div className="panel-content">
      <div className="multi-edit-info">
        <p>
          <strong>Bulk editing {devices.length} devices:</strong>
        </p>
        <div className="selected-devices-grid">
          {devices.map((device) => (
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
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('type', event.target.value as DeviceType)
                  event.target.value = ''
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
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('categorizationType', event.target.value)
                  event.target.value = ''
                }
              }}
            >
              <option value="">-- Set for All --</option>
              {CATEGORIZATION_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
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
              onBlur={(event) => {
                if (event.target.value) {
                  onBulkChange('patchLevel', event.target.value)
                  event.target.value = ''
                }
              }}
            />
          </label>

          <label className="form-field">
            <span>Encryption Status</span>
            <select
              defaultValue=""
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('encryptionStatus', event.target.value)
                  event.target.value = ''
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
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('accessControlPolicy', event.target.value)
                  event.target.value = ''
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
            <button type="button" className="btn btn-secondary" onClick={() => onBulkChange('monitoringEnabled', 'true')}>
              Enable Monitoring for All
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => onBulkChange('monitoringEnabled', 'false')}>
              Disable Monitoring for All
            </button>
          </div>

          <label className="form-field">
            <span>Backup Policy</span>
            <select
              defaultValue=""
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('backupPolicy', event.target.value)
                  event.target.value = ''
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
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('riskLevel', event.target.value)
                  event.target.value = ''
                }
              }}
            >
              <option value="">-- Set for All --</option>
              {RISK_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>

          <div className="impact-levels">
            <h5>Impact Levels (FIPS 199)</h5>
            <label className="form-field">
              <span>Confidentiality Impact</span>
              <select
                defaultValue=""
                onChange={(event) => {
                  if (event.target.value) {
                    onBulkChange('confidentialityImpact', event.target.value)
                    event.target.value = ''
                  }
                }}
              >
                <option value="">-- Set for All --</option>
                {IMPACT_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>Integrity Impact</span>
              <select
                defaultValue=""
                onChange={(event) => {
                  if (event.target.value) {
                    onBulkChange('integrityImpact', event.target.value)
                    event.target.value = ''
                  }
                }}
              >
                <option value="">-- Set for All --</option>
                {IMPACT_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>Availability Impact</span>
              <select
                defaultValue=""
                onChange={(event) => {
                  if (event.target.value) {
                    onBulkChange('availabilityImpact', event.target.value)
                    event.target.value = ''
                  }
                }}
              >
                <option value="">-- Set for All --</option>
                {IMPACT_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="form-field">
            <span>Compliance Status</span>
            <select
              defaultValue=""
              onChange={(event) => {
                if (event.target.value) {
                  onBulkChange('complianceStatus', event.target.value)
                  event.target.value = ''
                }
              }}
            >
              <option value="">-- Set for All --</option>
              {COMPLIANCE_STATUS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>Known Vulnerabilities (number)</span>
            <input
              type="number"
              min="0"
              placeholder="Set vulnerability count for all"
              onBlur={(event) => {
                if (event.target.value) {
                  onBulkChange('vulnerabilities', event.target.value)
                  event.target.value = ''
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
            <select value={connectionType} onChange={(event) => onConnectionTypeChange(event.target.value)}>
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
            <button type="button" className="btn btn-success btn-draw-connections" onClick={onDrawConnections} title="Draw/refresh all connection lines on the canvas">
              🎨 Draw Connections
            </button>
          </div>

          <div className="connection-buttons">
            <button type="button" className="btn btn-primary btn-small" onClick={onConnectNearest} title="Connect each device to its nearest neighbor">
              📍 Nearest Neighbor
            </button>
            <button type="button" className="btn btn-primary btn-small" onClick={onConnectStar} title="Connect all devices to the first selected device (hub)">
              ⭐ Star Pattern
            </button>
            <button type="button" className="btn btn-primary btn-small" onClick={onConnectChain} title="Connect devices in sequence (chain)">
              🔗 Chain Pattern
            </button>
            <button type="button" className="btn btn-primary btn-small" onClick={onConnectMesh} title="Connect every device to every other device">
              🕸️ Full Mesh
            </button>
          </div>
        </div>
      )}

      <div className="form-actions">
        <button type="button" className="btn btn-danger" onClick={onDeleteAll}>
          Delete All Selected ({devices.length})
        </button>
      </div>
    </div>
  </div>
)

export default BulkDevicePropertiesPanel

