import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import TopologyCanvas from '../TopologyCanvas'
import { render, createMockState, mockDevices } from '../../test/test-utils'
import { updateDeviceAsync } from '../../store/devicesSlice'
import { selectEntity } from '../../store/uiSlice'

// Mock the async thunks
vi.mock('../../store/devicesSlice', async () => {
  const actual = await vi.importActual('../../store/devicesSlice')
  return {
    ...actual,
    updateDeviceAsync: vi.fn(),
  }
})

vi.mock('../../store/uiSlice', async () => {
  const actual = await vi.importActual('../../store/uiSlice')
  return {
    ...actual,
    selectEntity: vi.fn(),
  }
})

const mockUpdateDeviceAsync = vi.mocked(updateDeviceAsync)
const mockSelectEntity = vi.mocked(selectEntity)

// Mock SVG methods that aren't available in jsdom
Object.defineProperty(SVGElement.prototype, 'getScreenCTM', {
  writable: true,
  value: vi.fn().mockReturnValue({
    a: 1, b: 0, c: 0, d: 1, e: 0, f: 0,
    inverse: vi.fn().mockReturnValue({ a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 })
  })
})

Object.defineProperty(SVGElement.prototype, 'createSVGPoint', {
  writable: true,
  value: vi.fn().mockReturnValue({ x: 0, y: 0, matrixTransform: vi.fn().mockReturnValue({ x: 100, y: 100 }) })
})

