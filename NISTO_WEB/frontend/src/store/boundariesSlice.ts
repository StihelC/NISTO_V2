import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import type { Boundary, BoundaryType, BoundariesState } from './types'
import { boundariesApi } from '../api/boundaries'

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
    return boundaries.map(boundary => ({
      id: boundary.id,
      type: boundary.type as BoundaryType,
      label: boundary.label,
      points: boundary.points,
      closed: boundary.closed,
      style: boundary.style,
      created: boundary.created,
      position: boundary.x && boundary.y ? {
        x: boundary.x,
        y: boundary.y,
        width: boundary.width || 200,
        height: boundary.height || 200
      } : undefined,
      x: boundary.x,
      y: boundary.y,
      width: boundary.width,
      height: boundary.height,
      config: boundary.config || {}
    }))
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
      x: boundary.position?.x || boundary.x,
      y: boundary.position?.y || boundary.y,
      width: boundary.position?.width || boundary.width,
      height: boundary.position?.height || boundary.height,
      config: boundary.config || {}
    })
    return {
      id: created.id,
      type: created.type as BoundaryType,
      label: created.label,
      points: created.points,
      closed: created.closed,
      style: created.style,
      created: created.created,
      position: created.x && created.y ? {
        x: created.x,
        y: created.y,
        width: created.width || 200,
        height: created.height || 200
      } : undefined,
      x: created.x,
      y: created.y,
      width: created.width,
      height: created.height,
      config: created.config || {}
    }
  }
)

export const updateBoundaryAsync = createAsyncThunk(
  'boundaries/updateBoundary',
  async ({ id, updates }: { id: string; updates: Partial<Boundary> }) => {
    const updated = await boundariesApi.updateBoundary(id, updates)
    return {
      id: updated.id,
      type: updated.type as BoundaryType,
      label: updated.label,
      points: updated.points,
      closed: updated.closed,
      style: updated.style,
      created: updated.created,
      position: updated.x && updated.y ? {
        x: updated.x,
        y: updated.y,
        width: updated.width || 200,
        height: updated.height || 200
      } : undefined,
      x: updated.x,
      y: updated.y,
      width: updated.width,
      height: updated.height,
      config: updated.config || {}
    }
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
    
    finishDrawing: (state, action: PayloadAction<{ label: string }>) => {
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
        state.items = action.payload
      })
      // Create boundary
      .addCase(createBoundaryAsync.fulfilled, (state, action) => {
        state.items.push(action.payload)
      })
      // Update boundary
      .addCase(updateBoundaryAsync.fulfilled, (state, action) => {
        const index = state.items.findIndex(boundary => boundary.id === action.payload.id)
        if (index !== -1) {
          state.items[index] = action.payload
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
