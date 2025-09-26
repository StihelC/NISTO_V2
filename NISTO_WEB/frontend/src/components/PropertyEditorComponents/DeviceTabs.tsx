import type { DeviceTab } from './types'

interface DeviceTabsProps {
  activeTab: DeviceTab
  onTabChange: (tab: DeviceTab) => void
}

const DeviceTabs = ({ activeTab, onTabChange }: DeviceTabsProps) => (
  <div className="property-tabs">
    <button className={`tab ${activeTab === 'general' ? 'active' : ''}`} onClick={() => onTabChange('general')}>
      General
    </button>
    <button className={`tab ${activeTab === 'security' ? 'active' : ''}`} onClick={() => onTabChange('security')}>
      Security
    </button>
    <button className={`tab ${activeTab === 'controls' ? 'active' : ''}`} onClick={() => onTabChange('controls')}>
      Controls
    </button>
    <button className={`tab ${activeTab === 'risk' ? 'active' : ''}`} onClick={() => onTabChange('risk')}>
      Risk
    </button>
  </div>
)

export default DeviceTabs

