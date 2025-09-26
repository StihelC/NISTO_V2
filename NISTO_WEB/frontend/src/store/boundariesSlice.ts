import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { Boundary, BoundaryType, BoundariesState } from './types'
import { boundariesApi, type BoundaryResponse } from '../api/boundaries'

const MIN_BOUNDARY_SIZE = 20

const computeBoundingBox = (points: Array<{ x: number; y: number }> | undefined) => {
  if (!points || points.length === 0) {
    return { x: 0, y: 0, width: 200, height: 200 }
  }

  const xs = points.map(point => point.x)
  const ys = points.map(point => point.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)

  return {
    x: minX,
    y: minY,
    width: Math.max(maxX - minX, MIN_BOUNDARY_SIZE),
    height: Math.max(maxY - minY, MIN_BOUNDARY_SIZE)
  }
}

const isDefinedNumber = (value: number | null | undefined): value is number =>
  value !== null && value !== undefined

const normalizeBoundary = (boundary: BoundaryResponse): Boundary => {
  const hasExplicitDimensions =
    isDefinedNumber(boundary.x) &&
    isDefinedNumber(boundary.y) &&
    isDefinedNumber(boundary.width) &&
    isDefinedNumber(boundary.height)

  const dimensions = hasExplicitDimensions
    ? {
        x: boundary.x!,
        y: boundary.y!,
        width: Math.max(boundary.width!, MIN_BOUNDARY_SIZE),
        height: Math.max(boundary.height!, MIN_BOUNDARY_SIZE)
      }
    : computeBoundingBox(boundary.points)

  return {
    id: boundary.id,
    type: boundary.type as BoundaryType,
    label: boundary.label,
    points: boundary.points,
    closed: boundary.closed,
    style: boundary.style,
    created: boundary.created,
    position: dimensions,
    x: dimensions.x,
    y: dimensions.y,
    width: dimensions.width,
    height: dimensions.height,
    config: boundary.config || {}
  }
}

const mergeWithExistingBoundary = (existing: Boundary | undefined, response: BoundaryResponse): Boundary => {
  const normalized = normalizeBoundary(response)

  const serverProvidedDimensions =
    isDefinedNumber(response.x) &&
    isDefinedNumber(response.y) &&
    isDefinedNumber(response.width) &&
    isDefinedNumber(response.height)

  if (!serverProvidedDimensions && existing) {
    return {
      ...normalized,
      position: existing.position,
      x: existing.x,
      y: existing.y,
      width: existing.width,
      height: existing.height,
    }
  }

  return normalized
}

// Boundary style presets
export const BOUNDARY_STYLES = {
  ato: {
    color: '#dc2626', // Red
    strokeWidth: 3,
    dashArray: '10,5',
    fill: '#fef2f2',
    fillOpacity: 0.1
  },
  building: {
    color: '#7c3aed', // Purple
    strokeWidth: 2,
    fill: '#f5f3ff',
    fillOpacity: 0.05
  },
  network_segment: {
    color: '#2563eb', // Blue
    strokeWidth: 2,
    dashArray: '5,5',
    fill: '#eff6ff',
    fillOpacity: 0.08
  },
  security_zone: {
    color: '#ea580c', // Orange
    strokeWidth: 3,
    dashArray: '8,4',
    fill: '#fff7ed',
    fillOpacity: 0.1
  },
  physical_location: {
    color: '#059669', // Green
    strokeWidth: 2,
    fill: '#ecfdf5',
    fillOpacity: 0.05
  },
  logical_group: {
    color: '#7c2d12', // Brown
    strokeWidth: 2,
    dashArray: '3,3',
    fill: '#fef7f0',
    fillOpacity: 0.06
  }
}

export const BOUNDARY_LABELS = {
  ato: 'ATO Boundary',
  building: 'Building/Facility',
  network_segment: 'Network Segment',
  security_zone: 'Security Zone',
  physical_location: 'Physical Location',
  logical_group: 'Logical Group'
}

// Async thunks for API operations
export const fetchBoundaries = createAsyncThunk(
  'boundaries/fetchBoundaries',
  async () => {
    const boundaries = await boundariesApi.getBoundaries()
    return boundaries
  }
)

