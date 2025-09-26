import type { ChangeEvent } from 'react'

interface DeviceSecurityTabProps {
  patchLevel: string
  encryptionStatus: string
  accessControlPolicy: string
  monitoringEnabled: boolean
  backupPolicy: string
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
}

const DeviceSecurityTab = ({
  patchLevel,
  encryptionStatus,
  accessControlPolicy,
  monitoringEnabled,
  backupPolicy,
  onChange,
}: DeviceSecurityTabProps) => (
  <div className="property-section">
    <h4>Security Configuration</h4>
    <label className="form-field">
      <span>Patch Level</span>
      <input name="patchLevel" value={patchLevel} onChange={onChange} placeholder="e.g., Current, 30 days behind" />
    </label>
    <label className="form-field">
      <span>Encryption Status</span>
      <select name="encryptionStatus" value={encryptionStatus} onChange={onChange}>
        <option value="Not Configured">Not Configured</option>
        <option value="Configured">Configured</option>
        <option value="Full Disk Encryption">Full Disk Encryption</option>
        <option value="Transit Only">Transit Only</option>
        <option value="At Rest Only">At Rest Only</option>
      </select>
    </label>
    <label className="form-field">
      <span>Access Control Policy</span>
      <select name="accessControlPolicy" value={accessControlPolicy} onChange={onChange}>
        <option value="Standard">Standard</option>
        <option value="Privileged">Privileged</option>
        <option value="High Security">High Security</option>
        <option value="Guest">Guest</option>
      </select>
    </label>
    <label className="form-field checkbox-field">
      <input type="checkbox" name="monitoringEnabled" checked={monitoringEnabled} onChange={onChange} />
      <span>Security Monitoring Enabled</span>
    </label>
    <label className="form-field">
      <span>Backup Policy</span>
      <select name="backupPolicy" value={backupPolicy} onChange={onChange}>
        <option value="Standard">Standard (Daily)</option>
        <option value="Critical">Critical (Real-time)</option>
        <option value="Weekly">Weekly</option>
        <option value="None">None</option>
      </select>
    </label>
  </div>
)

export default DeviceSecurityTab

