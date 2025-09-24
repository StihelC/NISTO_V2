import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { SelectedEntity, UiState } from './types'

const initialState: UiState = {
  selected: null,
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

export const { selectEntity, setHistoryState, resetUi } = uiSlice.actions

export default uiSlice.reducer

