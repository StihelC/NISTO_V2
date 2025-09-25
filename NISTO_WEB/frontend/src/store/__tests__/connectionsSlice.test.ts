import { describe, it, expect } from 'vitest'

import connectionsReducer, {
  createConnection,
  updateConnection,
  deleteConnection,
  deleteConnectionsByDevice,
  resetConnections,
  setConnections,
} from '../connectionsSlice'
import type { ConnectionsState, Connection } from '../types'

const mockConnection: Connection = {
  id: 'connection-1',
  sourceDeviceId: 'device-1',
  targetDeviceId: 'device-2',
  linkType: 'ethernet',
  properties: {}
}

describe('connectionsSlice', () => {
  describe('synchronous actions', () => {
    it('should handle createConnection', () => {
      const newConnection = {
        sourceDeviceId: 'device-1',
        targetDeviceId: 'device-2',
        linkType: 'fiber',
        properties: { bandwidth: '1Gbps' }
      }

      const action = createConnection(newConnection)
      const result = connectionsReducer(undefined, action)

      expect(result.items).toHaveLength(1)
      expect(result.items[0]).toEqual(
        expect.objectContaining(newConnection)
      )
      expect(result.items[0].id).toBeDefined()
    })

    it('should handle updateConnection', () => {
      const initialState: ConnectionsState = {
        items: [mockConnection]
      }

      const action = updateConnection({ 
        id: 'connection-1', 
        linkType: 'fiber',
        properties: { bandwidth: '10Gbps' }
      })
      const result = connectionsReducer(initialState, action)

      expect(result.items[0]).toEqual({
        ...mockConnection,
        linkType: 'fiber',
        properties: { bandwidth: '10Gbps' }
      })
    })

    it('should ignore updateConnection for non-existent connection', () => {
      const initialState: ConnectionsState = {
        items: [mockConnection]
      }

      const action = updateConnection({ id: 'non-existent', linkType: 'fiber' })
      const result = connectionsReducer(initialState, action)

      expect(result).toEqual(initialState)
    })

    it('should handle deleteConnection', () => {
      const initialState: ConnectionsState = {
        items: [
          mockConnection,
          { ...mockConnection, id: 'connection-2', sourceDeviceId: 'device-3' }
        ]
      }

      const action = deleteConnection('connection-1')
      const result = connectionsReducer(initialState, action)

      expect(result.items).toHaveLength(1)
      expect(result.items[0].id).toBe('connection-2')
    })

    it('should handle deleteConnectionsByDevice', () => {
      const initialState: ConnectionsState = {
        items: [
          mockConnection,
          { ...mockConnection, id: 'connection-2', sourceDeviceId: 'device-3' },
          { ...mockConnection, id: 'connection-3', targetDeviceId: 'device-1' },
          { ...mockConnection, id: 'connection-4', sourceDeviceId: 'device-4', targetDeviceId: 'device-5' }
        ]
      }

      const action = deleteConnectionsByDevice('device-1')
      const result = connectionsReducer(initialState, action)

      // Should remove connections where device-1 is either source or target
      expect(result.items).toHaveLength(2)
      expect(result.items.find(c => c.id === 'connection-1')).toBeUndefined()
      expect(result.items.find(c => c.id === 'connection-3')).toBeUndefined()
      expect(result.items.find(c => c.id === 'connection-2')).toBeDefined()
      expect(result.items.find(c => c.id === 'connection-4')).toBeDefined()
    })

    it('should handle resetConnections', () => {
      const initialState: ConnectionsState = {
        items: [mockConnection]
      }

      const action = resetConnections()
      const result = connectionsReducer(initialState, action)

      expect(result.items).toEqual([])
    })

    it('should handle setConnections', () => {
      const connections = [
        mockConnection,
        { ...mockConnection, id: 'connection-2' }
      ]
      const action = setConnections(connections)
      const result = connectionsReducer(undefined, action)

      expect(result.items).toEqual(connections)
    })
  })

  describe('edge cases', () => {
    it('should handle multiple updates to same connection', () => {
      let state: ConnectionsState = { items: [mockConnection] }

      state = connectionsReducer(state, updateConnection({ 
        id: 'connection-1', 
        linkType: 'fiber' 
      }))
      state = connectionsReducer(state, updateConnection({ 
        id: 'connection-1', 
        properties: { bandwidth: '10Gbps' } 
      }))
      state = connectionsReducer(state, updateConnection({ 
        id: 'connection-1', 
        sourceDeviceId: 'device-3' 
      }))

      expect(state.items[0]).toEqual({
        ...mockConnection,
        linkType: 'fiber',
        properties: { bandwidth: '10Gbps' },
        sourceDeviceId: 'device-3'
      })
    })

    it('should preserve connection order when updating', () => {
      const connections = [
        { ...mockConnection, id: 'connection-1' },
        { ...mockConnection, id: 'connection-2' },
        { ...mockConnection, id: 'connection-3' },
      ]
      let state: ConnectionsState = { items: connections }

      state = connectionsReducer(state, updateConnection({ 
        id: 'connection-2', 
        linkType: 'fiber' 
      }))

      expect(state.items[0].id).toBe('connection-1')
      expect(state.items[1].id).toBe('connection-2')
      expect(state.items[1].linkType).toBe('fiber')
      expect(state.items[2].id).toBe('connection-3')
    })

    it('should handle deleteConnectionsByDevice when device has no connections', () => {
      const initialState: ConnectionsState = {
        items: [mockConnection]
      }

      const action = deleteConnectionsByDevice('non-existent-device')
      const result = connectionsReducer(initialState, action)

      expect(result.items).toEqual(initialState.items)
    })

    it('should handle connection creation with different link types', () => {
      const linkTypes = ['ethernet', 'fiber', 'vpn', 'wireless', 'serial']
      let state: ConnectionsState = { items: [] }

      linkTypes.forEach((linkType, index) => {
        state = connectionsReducer(
          state,
          createConnection({
            sourceDeviceId: 'device-1',
            targetDeviceId: 'device-2',
            linkType,
            properties: {}
          })
        )
      })

      expect(state.items).toHaveLength(linkTypes.length)
      linkTypes.forEach((linkType, index) => {
        expect(state.items[index].linkType).toBe(linkType)
      })
    })

    it('REGRESSION: should not duplicate connections', () => {
      let state: ConnectionsState = { items: [] }

      // Create same connection multiple times
      const connectionData = {
        sourceDeviceId: 'device-1',
        targetDeviceId: 'device-2',
        linkType: 'ethernet',
        properties: {}
      }

      state = connectionsReducer(state, createConnection(connectionData))
      state = connectionsReducer(state, createConnection(connectionData))
      state = connectionsReducer(state, createConnection(connectionData))

      // Should have 3 separate connections (each with unique ID)
      expect(state.items).toHaveLength(3)
      expect(new Set(state.items.map(c => c.id)).size).toBe(3) // All IDs should be unique
    })

    it('should handle complex device deletion scenarios', () => {
      const initialState: ConnectionsState = {
        items: [
          { id: 'c1', sourceDeviceId: 'device-1', targetDeviceId: 'device-2', linkType: 'ethernet', properties: {} },
          { id: 'c2', sourceDeviceId: 'device-2', targetDeviceId: 'device-3', linkType: 'fiber', properties: {} },
          { id: 'c3', sourceDeviceId: 'device-3', targetDeviceId: 'device-1', linkType: 'vpn', properties: {} },
          { id: 'c4', sourceDeviceId: 'device-4', targetDeviceId: 'device-5', linkType: 'ethernet', properties: {} },
        ]
      }

      // Delete device-1 (should remove c1 and c3)
      const result = connectionsReducer(initialState, deleteConnectionsByDevice('device-1'))

      expect(result.items).toHaveLength(2)
      expect(result.items.map(c => c.id)).toEqual(['c2', 'c4'])
    })
  })
})

