import { createAction } from '@reduxjs/toolkit'

import type { RootState } from './types'

export const undo = createAction('history/undo')
export const redo = createAction('history/redo')
export const restore = createAction<RootState>('history/restore')

