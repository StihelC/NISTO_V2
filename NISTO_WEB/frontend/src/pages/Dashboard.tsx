import { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'

import TabbedSidebar from '../components/TabbedSidebar'
import PropertyEditor from '../components/PropertyEditor'
import TopologyCanvas from '../components/TopologyCanvas'
import { useAutoSave } from '../hooks/useAutoSave'
import { fetchDevices, fetchConnections, type AppDispatch } from '../store'

const Dashboard = () => {
  const dispatch = useDispatch<AppDispatch>()
  
  // Load initial data
  useEffect(() => {
    dispatch(fetchDevices())
    dispatch(fetchConnections())
  }, [dispatch])
  
  // Enable auto-save with 30 second intervals
  useAutoSave(30000)

  return (
    <div className="dashboard">
      <PanelGroup direction="horizontal" storage={{ getItem: () => null, setItem: () => {} }}>
        <Panel defaultSize={20} minSize={15} maxSize={35}>
          <TabbedSidebar />
        </Panel>
        <PanelResizeHandle className="resize-handle" />
        <Panel defaultSize={60} minSize={30} className="topology-panel">
          <TopologyCanvas />
        </Panel>
        <PanelResizeHandle className="resize-handle" />
        <Panel defaultSize={20} minSize={15} maxSize={35}>
          <PropertyEditor />
        </Panel>
      </PanelGroup>
    </div>
  )
}

export default Dashboard


