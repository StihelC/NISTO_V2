import { createSlice, nanoid } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

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
  },
})

export const { createDevice, updateDevice, deleteDevice, resetDevices } =
  devicesSlice.actions

export default devicesSlice.reducer

