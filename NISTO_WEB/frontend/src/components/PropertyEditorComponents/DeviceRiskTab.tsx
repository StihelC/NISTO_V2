import type { ChangeEvent } from 'react'

import { IMPACT_LEVELS, RISK_LEVELS, COMPLIANCE_STATUS } from './constants'

interface DeviceRiskTabProps {
  riskLevel: string
  confidentialityImpact: string
  integrityImpact: string
  availabilityImpact: string
  complianceStatus: string
  vulnerabilities: string
  authorizer: string
  lastAssessment: string
  nextAssessment: string
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
}

const DeviceRiskTab = ({
  riskLevel,
  confidentialityImpact,
  integrityImpact,
  availabilityImpact,
  complianceStatus,
  vulnerabilities,
  authorizer,
  lastAssessment,
  nextAssessment,
  onChange,
}: DeviceRiskTabProps) => (
  <div className="property-section">
    <h4>Risk Assessment & Impact</h4>
    <label className="form-field">
      <span>Overall Risk Level</span>
      <select name="riskLevel" value={riskLevel} onChange={onChange}>
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
        <select name="confidentialityImpact" value={confidentialityImpact} onChange={onChange}>
          {IMPACT_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
      </label>
      <label className="form-field">
        <span>Integrity Impact</span>
        <select name="integrityImpact" value={integrityImpact} onChange={onChange}>
          {IMPACT_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
      </label>
      <label className="form-field">
        <span>Availability Impact</span>
        <select name="availabilityImpact" value={availabilityImpact} onChange={onChange}>
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
      <select name="complianceStatus" value={complianceStatus} onChange={onChange}>
        {COMPLIANCE_STATUS.map((status) => (
          <option key={status} value={status}>
            {status}
          </option>
        ))}
      </select>
    </label>

    <label className="form-field">
      <span>Known Vulnerabilities</span>
      <input name="vulnerabilities" type="number" min="0" value={vulnerabilities} onChange={onChange} />
    </label>

    <label className="form-field">
      <span>Authorizing Official</span>
      <input name="authorizer" value={authorizer} onChange={onChange} placeholder="Name of AO" />
    </label>

    <label className="form-field">
      <span>Last Assessment Date</span>
      <input name="lastAssessment" type="date" value={lastAssessment} onChange={onChange} />
    </label>

    <label className="form-field">
      <span>Next Assessment Due</span>
      <input name="nextAssessment" type="date" value={nextAssessment} onChange={onChange} />
    </label>
  </div>
)

export default DeviceRiskTab

