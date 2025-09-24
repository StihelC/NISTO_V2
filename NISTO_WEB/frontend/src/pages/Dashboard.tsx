import DeviceList from '../components/DeviceList'
import ConnectionList from '../components/ConnectionList'
import PropertyEditor from '../components/PropertyEditor'
import TopologyCanvas from '../components/TopologyCanvas'
import { useAutoSave } from '../hooks/useAutoSave'

const Dashboard = () => {
  // Enable auto-save with 30 second intervals
  useAutoSave(30000)

  return (
    <div className="dashboard">
      <section className="dashboard-column dashboard-column-left">
        <DeviceList />
        <ConnectionList />
      </section>
      <section className="dashboard-column dashboard-column-center">
        <TopologyCanvas />
      </section>
      <aside className="dashboard-column dashboard-column-right">
        <PropertyEditor />
      </aside>
    </div>
  )
}

export default Dashboard


