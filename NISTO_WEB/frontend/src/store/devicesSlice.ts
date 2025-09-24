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
  config?: Record<string, string>
}

interface CreateBulkDevicesPayload {
  baseName: string
  type: DeviceType
  quantity: number
  arrangement: 'grid' | 'circle' | 'line' | 'random'
}

const initialState: DevicesState = {
  items: [],
}

// Arrangement calculation functions
const calculateArrangementPositions = (
  quantity: number, 
  arrangement: 'grid' | 'circle' | 'line' | 'random', 
  canvasWidth = 800, 
  canvasHeight = 600
): Array<{ x: number; y: number }> => {
  const positions: Array<{ x: number; y: number }> = []
  const centerX = canvasWidth / 2
  const centerY = canvasHeight / 2
  const spacing = 120

  switch (arrangement) {
    case 'grid': {
      const cols = Math.ceil(Math.sqrt(quantity))
      const rows = Math.ceil(quantity / cols)
      const startX = centerX - ((cols - 1) * spacing) / 2
      const startY = centerY - ((rows - 1) * spacing) / 2
      
      for (let i = 0; i < quantity; i++) {
        const row = Math.floor(i / cols)
        const col = i % cols
        positions.push({
          x: startX + col * spacing,
          y: startY + row * spacing
        })
      }
      break
    }
    
    case 'circle': {
      const radius = Math.min(canvasWidth, canvasHeight) * 0.3
      const angleStep = (2 * Math.PI) / quantity
      
      for (let i = 0; i < quantity; i++) {
        const angle = i * angleStep
        positions.push({
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        })
      }
      break
    }
    
    case 'line': {
      const totalWidth = (quantity - 1) * spacing
      const startX = centerX - totalWidth / 2
      
      for (let i = 0; i < quantity; i++) {
        positions.push({
          x: startX + i * spacing,
          y: centerY
        })
      }
      break
    }
    
    case 'random': {
      const margin = 100
      for (let i = 0; i < quantity; i++) {
        positions.push({
          x: margin + Math.random() * (canvasWidth - 2 * margin),
          y: margin + Math.random() * (canvasHeight - 2 * margin)
        })
      }
      break
    }
  }
  
  return positions
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

export const createDeviceAsync = createAsyncThunk(
  'devices/createDeviceAsync',
  async (payload: CreateDevicePayload, { rejectWithValue }) => {
    try {
      const device = await devicesApi.createDevice({
        name: payload.name,
        type: payload.type,
        config: {},
      })
      return {
        id: device.id.toString(),
        name: device.name,
        type: device.type as DeviceType,
        config: device.config,
        position: device.x && device.y ? { x: device.x, y: device.y } : undefined,
      }
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create device')
    }
  }
)

export const createBulkDevicesAsync = createAsyncThunk(
  'devices/createBulkDevicesAsync',
  async (payload: CreateBulkDevicesPayload, { rejectWithValue }) => {
    try {
      // Calculate positions for all devices
      const positions = calculateArrangementPositions(
        payload.quantity,
        payload.arrangement
      )
      
      // Create devices in parallel
      const devicePromises = Array.from({ length: payload.quantity }, async (_, index) => {
        const deviceName = `${payload.baseName}-${index + 1}`
        const position = positions[index]
        
        const device = await devicesApi.createDevice({
          name: deviceName,
          type: payload.type,
          x: position.x,
          y: position.y,
          config: {},
        })
        
        return {
          id: device.id.toString(),
          name: device.name,
          type: device.type as DeviceType,
          config: device.config,
          position: { x: device.x!, y: device.y! },
        }
      })
      
      const devices = await Promise.all(devicePromises)
      return devices
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create devices')
    }
  }
)

export const updateDeviceAsync = createAsyncThunk(
  'devices/updateDeviceAsync',
  async (payload: UpdateDevicePayload, { rejectWithValue }) => {
    try {
      const { id, position, ...otherUpdates } = payload
      const updates = {
        ...otherUpdates,
        ...(position && { x: position.x, y: position.y }),
      }
      const device = await devicesApi.updateDevice(parseInt(id), updates)
      return {
        id: device.id.toString(),
        name: device.name,
        type: device.type as DeviceType,
        config: device.config,
        position: device.x && device.y ? { x: device.x, y: device.y } : undefined,
      }
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update device')
    }
  }
)

export const deleteDeviceAsync = createAsyncThunk(
  'devices/deleteDeviceAsync',
  async (id: string, { rejectWithValue }) => {
    try {
      await devicesApi.deleteDevice(parseInt(id))
      return id
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete device')
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
      .addCase(createDeviceAsync.fulfilled, (state, action) => {
        state.items.push(action.payload)
      })
      .addCase(createBulkDevicesAsync.fulfilled, (state, action) => {
        state.items.push(...action.payload)
      })
      .addCase(updateDeviceAsync.fulfilled, (state, action) => {
        const index = state.items.findIndex(device => device.id === action.payload.id)
        if (index !== -1) {
          state.items[index] = action.payload
        }
      })
      .addCase(deleteDeviceAsync.fulfilled, (state, action) => {
        state.items = state.items.filter(device => device.id !== action.payload)
      })
  },
})

export const { createDevice, updateDevice, deleteDevice, resetDevices, setDevices } =
  devicesSlice.actions

export default devicesSlice.reducer

