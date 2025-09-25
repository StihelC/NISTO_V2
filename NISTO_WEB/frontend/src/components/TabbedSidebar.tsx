import { useState } from 'react'
import DeviceList from './DeviceList'
import ConnectionList from './ConnectionList'

type TabType = 'devices' | 'connections'

const TabbedSidebar = () => {
  const [activeTab, setActiveTab] = useState<TabType>('devices')

  return (
    <div className="panel tabbed-sidebar">
      <div className="sidebar-tabs">
        <button
          className={`sidebar-tab ${activeTab === 'devices' ? 'active' : ''}`}
          onClick={() => setActiveTab('devices')}
        >
          Devices
        </button>
        <button
          className={`sidebar-tab ${activeTab === 'connections' ? 'active' : ''}`}
          onClick={() => setActiveTab('connections')}
        >
          Connections
        </button>
      </div>
      <div className="tab-content">
        {activeTab === 'devices' && <DeviceList />}
        {activeTab === 'connections' && <ConnectionList />}
      </div>
    </div>
  )
}

export default TabbedSidebar
