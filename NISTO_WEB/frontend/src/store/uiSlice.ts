import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { SelectedEntity, UiState, MultiSelection } from './types'

const initialState: UiState = {
  selected: null,
  multiSelected: null,
  history: {
    canUndo: false,
    canRedo: false,
  },
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    selectEntity(state, action: PayloadAction<SelectedEntity>) {
      state.selected = action.payload
      // Clear multi-selection when single selecting
      state.multiSelected = null
    },
    toggleMultiSelect(state, action: PayloadAction<{ kind: 'device' | 'connection', id: string }>) {
      const { kind, id } = action.payload
      
      if (!state.multiSelected || state.multiSelected.kind !== kind) {
        // Start new multi-selection with current item
        state.multiSelected = { kind, ids: [id] }
        state.selected = null
      } else {
        // Toggle the item in existing multi-selection
        const index = state.multiSelected.ids.indexOf(id)
        if (index >= 0) {
          // Remove from selection
          state.multiSelected.ids.splice(index, 1)
          if (state.multiSelected.ids.length === 0) {
            state.multiSelected = null
          }
        } else {
          // Add to selection
          state.multiSelected.ids.push(id)
        }
      }
    },
    clearMultiSelection(state) {
      state.multiSelected = null
    },
    setHistoryState(
      state,
      action: PayloadAction<{ canUndo: boolean; canRedo: boolean }>,
    ) {
      state.history = action.payload
    },
    resetUi() {
      return initialState
    },
  },
})

export const { selectEntity, toggleMultiSelect, clearMultiSelection, setHistoryState, resetUi } = uiSlice.actions

export default uiSlice.reducer