export const createBoundaryAsync = createAsyncThunk(
  'boundaries/createBoundary',
  async (boundary: Boundary) => {
    const created = await boundariesApi.createBoundary({
      id: boundary.id,
      type: boundary.type,
      label: boundary.label,
      points: boundary.points,
      closed: boundary.closed,
      style: boundary.style,
      created: boundary.created,
      x: boundary.position?.x ?? boundary.x,
      y: boundary.position?.y ?? boundary.y,
      width: boundary.position?.width ?? boundary.width,
      height: boundary.position?.height ?? boundary.height,
      config: boundary.config || {}
    })
    return created
  }
)

export const updateBoundaryAsync = createAsyncThunk(
  'boundaries/updateBoundary',
  async ({ id, updates }: { id: string; updates: Partial<Boundary> }) => {
    const updated = await boundariesApi.updateBoundary(id, updates)
    return updated
  }
)

export const deleteBoundaryAsync = createAsyncThunk(
  'boundaries/deleteBoundary',
  async (id: string) => {
    await boundariesApi.deleteBoundary(id)
    return id
  }
)

const initialState: BoundariesState = {
  items: [],
  isDrawing: false,
  currentBoundaryType: null,
  drawingPoints: []
}

const boundariesSlice = createSlice({
  name: 'boundaries',
  initialState,
  reducers: {
    startDrawing: (state, action: PayloadAction<BoundaryType>) => {
      state.isDrawing = true
      state.currentBoundaryType = action.payload
      state.drawingPoints = []
    },
    
    addDrawingPoint: (state, action: PayloadAction<{ x: number; y: number }>) => {
      if (state.isDrawing) {
        state.drawingPoints.push(action.payload)
      }
    },
    
    updateLastDrawingPoint: (state, action: PayloadAction<{ x: number; y: number }>) => {
      if (state.isDrawing && state.drawingPoints.length > 0) {
        state.drawingPoints[state.drawingPoints.length - 1] = action.payload
      }
    },
    
    finishDrawing: (state, _action: PayloadAction<{ label: string }>) => {
      // Set the drawing state to false immediately for UI responsiveness
      // The actual boundary creation will be handled by the async thunk
      state.isDrawing = false
      state.currentBoundaryType = null
      state.drawingPoints = []
    },
    
    cancelDrawing: (state) => {
      state.isDrawing = false
      state.currentBoundaryType = null
      state.drawingPoints = []
    },
    
    deleteBoundary: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(boundary => boundary.id !== action.payload)
    },
    
    updateBoundary: (state, action: PayloadAction<{ id: string; updates: Partial<Boundary> }>) => {
      const index = state.items.findIndex(boundary => boundary.id === action.payload.id)
      if (index !== -1) {
        state.items[index] = { ...state.items[index], ...action.payload.updates }
      }
    },
    
    clearAllBoundaries: (state) => {
      state.items = []
      state.isDrawing = false
      state.currentBoundaryType = null
      state.drawingPoints = []
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch boundaries
      .addCase(fetchBoundaries.fulfilled, (state, action) => {
        const existingById = new Map(state.items.map(boundary => [boundary.id, boundary]))
        state.items = action.payload.map(response =>
          mergeWithExistingBoundary(existingById.get(response.id), response)
        )
      })
      // Create boundary
      .addCase(createBoundaryAsync.fulfilled, (state, action) => {
        state.items.push(normalizeBoundary(action.payload))
      })
      // Update boundary
      .addCase(updateBoundaryAsync.fulfilled, (state, action) => {
        const index = state.items.findIndex(boundary => boundary.id === action.payload.id)
        if (index !== -1) {
          state.items[index] = mergeWithExistingBoundary(state.items[index], action.payload)
        } else {
          state.items.push(normalizeBoundary(action.payload))
        }
      })
      // Delete boundary
      .addCase(deleteBoundaryAsync.fulfilled, (state, action) => {
        state.items = state.items.filter(boundary => boundary.id !== action.payload)
      })
  }
})

export const {
  startDrawing,
  addDrawingPoint,
  updateLastDrawingPoint,
  finishDrawing,
  cancelDrawing,
  updateBoundary,
  clearAllBoundaries
} = boundariesSlice.actions

// Async thunks are already exported above where they're defined with createAsyncThunk

export default boundariesSlice.reducer

// Selectors
export const selectBoundaries = (state: { boundaries: BoundariesState }) => state.boundaries.items
export const selectIsDrawingBoundary = (state: { boundaries: BoundariesState }) => state.boundaries.isDrawing
export const selectCurrentBoundaryType = (state: { boundaries: BoundariesState }) => state.boundaries.currentBoundaryType
export const selectDrawingPoints = (state: { boundaries: BoundariesState }) => state.boundaries.drawingPoints
