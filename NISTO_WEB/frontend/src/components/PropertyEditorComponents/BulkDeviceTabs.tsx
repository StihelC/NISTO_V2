import type { BulkDeviceTab } from './types'

interface BulkDeviceTabsProps {
  activeTab: BulkDeviceTab
  onTabChange: (tab: BulkDeviceTab) => void
}

const BulkDeviceTabs = ({ activeTab, onTabChange }: BulkDeviceTabsProps) => (
  <div className="property-tabs">
    <button className={`tab ${activeTab === 'general' ? 'active' : ''}`} onClick={() => onTabChange('general')}>
      General
    </button>
    <button className={`tab ${activeTab === 'security' ? 'active' : ''}`} onClick={() => onTabChange('security')}>
      Security
    </button>
    <button className={`tab ${activeTab === 'risk' ? 'active' : ''}`} onClick={() => onTabChange('risk')}>
      Risk
    </button>
    <button className={`tab ${activeTab === 'connections' ? 'active' : ''}`} onClick={() => onTabChange('connections')}>
      Connections
    </button>
  </div>
)

export default BulkDeviceTabs

