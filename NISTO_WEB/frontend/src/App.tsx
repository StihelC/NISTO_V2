import { Outlet } from 'react-router-dom'
import { Provider, useDispatch, useSelector } from 'react-redux'

import { redo, undo } from './store/historyActions'
import { store } from './store'
import type { RootState } from './store/types'

const Shell = () => {
  const dispatch = useDispatch()
  const { canUndo, canRedo } = useSelector((state: RootState) => state.ui.history)

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">NISTO Web</h1>
        <div className="app-actions">
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
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}

const App = () => (
  <Provider store={store}>
    <Shell />
  </Provider>
)

export default App
