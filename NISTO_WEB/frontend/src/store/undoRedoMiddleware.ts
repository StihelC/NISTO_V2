import type { AnyAction, Middleware } from '@reduxjs/toolkit'

import type { RootState } from './types'
import { setHistoryState } from './uiSlice'

interface HistoryEntry {
  state: RootState
}

const MAX_HISTORY = 50

const IGNORED_ACTIONS = new Set([setHistoryState.type, 'history/restore'])

export const createUndoRedoMiddleware = (): Middleware<{}, RootState> => {
  const past: HistoryEntry[] = []
  const future: HistoryEntry[] = []
  let isRestoring = false

  return (storeApi) => (next) => (incomingAction) => {
    const action = incomingAction as AnyAction
    if (action.type === 'history/undo') {
      const last = past.pop()
      if (!last) {
        return
      }
      future.push({ state: storeApi.getState() })
      isRestoring = true
      storeApi.dispatch({ type: 'history/restore', payload: last.state })
      isRestoring = false
      storeApi.dispatch(
        setHistoryState({ canUndo: past.length > 0, canRedo: future.length > 0 }),
      )
      return
    }

    if (action.type === 'history/redo') {
      const nextFuture = future.pop()
      if (!nextFuture) {
        return
      }
      past.push({ state: storeApi.getState() })
      isRestoring = true
      storeApi.dispatch({ type: 'history/restore', payload: nextFuture.state })
      isRestoring = false
      storeApi.dispatch(
        setHistoryState({ canUndo: past.length > 0, canRedo: future.length > 0 }),
      )
      return
    }

    const prevState = storeApi.getState()
    const result = next(action)
    const nextState = storeApi.getState()

    if (
      !isRestoring &&
      prevState !== nextState &&
      !IGNORED_ACTIONS.has(action.type)
    ) {
      past.push({ state: prevState })
      if (past.length > MAX_HISTORY) {
        past.shift()
      }
      future.length = 0
      storeApi.dispatch(
        setHistoryState({ canUndo: past.length > 0, canRedo: future.length > 0 }),
      )
    }

    return result
  }
}

