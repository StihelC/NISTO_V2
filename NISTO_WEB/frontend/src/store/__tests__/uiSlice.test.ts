import { describe, it, expect } from 'vitest'

import uiReducer, { selectEntity, setHistoryState, resetUi } from '../uiSlice'
import type { UiState, SelectedEntity } from '../types'

describe('uiSlice', () => {
  const initialState: UiState = {
    selected: null,
    history: {
      canUndo: false,
      canRedo: false,
    },
  }

  describe('selectEntity', () => {
    it('should select a device', () => {
      const deviceSelection: SelectedEntity = { kind: 'device', id: 'device-1' }
      const action = selectEntity(deviceSelection)
      const result = uiReducer(initialState, action)

      expect(result.selected).toEqual(deviceSelection)
    })

    it('should select a connection', () => {
      const connectionSelection: SelectedEntity = { kind: 'connection', id: 'connection-1' }
      const action = selectEntity(connectionSelection)
      const result = uiReducer(initialState, action)

      expect(result.selected).toEqual(connectionSelection)
    })

    it('should clear selection when null is passed', () => {
      const stateWithSelection: UiState = {
        ...initialState,
        selected: { kind: 'device', id: 'device-1' }
      }

      const action = selectEntity(null)
      const result = uiReducer(stateWithSelection, action)

      expect(result.selected).toBeNull()
    })

    it('should replace previous selection', () => {
      const stateWithSelection: UiState = {
        ...initialState,
        selected: { kind: 'device', id: 'device-1' }
      }

      const newSelection: SelectedEntity = { kind: 'connection', id: 'connection-1' }
      const action = selectEntity(newSelection)
      const result = uiReducer(stateWithSelection, action)

      expect(result.selected).toEqual(newSelection)
    })
  })

  describe('setHistoryState', () => {
    it('should set history state with undo available', () => {
      const historyState = { canUndo: true, canRedo: false }
      const action = setHistoryState(historyState)
      const result = uiReducer(initialState, action)

      expect(result.history).toEqual(historyState)
    })

    it('should set history state with redo available', () => {
      const historyState = { canUndo: false, canRedo: true }
      const action = setHistoryState(historyState)
      const result = uiReducer(initialState, action)

      expect(result.history).toEqual(historyState)
    })

    it('should set history state with both undo and redo available', () => {
      const historyState = { canUndo: true, canRedo: true }
      const action = setHistoryState(historyState)
      const result = uiReducer(initialState, action)

      expect(result.history).toEqual(historyState)
    })

    it('should preserve selection when updating history', () => {
      const stateWithSelection: UiState = {
        ...initialState,
        selected: { kind: 'device', id: 'device-1' }
      }

      const historyState = { canUndo: true, canRedo: false }
      const action = setHistoryState(historyState)
      const result = uiReducer(stateWithSelection, action)

      expect(result.selected).toEqual(stateWithSelection.selected)
      expect(result.history).toEqual(historyState)
    })
  })

  describe('resetUi', () => {
    it('should reset to initial state', () => {
      const modifiedState: UiState = {
        selected: { kind: 'device', id: 'device-1' },
        history: { canUndo: true, canRedo: true }
      }

      const action = resetUi()
      const result = uiReducer(modifiedState, action)

      expect(result).toEqual(initialState)
    })

    it('should not change state if already at initial state', () => {
      const action = resetUi()
      const result = uiReducer(initialState, action)

      expect(result).toEqual(initialState)
    })
  })

  describe('complex scenarios', () => {
    it('should handle selection changes with history updates', () => {
      let state = initialState

      // Select a device
      state = uiReducer(state, selectEntity({ kind: 'device', id: 'device-1' }))
      expect(state.selected).toEqual({ kind: 'device', id: 'device-1' })

      // Update history
      state = uiReducer(state, setHistoryState({ canUndo: true, canRedo: false }))
      expect(state.history).toEqual({ canUndo: true, canRedo: false })
      expect(state.selected).toEqual({ kind: 'device', id: 'device-1' })

      // Change selection
      state = uiReducer(state, selectEntity({ kind: 'connection', id: 'connection-1' }))
      expect(state.selected).toEqual({ kind: 'connection', id: 'connection-1' })
      expect(state.history).toEqual({ canUndo: true, canRedo: false })

      // Clear selection
      state = uiReducer(state, selectEntity(null))
      expect(state.selected).toBeNull()
      expect(state.history).toEqual({ canUndo: true, canRedo: false })
    })

    it('REGRESSION: should maintain selection persistence', () => {
      let state = initialState

      // Select a device
      const deviceSelection = { kind: 'device', id: 'device-1' } as SelectedEntity
      state = uiReducer(state, selectEntity(deviceSelection))

      // Verify selection persists through multiple state updates
      state = uiReducer(state, setHistoryState({ canUndo: true, canRedo: false }))
      state = uiReducer(state, setHistoryState({ canUndo: false, canRedo: true }))

      expect(state.selected).toEqual(deviceSelection)
    })

    it('should handle rapid selection changes', () => {
      let state = initialState

      const selections: SelectedEntity[] = [
        { kind: 'device', id: 'device-1' },
        { kind: 'device', id: 'device-2' },
        { kind: 'connection', id: 'connection-1' },
        { kind: 'device', id: 'device-3' },
      ]

      selections.forEach(selection => {
        state = uiReducer(state, selectEntity(selection))
        expect(state.selected).toEqual(selection)
      })

      // Final selection should be the last one
      expect(state.selected).toEqual(selections[selections.length - 1])
    })
  })
})

