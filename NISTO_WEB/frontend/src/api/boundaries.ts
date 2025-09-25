import { apiClient } from './axios'
import type { Boundary } from '../store/types'

export interface BoundaryResponse {
  id: string
  type: string
  label: string
  points: Array<{ x: number; y: number }>
  closed: boolean
  style: {
    color: string
    strokeWidth: number
    dashArray?: string
    fill?: string
    fillOpacity?: number
  }
  created: string
  // New device-like properties
  x?: number
  y?: number
  width?: number
  height?: number
  config: Record<string, string>
}

export interface CreateBoundaryRequest {
  id: string
  type: string
  label: string
  points: Array<{ x: number; y: number }>
  closed: boolean
  style: {
    color: string
    strokeWidth: number
    dashArray?: string
    fill?: string
    fillOpacity?: number
  }
  created: string
  // New device-like properties
  x?: number
  y?: number
  width?: number
  height?: number
  config?: Record<string, string>
}

export interface UpdateBoundaryRequest {
  type?: string
  label?: string
  points?: Array<{ x: number; y: number }>
  closed?: boolean
  style?: {
    color?: string
    strokeWidth?: number
    dashArray?: string
    fill?: string
    fillOpacity?: number
  }
  // New device-like properties
  x?: number
  y?: number
  width?: number
  height?: number
  config?: Record<string, string>
}

export const boundariesApi = {
  // Get all boundaries
  async getBoundaries(): Promise<BoundaryResponse[]> {
    const response = await apiClient.get<BoundaryResponse[]>('/boundaries')
    return response.data
  },

  // Get a specific boundary
  async getBoundary(id: string): Promise<BoundaryResponse> {
    const response = await apiClient.get<BoundaryResponse>(`/boundaries/${id}`)
    return response.data
  },

  // Create a new boundary
  async createBoundary(boundary: CreateBoundaryRequest): Promise<BoundaryResponse> {
    const response = await apiClient.post<BoundaryResponse>('/boundaries', boundary)
    return response.data
  },

  // Update a boundary
  async updateBoundary(id: string, updates: UpdateBoundaryRequest): Promise<BoundaryResponse> {
    const response = await apiClient.put<BoundaryResponse>(`/boundaries/${id}`, updates)
    return response.data
  },

  // Delete a boundary
  async deleteBoundary(id: string): Promise<void> {
    await apiClient.delete(`/boundaries/${id}`)
  },
}
