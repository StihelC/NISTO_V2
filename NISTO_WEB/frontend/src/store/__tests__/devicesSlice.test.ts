import { describe, it, expect, vi, beforeEach } from 'vitest'
import { configureStore } from '@reduxjs/toolkit'

import devicesReducer, {
  createDevice,
  updateDevice,
  deleteDevice,
  resetDevices,
  setDevices,
  createDeviceAsync,
  updateDeviceAsync,
  deleteDeviceAsync,
  fetchDevices,
} from '../devicesSlice'
import type { DevicesState, Device } from '../types'

// Mock the API
vi.mock('../../api/devices', () => ({
  devicesApi: {
    getDevices: vi.fn(),
    createDevice: vi.fn(),
    updateDevice: vi.fn(),
    deleteDevice: vi.fn(),
  }
}))

const mockDevice: Device = {
  id: 'test-device-1',
  name: 'Test Switch',
  type: 'switch',
  config: {},
  position: { x: 100, y: 100 }
}

describe('devicesSlice', () => {
  let store: ReturnType<typeof configureStore>

  beforeEach(() => {
    store = configureStore({
      reducer: {
        devices: devicesReducer,
      },
    })
  })

  describe('synchronous actions', () => {
    it('should handle createDevice', () => {
      const action = createDevice({ name: 'New Device', type: 'router' })
      const result = devicesReducer(undefined, action)

      expect(result.items).toHaveLength(1)
      expect(result.items[0]).toEqual(
        expect.objectContaining({
          name: 'New Device',
          type: 'router',
          config: {},
        })
      )
      expect(result.items[0].id).toBeDefined()
    })

    it('should handle updateDevice', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const action = updateDevice({ id: 'test-device-1', name: 'Updated Device' })
      const result = devicesReducer(initialState, action)

      expect(result.items[0]).toEqual({
        ...mockDevice,
        name: 'Updated Device'
      })
    })

    it('should handle updateDevice with config changes', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const newConfig = { riskLevel: 'High', patchLevel: 'Current' }
      const action = updateDevice({ id: 'test-device-1', config: newConfig })
      const result = devicesReducer(initialState, action)

      expect(result.items[0].config).toEqual(newConfig)
    })

    it('should handle updateDevice with position changes', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const newPosition = { x: 200, y: 300 }
      const action = updateDevice({ id: 'test-device-1', position: newPosition })
      const result = devicesReducer(initialState, action)

      expect(result.items[0].position).toEqual(newPosition)
    })

    it('should ignore updateDevice for non-existent device', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const action = updateDevice({ id: 'non-existent', name: 'Updated' })
      const result = devicesReducer(initialState, action)

      expect(result).toEqual(initialState)
    })

    it('should handle deleteDevice', () => {
      const initialState: DevicesState = {
        items: [mockDevice, { ...mockDevice, id: 'device-2', name: 'Device 2' }]
      }

      const action = deleteDevice('test-device-1')
      const result = devicesReducer(initialState, action)

      expect(result.items).toHaveLength(1)
      expect(result.items[0].id).toBe('device-2')
    })

    it('should handle resetDevices', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const action = resetDevices()
      const result = devicesReducer(initialState, action)

      expect(result.items).toEqual([])
    })

    it('should handle setDevices', () => {
      const devices = [mockDevice, { ...mockDevice, id: 'device-2' }]
      const action = setDevices(devices)
      const result = devicesReducer(undefined, action)

      expect(result.items).toEqual(devices)
    })
  })

  describe('async thunks', () => {
    it('should handle fetchDevices.fulfilled', () => {
      const devices = [mockDevice]
      const action = { type: fetchDevices.fulfilled.type, payload: devices }
      const result = devicesReducer(undefined, action)

      expect(result.items).toEqual(devices)
    })

    it('should handle createDeviceAsync.fulfilled', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const newDevice = { ...mockDevice, id: 'device-2', name: 'New Device' }
      const action = { type: createDeviceAsync.fulfilled.type, payload: newDevice }
      const result = devicesReducer(initialState, action)

      expect(result.items).toHaveLength(2)
      expect(result.items[1]).toEqual(newDevice)
    })

    it('should handle updateDeviceAsync.fulfilled', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const updatedDevice = { ...mockDevice, name: 'Updated Device' }
      const action = { type: updateDeviceAsync.fulfilled.type, payload: updatedDevice }
      const result = devicesReducer(initialState, action)

      expect(result.items[0]).toEqual(updatedDevice)
    })

    it('should handle updateDeviceAsync.fulfilled for non-existent device', () => {
      const initialState: DevicesState = {
        items: [mockDevice]
      }

      const nonExistentDevice = { ...mockDevice, id: 'non-existent' }
      const action = { type: updateDeviceAsync.fulfilled.type, payload: nonExistentDevice }
      const result = devicesReducer(initialState, action)

      // Should not change the state if device doesn't exist
      expect(result.items).toEqual(initialState.items)
    })

    it('should handle deleteDeviceAsync.fulfilled', () => {
      const initialState: DevicesState = {
        items: [mockDevice, { ...mockDevice, id: 'device-2' }]
      }

      const action = { type: deleteDeviceAsync.fulfilled.type, payload: 'test-device-1' }
      const result = devicesReducer(initialState, action)

      expect(result.items).toHaveLength(1)
      expect(result.items[0].id).toBe('device-2')
    })
  })

  describe('edge cases', () => {
    it('should handle multiple updates to same device', () => {
      let state: DevicesState = { items: [mockDevice] }

      state = devicesReducer(state, updateDevice({ id: 'test-device-1', name: 'First Update' }))
      state = devicesReducer(state, updateDevice({ id: 'test-device-1', type: 'router' }))
      state = devicesReducer(state, updateDevice({ id: 'test-device-1', config: { riskLevel: 'High' } }))

      expect(state.items[0]).toEqual({
        ...mockDevice,
        name: 'First Update',
        type: 'router',
        config: { riskLevel: 'High' }
      })
    })

    it('should handle device creation with all device types', () => {
      const deviceTypes = ['switch', 'router', 'firewall', 'server', 'workstation', 'generic'] as const
      let state: DevicesState = { items: [] }

      deviceTypes.forEach((type, index) => {
        state = devicesReducer(
          state,
          createDevice({ name: `Device ${index}`, type })
        )
      })

      expect(state.items).toHaveLength(deviceTypes.length)
      deviceTypes.forEach((type, index) => {
        expect(state.items[index].type).toBe(type)
      })
    })

    it('should preserve device order when updating', () => {
      const devices = [
        { ...mockDevice, id: 'device-1', name: 'Device 1' },
        { ...mockDevice, id: 'device-2', name: 'Device 2' },
        { ...mockDevice, id: 'device-3', name: 'Device 3' },
      ]
      let state: DevicesState = { items: devices }

      state = devicesReducer(state, updateDevice({ id: 'device-2', name: 'Updated Device 2' }))

      expect(state.items[0].id).toBe('device-1')
      expect(state.items[1].id).toBe('device-2')
      expect(state.items[1].name).toBe('Updated Device 2')
      expect(state.items[2].id).toBe('device-3')
    })
  })
})
