import { combineReducers, configureStore } from '@reduxjs/toolkit'

import connectionsReducer, { deleteConnectionsByDevice } from './connectionsSlice'
import devicesReducer from './devicesSlice'
import { restore } from './historyActions'
import projectsReducer from './projectsSlice'
import uiReducer from './uiSlice'
import { createUndoRedoMiddleware } from './undoRedoMiddleware'

const baseReducer = combineReducers({
  devices: devicesReducer,
  connections: connectionsReducer,
  ui: uiReducer,
  projects: projectsReducer,
})

const enhanceWithCrossSlice = (state: ReturnType<typeof baseReducer> | undefined, action: any) => {
  let intermediateState = baseReducer(state, action)

  if (action.type === 'devices/deleteDevice') {
    intermediateState = baseReducer(intermediateState, deleteConnectionsByDevice(action.payload))
  }

  return intermediateState
}

const undoRedoMiddleware = createUndoRedoMiddleware()

export const store = configureStore({
  reducer: (state, action) => {
    if (restore.match(action)) {
      return action.payload
    }

    return enhanceWithCrossSlice(state, action)
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ serializableCheck: false }).concat(undoRedoMiddleware),
})

export type AppDispatch = typeof store.dispatch
export type RootStateFromStore = ReturnType<typeof store.getState>

// Re-export everything for easier imports
export type { RootState, DeviceType } from './types'
export { fetchDevices, createDeviceAsync, updateDeviceAsync, deleteDeviceAsync } from './devicesSlice'
export { fetchConnections } from './connectionsSlice'
export * from './projectsSlice'
export * from './historyActions'

