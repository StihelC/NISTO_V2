import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Provider, useDispatch, useSelector } from 'react-redux'

import { SaveLoadModal } from './components/SaveLoadModal'
import { redo, undo } from './store/historyActions'
import { store } from './store'
import type { RootState } from './store/types'

const Shell = () => {
  const dispatch = useDispatch()
  const { canUndo, canRedo } = useSelector((state: RootState) => state.ui.history)
  const { autoSaving, lastAutoSave } = useSelector((state: RootState) => state.projects)
  
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const [loadModalOpen, setLoadModalOpen] = useState(false)

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">NISTO Web</h1>
        <div className="app-actions">
          <button
            type="button"
            className="action-button"
            onClick={() => setSaveModalOpen(true)}
          >
            Save
          </button>
          <button
            type="button"
            className="action-button"
            onClick={() => setLoadModalOpen(true)}
          >
            Load
          </button>
          <button
            type="button"
            className="action-button"
            disabled={!canUndo}
            onClick={() => dispatch(undo())}
          >
            Undo
          </button>
          <button
            type="button"
            className="action-button"
            disabled={!canRedo}
            onClick={() => dispatch(redo())}
          >
            Redo
          </button>
          {autoSaving && (
            <span className="auto-save-indicator">Auto-saving...</span>
          )}
          {lastAutoSave && !autoSaving && (
            <span className="auto-save-indicator">
              Last saved: {new Date(lastAutoSave).toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      
      <SaveLoadModal
        isOpen={saveModalOpen}
        onClose={() => setSaveModalOpen(false)}
        mode="save"
      />
      
      <SaveLoadModal
        isOpen={loadModalOpen}
        onClose={() => setLoadModalOpen(false)}
        mode="load"
      />
    </div>
  )
}

const App = () => (
  <Provider store={store}>
    <Shell />
  </Provider>
)

export default App
