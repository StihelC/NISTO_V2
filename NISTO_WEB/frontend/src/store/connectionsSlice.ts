import { createSlice, createAsyncThunk, nanoid } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import { connectionsApi } from '../api/connections'
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

// Async thunks
export const fetchConnections = createAsyncThunk(
  'connections/fetchConnections',
  async (_, { rejectWithValue }) => {
    try {
      const connections = await connectionsApi.getConnections()
      return connections.map(conn => ({
        id: conn.id.toString(),
        sourceDeviceId: conn.source_device_id.toString(),
        targetDeviceId: conn.target_device_id.toString(),
        linkType: conn.link_type,
        properties: conn.properties,
      }))
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch connections')
    }
  }
)

export const createConnectionAsync = createAsyncThunk(
  'connections/createConnectionAsync',
  async (payload: CreateConnectionPayload, { rejectWithValue }) => {
    try {
      const connection = await connectionsApi.createConnection({
        source_device_id: parseInt(payload.sourceDeviceId),
        target_device_id: parseInt(payload.targetDeviceId),
        link_type: payload.linkType,
        properties: {},
      })
      return {
        id: connection.id.toString(),
        sourceDeviceId: connection.source_device_id.toString(),
        targetDeviceId: connection.target_device_id.toString(),
        linkType: connection.link_type,
        properties: connection.properties,
      }
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create connection')
    }
  }
)

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
    setConnections(state, action: PayloadAction<Connection[]>) {
      state.items = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchConnections.fulfilled, (state, action) => {
        state.items = action.payload
      })
      .addCase(createConnectionAsync.fulfilled, (state, action) => {
        state.items.push(action.payload)
      })
  },
})

export const {
  createConnection,
  updateConnection,
  deleteConnection,
  deleteConnectionsByDevice,
  resetConnections,
  setConnections,
} = connectionsSlice.actions

export default connectionsSlice.reducer

