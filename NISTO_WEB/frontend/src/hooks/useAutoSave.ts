import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { createSelector } from '@reduxjs/toolkit'
import { autoSaveProject, type AppDispatch, type RootState } from '../store'

// Memoized selector to prevent unnecessary rerenders
const selectDevicesConnectionsAndBoundaries = createSelector(
  [
    (state: RootState) => state.devices.items, 
    (state: RootState) => state.connections.items,
    (state: RootState) => state.boundaries.items
  ],
  (devices, connections, boundaries) => ({ devices, connections, boundaries })
)

export const useAutoSave = (intervalMs: number = 30000) => {
  const dispatch = useDispatch<AppDispatch>()
  const { devices, connections, boundaries } = useSelector(selectDevicesConnectionsAndBoundaries)
  const autoSaving = useSelector((state: RootState) => state.projects.autoSaving)
  
  const lastSavedState = useRef<string>('')
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null)
  const lastChangeTime = useRef<number>(0)

  // Calculate current state hash for comparison
  const getCurrentStateHash = () => {
    const state = { devices, connections, boundaries }
    return JSON.stringify(state)
  }

  // Trigger auto-save
  const triggerAutoSave = async () => {
    if (autoSaving) return // Don't auto-save if already in progress
    
    try {
      await dispatch(autoSaveProject()).unwrap()
      lastSavedState.current = getCurrentStateHash()
    } catch (error) {
      console.error('Auto-save failed:', error)
    }
  }

  // Check if state has changed and schedule auto-save
  const scheduleAutoSave = () => {
    const currentStateHash = getCurrentStateHash()
    
    // If state hasn't changed, don't schedule auto-save
    if (currentStateHash === lastSavedState.current) {
      return
    }

    lastChangeTime.current = Date.now()

    // Clear existing timer
    if (autoSaveTimer.current) {
      clearTimeout(autoSaveTimer.current)
    }

    // Schedule auto-save after delay
    autoSaveTimer.current = setTimeout(() => {
      // Only auto-save if enough time has passed since last change
      // This prevents constant auto-saving during rapid changes
      const timeSinceLastChange = Date.now() - lastChangeTime.current
      if (timeSinceLastChange >= 2000) { // 2 second debounce
        triggerAutoSave()
      } else {
        // Reschedule if changes are still happening
        scheduleAutoSave()
      }
    }, intervalMs)
  }

  // Monitor state changes
  useEffect(() => {
    scheduleAutoSave()
  }, [devices, connections, boundaries])

  // Initial state save on mount (if there's data)
  useEffect(() => {
    const currentStateHash = getCurrentStateHash()
    if (devices.length > 0 || connections.length > 0 || boundaries.length > 0) {
      lastSavedState.current = currentStateHash
    }
  }, [])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }
    }
  }, [])

  // Manual trigger for immediate auto-save
  const manualAutoSave = () => {
    if (autoSaveTimer.current) {
      clearTimeout(autoSaveTimer.current)
    }
    triggerAutoSave()
  }

  return {
    triggerAutoSave: manualAutoSave,
    isAutoSaving: autoSaving,
  }
}
