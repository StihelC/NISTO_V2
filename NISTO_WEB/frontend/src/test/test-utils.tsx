import type { ReactElement } from 'react'
import { render as rtlRender, type RenderOptions } from '@testing-library/react'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'

import devicesReducer from '../store/devicesSlice'
import connectionsReducer from '../store/connectionsSlice'
import uiReducer from '../store/uiSlice'
import projectsReducer from '../store/projectsSlice'
import type { RootState } from '../store'

interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Partial<RootState>
  store?: ReturnType<typeof configureStore>
  initialEntries?: string[]
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState = {},
    store = configureStore({
      reducer: {
        devices: devicesReducer,
        connections: connectionsReducer,
        ui: uiReducer,
        projects: projectsReducer,
      },
      preloadedState,
    }),
    initialEntries = ['/'],
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={initialEntries}>
          {children}
        </MemoryRouter>
      </Provider>
    )
  }
  return { store, ...rtlRender(ui, { wrapper: Wrapper, ...renderOptions }) }
}

export * from '@testing-library/react'
export { renderWithProviders as render }

// Mock device data for testing
export const mockDevice = {
  id: 'test-device-1',
  name: 'Test Switch',
  type: 'switch' as const,
  config: {},
  position: { x: 100, y: 100 }
}

export const mockDevices = [
  mockDevice,
  {
    id: 'test-device-2',
    name: 'Test Router',
    type: 'router' as const,
    config: {},
    position: { x: 200, y: 200 }
  }
]

export const mockConnection = {
  id: 'test-connection-1',
  sourceDeviceId: 'test-device-1',
  targetDeviceId: 'test-device-2',
  linkType: 'ethernet',
  properties: {}
}

export const mockConnections = [mockConnection]

// Helper to create initial state
export const createMockState = (overrides: Partial<RootState> = {}): Partial<RootState> => ({
  devices: { items: mockDevices },
  connections: { items: mockConnections },
  ui: { selected: null, history: { canUndo: false, canRedo: false } },
  projects: { items: [], current: null },
  ...overrides,
})

