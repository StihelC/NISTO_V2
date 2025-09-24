import { createSlice, nanoid } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { Connection, ConnectionsState } from './types'

interface CreateConnectionPayload {
  sourceDeviceId: string
  targetDeviceId: string
  linkType: string
}

interface UpdateConnectionPayload {
  id: string
  sourceDeviceId?: string
  targetDeviceId?: string
  linkType?: string
  properties?: Record<string, string>
}

const initialState: ConnectionsState = {
  items: [],
}

const connectionsSlice = createSlice({
  name: 'connections',
  initialState,
  reducers: {
    createConnection: {
      reducer(state, action: PayloadAction<Connection>) {
        state.items.push(action.payload)
      },
      prepare({ sourceDeviceId, targetDeviceId, linkType }: CreateConnectionPayload) {
        return {
          payload: {
            id: nanoid(),
            sourceDeviceId,
            targetDeviceId,
            linkType,
            properties: {},
          },
        }
      },
    },
    updateConnection(state, action: PayloadAction<UpdateConnectionPayload>) {
      const { id, ...changes } = action.payload
      const connection = state.items.find((item) => item.id === id)
      if (connection) {
        Object.assign(connection, changes)
      }
    },
    deleteConnection(state, action: PayloadAction<string>) {
      state.items = state.items.filter((connection) => connection.id !== action.payload)
    },
    deleteConnectionsByDevice(state, action: PayloadAction<string>) {
      state.items = state.items.filter(
        (connection) =>
          connection.sourceDeviceId !== action.payload &&
          connection.targetDeviceId !== action.payload,
      )
    },
    resetConnections() {
      return initialState
    },
  },
})

export const {
  createConnection,
  updateConnection,
  deleteConnection,
  deleteConnectionsByDevice,
  resetConnections,
} = connectionsSlice.actions

export default connectionsSlice.reducer