describe('TopologyCanvas Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUpdateDeviceAsync.mockReturnValue({ type: 'devices/updateDeviceAsync/pending' } as any)
    mockSelectEntity.mockReturnValue({ type: 'ui/selectEntity', payload: null } as any)
    
    // Mock getBoundingClientRect for the container
    Element.prototype.getBoundingClientRect = vi.fn().mockReturnValue({
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      bottom: 600,
      right: 800,
    })
  })

  it('renders canvas with devices', () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    // Check if SVG canvas is rendered
    const canvas = screen.getByRole('img', { hidden: true }) // SVG has implicit img role
    expect(canvas).toBeInTheDocument()
  })

  it('renders devices at their positions', () => {
    const initialState = createMockState({
      devices: {
        items: [
          {
            id: 'device-1',
            name: 'Test Device',
            type: 'switch',
            config: {},
            position: { x: 200, y: 300 }
          }
        ]
      }
    })
    render(<TopologyCanvas />, { preloadedState: initialState })

    // Find the device group element
    const deviceGroup = screen.getByText('Test Device').closest('g')
    expect(deviceGroup).toHaveAttribute('transform', 'translate(200, 300)')
  })

  it('REGRESSION: selects device on click', async () => {
    const user = userEvent.setup()
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const deviceElement = screen.getByText('Test Switch').closest('g')
    expect(deviceElement).toBeInTheDocument()

    // Click on the device
    await user.click(deviceElement!)

    expect(mockSelectEntity).toHaveBeenCalledWith({
      kind: 'device',
      id: 'test-device-1'
    })
  })

  it('REGRESSION: device selection persists after click', async () => {
    const user = userEvent.setup()
    const initialState = createMockState({
      ui: {
        selected: { kind: 'device', id: 'test-device-1' },
        history: { canUndo: false, canRedo: false }
      }
    })
    render(<TopologyCanvas />, { preloadedState: initialState })

    const selectedDevice = screen.getByText('Test Switch').closest('g')
    expect(selectedDevice).toHaveClass('is-selected')
  })

  it('REGRESSION: only updates position after actual drag, not click', async () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const deviceElement = screen.getByText('Test Switch').closest('g')!

    // Simulate a click (pointer down + up without movement)
    fireEvent.pointerDown(deviceElement, { 
      clientX: 100, 
      clientY: 100,
      pointerId: 1 
    })
    fireEvent.pointerUp(deviceElement, { pointerId: 1 })

    // Should not update position for a click
    expect(mockUpdateDeviceAsync).not.toHaveBeenCalled()
  })

  it('updates position only after drag movement', async () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const deviceElement = screen.getByText('Test Switch').closest('g')!

    // Simulate drag with significant movement
    fireEvent.pointerDown(deviceElement, { 
      clientX: 100, 
      clientY: 100,
      pointerId: 1 
    })
    
    // Move more than the threshold (5px)
    fireEvent.pointerMove(deviceElement, { 
      clientX: 120, 
      clientY: 130,
      pointerId: 1 
    })
    
    fireEvent.pointerUp(deviceElement, { pointerId: 1 })

    // Should update position for a drag
    expect(mockUpdateDeviceAsync).toHaveBeenCalledTimes(1)
  })

  it('shows different device types with correct styling', () => {
    const initialState = createMockState({
      devices: {
        items: [
          { id: '1', name: 'Switch', type: 'switch', config: {}, position: { x: 100, y: 100 } },
          { id: '2', name: 'Router', type: 'router', config: {}, position: { x: 200, y: 100 } },
          { id: '3', name: 'Firewall', type: 'firewall', config: {}, position: { x: 300, y: 100 } },
          { id: '4', name: 'Server', type: 'server', config: {}, position: { x: 400, y: 100 } },
        ]
      }
    })
    render(<TopologyCanvas />, { preloadedState: initialState })

    expect(screen.getByText('Switch')).toBeInTheDocument()
    expect(screen.getByText('Router')).toBeInTheDocument()
    expect(screen.getByText('Firewall')).toBeInTheDocument()
    expect(screen.getByText('Server')).toBeInTheDocument()
  })

  it('renders connections between devices', () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    // Look for connection line elements
    const connections = screen.getByRole('img', { hidden: true }).querySelectorAll('line')
    expect(connections.length).toBeGreaterThan(0)
  })

  it('handles zoom functionality', () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const canvas = screen.getByRole('img', { hidden: true })
    
    // Test zoom in
    fireEvent.wheel(canvas, { deltaY: -100 })
    
    // Test zoom out  
    fireEvent.wheel(canvas, { deltaY: 100 })
    
    // Canvas should still be rendered (basic smoke test)
    expect(canvas).toBeInTheDocument()
  })

  it('handles pan functionality', () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const canvas = screen.getByRole('img', { hidden: true })
    
    // Simulate pan gesture
    fireEvent.pointerDown(canvas, { 
      clientX: 100, 
      clientY: 100,
      pointerId: 1,
      button: 0
    })
    
    fireEvent.pointerMove(canvas, { 
      clientX: 150, 
      clientY: 150,
      pointerId: 1 
    })
    
    fireEvent.pointerUp(canvas, { pointerId: 1 })
    
    // Canvas should still be rendered (basic smoke test)
    expect(canvas).toBeInTheDocument()
  })

  it('prevents device updates when dragging is cancelled', () => {
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const deviceElement = screen.getByText('Test Switch').closest('g')!

    // Start drag
    fireEvent.pointerDown(deviceElement, { 
      clientX: 100, 
      clientY: 100,
      pointerId: 1 
    })
    
    // Move significantly
    fireEvent.pointerMove(deviceElement, { 
      clientX: 120, 
      clientY: 130,
      pointerId: 1 
    })
    
    // Cancel instead of releasing
    fireEvent.pointerCancel(deviceElement, { pointerId: 1 })

    // Should not update position for cancelled drag
    expect(mockUpdateDeviceAsync).not.toHaveBeenCalled()
  })

  it('handles multiple device selection correctly', async () => {
    const user = userEvent.setup()
    const initialState = createMockState()
    render(<TopologyCanvas />, { preloadedState: initialState })

    const device1 = screen.getByText('Test Switch').closest('g')!
    const device2 = screen.getByText('Test Router').closest('g')!

    // Select first device
    await user.click(device1)
    expect(mockSelectEntity).toHaveBeenCalledWith({
      kind: 'device',
      id: 'test-device-1'
    })

    // Select second device
    await user.click(device2)
    expect(mockSelectEntity).toHaveBeenCalledWith({
      kind: 'device',
      id: 'test-device-2'
    })

    expect(mockSelectEntity).toHaveBeenCalledTimes(2)
  })
})
