import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import DeviceList from '../DeviceList'
import { render, createMockState, mockDevices } from '../../test/test-utils'
import { createDeviceAsync, deleteDeviceAsync } from '../../store/devicesSlice'

// Mock the async thunks
vi.mock('../../store/devicesSlice', async () => {
  const actual = await vi.importActual('../../store/devicesSlice')
  return {
    ...actual,
    createDeviceAsync: vi.fn(),
    deleteDeviceAsync: vi.fn(),
  }
})

const mockCreateDeviceAsync = vi.mocked(createDeviceAsync)
const mockDeleteDeviceAsync = vi.mocked(deleteDeviceAsync)

describe('DeviceList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock the thunk creators to return action objects
    mockCreateDeviceAsync.mockReturnValue({ type: 'devices/createDeviceAsync/pending' } as any)
    mockDeleteDeviceAsync.mockReturnValue({ type: 'devices/deleteDeviceAsync/pending' } as any)
  })

  it('renders device list correctly', () => {
    const initialState = createMockState()
    render(<DeviceList />, { preloadedState: initialState })

    expect(screen.getByText('Devices')).toBeInTheDocument()
    expect(screen.getByText('Test Switch')).toBeInTheDocument()
    expect(screen.getByText('Test Router')).toBeInTheDocument()
  })

  it('renders empty state when no devices', () => {
    const initialState = createMockState({
      devices: { items: [] }
    })
    render(<DeviceList />, { preloadedState: initialState })

    expect(screen.getByText('No devices yet.')).toBeInTheDocument()
  })

  it('renders device creation form', () => {
    render(<DeviceList />)

    expect(screen.getByLabelText('Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Type')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Device' })).toBeInTheDocument()
  })

  it('REGRESSION: only dispatches createDeviceAsync once when creating device', async () => {
    const user = userEvent.setup()
    const { store } = render(<DeviceList />)

    const nameInput = screen.getByLabelText('Name')
    const typeSelect = screen.getByLabelText('Type')
    const addButton = screen.getByRole('button', { name: 'Add Device' })

    await user.type(nameInput, 'New Device')
    await user.selectOptions(typeSelect, 'router')
    await user.click(addButton)

    // Verify only async action is dispatched (not both local and async)
    expect(mockCreateDeviceAsync).toHaveBeenCalledTimes(1)
    expect(mockCreateDeviceAsync).toHaveBeenCalledWith({
      name: 'New Device',
      type: 'router'
    })

    // Verify form is cleared after submission
    expect(nameInput).toHaveValue('')
    expect(typeSelect).toHaveValue('switch') // default value
  })

  it('shows validation error for empty name', async () => {
    const user = userEvent.setup()
    render(<DeviceList />)

    const addButton = screen.getByRole('button', { name: 'Add Device' })
    await user.click(addButton)

    expect(screen.getByText('Name is required')).toBeInTheDocument()
    expect(mockCreateDeviceAsync).not.toHaveBeenCalled()
  })

  it('clears validation error when name is provided', async () => {
    const user = userEvent.setup()
    render(<DeviceList />)

    const nameInput = screen.getByLabelText('Name')
    const addButton = screen.getByRole('button', { name: 'Add Device' })

    // Trigger validation error
    await user.click(addButton)
    expect(screen.getByText('Name is required')).toBeInTheDocument()

    // Provide name and submit again
    await user.type(nameInput, 'Valid Name')
    await user.click(addButton)

    expect(screen.queryByText('Name is required')).not.toBeInTheDocument()
  })

  it('REGRESSION: only dispatches deleteDeviceAsync once when deleting device', async () => {
    const user = userEvent.setup()
    const initialState = createMockState()
    render(<DeviceList />, { preloadedState: initialState })

    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    // Verify only async action is dispatched (not both local and async)
    expect(mockDeleteDeviceAsync).toHaveBeenCalledTimes(1)
    expect(mockDeleteDeviceAsync).toHaveBeenCalledWith('test-device-1')
  })

  it('selects device when clicked', async () => {
    const user = userEvent.setup()
    const { store } = render(<DeviceList />)

    const deviceButton = screen.getByRole('button', { name: /Test Switch/ })
    await user.click(deviceButton)

    const actions = store.getState()
    // We can't easily test the dispatch directly due to mocking, but we can verify the UI state
    expect(deviceButton.closest('.list-item')).toHaveClass('is-selected')
  })

  it('supports all device types', async () => {
    const user = userEvent.setup()
    render(<DeviceList />)

    const typeSelect = screen.getByLabelText('Type')
    const options = Array.from(typeSelect.querySelectorAll('option')).map(opt => opt.value)

    expect(options).toEqual(['switch', 'router', 'firewall', 'server', 'workstation', 'generic'])
  })

  it('handles device creation with different types', async () => {
    const user = userEvent.setup()
    render(<DeviceList />)

    const nameInput = screen.getByLabelText('Name')
    const typeSelect = screen.getByLabelText('Type')
    const addButton = screen.getByRole('button', { name: 'Add Device' })

    // Test each device type
    const deviceTypes = ['switch', 'router', 'firewall', 'server', 'workstation', 'generic']
    
    for (const deviceType of deviceTypes) {
      await user.clear(nameInput)
      await user.type(nameInput, `Test ${deviceType}`)
      await user.selectOptions(typeSelect, deviceType)
      await user.click(addButton)

      expect(mockCreateDeviceAsync).toHaveBeenCalledWith({
        name: `Test ${deviceType}`,
        type: deviceType
      })
    }

    expect(mockCreateDeviceAsync).toHaveBeenCalledTimes(deviceTypes.length)
  })

  it('maintains selection state correctly', () => {
    const initialState = createMockState({
      ui: {
        selected: { kind: 'device', id: 'test-device-1' },
        history: { canUndo: false, canRedo: false }
      }
    })
    render(<DeviceList />, { preloadedState: initialState })

    const selectedDevice = screen.getByRole('button', { name: /Test Switch/ })
    expect(selectedDevice.closest('.list-item')).toHaveClass('is-selected')

    const otherDevice = screen.getByRole('button', { name: /Test Router/ })
    expect(otherDevice.closest('.list-item')).not.toHaveClass('is-selected')
  })
})
