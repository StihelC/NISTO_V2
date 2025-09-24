import { createSlice, createAsyncThunk, nanoid } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import { devicesApi } from '../api/devices'
import type { Device, DevicesState, DeviceType } from './types'

interface CreateDevicePayload {
  name: string
  type: DeviceType
}

interface UpdateDevicePayload {
  id: string
  name?: string
  type?: DeviceType
  position?: { x: number; y: number }
}

const initialState: DevicesState = {
  items: [],
}

// Async thunks
export const fetchDevices = createAsyncThunk(
  'devices/fetchDevices',
  async (_, { rejectWithValue }) => {
    try {
      const devices = await devicesApi.getDevices()
      return devices.map(device => ({
        id: device.id.toString(),
        name: device.name,
        type: device.type as DeviceType,
        config: device.config,
        position: device.x && device.y ? { x: device.x, y: device.y } : undefined,
      }))
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch devices')
    }
  }
)

const devicesSlice = createSlice({
  name: 'devices',
  initialState,
  reducers: {
    createDevice: {
      reducer(state, action: PayloadAction<Device>) {
        state.items.push(action.payload)
      },
      prepare({ name, type }: CreateDevicePayload) {
        return {
          payload: {
            id: nanoid(),
            name,
            type,
            config: {},
          },
        }
      },
    },
    updateDevice(state, action: PayloadAction<UpdateDevicePayload>) {
      const { id, ...changes } = action.payload
      const device = state.items.find((item) => item.id === id)
      if (device) {
        Object.assign(device, changes)
      }
    },
    deleteDevice(state, action: PayloadAction<string>) {
      state.items = state.items.filter((device) => device.id !== action.payload)
    },
    resetDevices() {
      return initialState
    },
    setDevices(state, action: PayloadAction<Device[]>) {
      state.items = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDevices.fulfilled, (state, action) => {
        state.items = action.payload
      })
  },
})

export const { createDevice, updateDevice, deleteDevice, resetDevices, setDevices } =
  devicesSlice.actions

export default devicesSlice.reducer

