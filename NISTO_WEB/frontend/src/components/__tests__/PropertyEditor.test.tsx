import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import PropertyEditor from '../PropertyEditor'
import { render, createMockState, mockDevice, mockConnection } from '../../test/test-utils'
import { updateDeviceAsync } from '../../store/devicesSlice'
import { updateConnection } from '../../store/connectionsSlice'

// Mock the async thunks
vi.mock('../../store/devicesSlice', async () => {
  const actual = await vi.importActual('../../store/devicesSlice')
  return {
    ...actual,
    updateDeviceAsync: vi.fn(),
  }
})

vi.mock('../../store/connectionsSlice', async () => {
  const actual = await vi.importActual('../../store/connectionsSlice')
  return {
    ...actual,
    updateConnection: vi.fn(),
  }
})

const mockUpdateDeviceAsync = vi.mocked(updateDeviceAsync)
const mockUpdateConnection = vi.mocked(updateConnection)

describe('PropertyEditor Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUpdateDeviceAsync.mockReturnValue({ type: 'devices/updateDeviceAsync/pending' } as any)
    mockUpdateConnection.mockReturnValue({ type: 'connections/updateConnection', payload: {} } as any)
  })

  it('shows placeholder when no entity is selected', () => {
    const initialState = createMockState({
      ui: {
        selected: null,
        history: { canUndo: false, canRedo: false }
      }
    })
    render(<PropertyEditor />, { preloadedState: initialState })

    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('Select a device or connection.')).toBeInTheDocument()
  })

  describe('Device Properties', () => {
    it('displays device properties when device is selected', () => {
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      expect(screen.getByText('Device Properties')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Test Switch')).toBeInTheDocument()
      expect(screen.getByDisplayValue('switch')).toBeInTheDocument()
    })

    it('shows all property tabs', () => {
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      expect(screen.getByRole('button', { name: 'General' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Security' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Controls' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Risk' })).toBeInTheDocument()
    })

    it('REGRESSION: only dispatches updateDeviceAsync once when updating device name', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const nameInput = screen.getByDisplayValue('Test Switch')
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Switch')

      // Should only dispatch async action, not both local and async
      expect(mockUpdateDeviceAsync).toHaveBeenCalledTimes('Updated Switch'.length) // Once per character
      expect(mockUpdateDeviceAsync).toHaveBeenLastCalledWith({
        id: 'test-device-1',
        name: 'Updated Switch'
      })
    })

    it('REGRESSION: only dispatches updateDeviceAsync once when updating device type', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const typeSelect = screen.getByDisplayValue('switch')
      await user.selectOptions(typeSelect, 'router')

      expect(mockUpdateDeviceAsync).toHaveBeenCalledTimes(1)
      expect(mockUpdateDeviceAsync).toHaveBeenCalledWith({
        id: 'test-device-1',
        type: 'router'
      })
    })

    it('switches to security tab and shows security fields', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const securityTab = screen.getByRole('button', { name: 'Security' })
      await user.click(securityTab)

      expect(screen.getByText('Security Configuration')).toBeInTheDocument()
      expect(screen.getByLabelText('Patch Level')).toBeInTheDocument()
      expect(screen.getByLabelText('Encryption Status')).toBeInTheDocument()
      expect(screen.getByLabelText('Security Monitoring Enabled')).toBeInTheDocument()
    })

    it('updates security configuration fields', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const securityTab = screen.getByRole('button', { name: 'Security' })
      await user.click(securityTab)

      const patchLevelInput = screen.getByLabelText('Patch Level')
      await user.type(patchLevelInput, 'Current')

      expect(mockUpdateDeviceAsync).toHaveBeenCalledWith({
        id: 'test-device-1',
        config: {
          patchLevel: 'Current'
        }
      })
    })

    it('switches to risk tab and shows risk assessment fields', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const riskTab = screen.getByRole('button', { name: 'Risk' })
      await user.click(riskTab)

      expect(screen.getByText('Risk Assessment & Impact')).toBeInTheDocument()
      expect(screen.getByLabelText('Overall Risk Level')).toBeInTheDocument()
      expect(screen.getByLabelText('Confidentiality Impact')).toBeInTheDocument()
      expect(screen.getByLabelText('Integrity Impact')).toBeInTheDocument()
      expect(screen.getByLabelText('Availability Impact')).toBeInTheDocument()
    })

    it('switches to controls tab and shows NIST controls', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const controlsTab = screen.getByRole('button', { name: 'Controls' })
      await user.click(controlsTab)

      expect(screen.getByText('NIST Security Controls')).toBeInTheDocument()
      expect(screen.getByText('AC - Access Control')).toBeInTheDocument()
      expect(screen.getByText('AU - Audit and Accountability')).toBeInTheDocument()
    })

    it('updates NIST security controls', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const controlsTab = screen.getByRole('button', { name: 'Controls' })
      await user.click(controlsTab)

      // Find the first control select (AC - Access Control)
      const controlSelects = screen.getAllByDisplayValue('not_implemented')
      await user.selectOptions(controlSelects[0], 'implemented')

      expect(mockUpdateDeviceAsync).toHaveBeenCalledWith({
        id: 'test-device-1',
        config: {
          securityControls: expect.stringContaining('implemented')
        }
      })
    })

    it('resets tab to general when switching devices', () => {
      const { rerender } = render(<PropertyEditor />, {
        preloadedState: createMockState({
          ui: {
            selected: { kind: 'device', id: 'test-device-1' },
            history: { canUndo: false, canRedo: false }
          }
        })
      })

      // Switch to security tab
      const securityTab = screen.getByRole('button', { name: 'Security' })
      fireEvent.click(securityTab)
      expect(securityTab).toHaveClass('active')

      // Switch to different device
      rerender(<PropertyEditor />)
      const newState = createMockState({
        ui: {
          selected: { kind: 'device', id: 'test-device-2' },
          history: { canUndo: false, canRedo: false }
        }
      })
      
      // Should reset to general tab
      const generalTab = screen.getByRole('button', { name: 'General' })
      expect(generalTab).toHaveClass('active')
    })
  })

  describe('Connection Properties', () => {
    it('displays connection properties when connection is selected', () => {
      const initialState = createMockState({
        ui: {
          selected: { kind: 'connection', id: 'test-connection-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      expect(screen.getByText('Connection Properties')).toBeInTheDocument()
      expect(screen.getByDisplayValue('test-device-1')).toBeInTheDocument()
      expect(screen.getByDisplayValue('test-device-2')).toBeInTheDocument()
      expect(screen.getByDisplayValue('ethernet')).toBeInTheDocument()
    })

    it('updates connection properties', async () => {
      const user = userEvent.setup()
      const initialState = createMockState({
        ui: {
          selected: { kind: 'connection', id: 'test-connection-1' },
          history: { canUndo: false, canRedo: false }
        }
      })
      render(<PropertyEditor />, { preloadedState: initialState })

      const linkTypeInput = screen.getByDisplayValue('ethernet')
      await user.clear(linkTypeInput)
      await user.type(linkTypeInput, 'fiber')

      expect(mockUpdateConnection).toHaveBeenCalledWith({
        id: 'test-connection-1',
        linkType: 'fiber'
      })
    })
  })

  it('handles invalid selection gracefully', () => {
    const initialState = createMockState({
      devices: { items: [] }, // No devices
      ui: {
        selected: { kind: 'device', id: 'non-existent-device' },
        history: { canUndo: false, canRedo: false }
      }
    })
    render(<PropertyEditor />, { preloadedState: initialState })

    // Should show placeholder when selected device doesn't exist
    expect(screen.getByText('Select a device or connection.')).toBeInTheDocument()
  })
})
