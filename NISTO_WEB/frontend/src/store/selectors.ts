import { createSelector } from '@reduxjs/toolkit'

import type { RootState } from './types'

export const selectDevices = (state: RootState) => state.devices.items
export const selectConnections = (state: RootState) => state.connections.items
export const selectUi = (state: RootState) => state.ui

export const selectHistory = createSelector(selectUi, (ui) => ui.history)

export const selectSelectedEntity = createSelector(selectUi, (ui) => ui.selected)

export const selectDeviceById = (id: string) =>
  createSelector(selectDevices, (devices) => devices.find((device) => device.id === id))

export const selectConnectionById = (id: string) =>
  createSelector(
    selectConnections,
    (connections) => connections.find((connection) => connection.id === id),
  )
