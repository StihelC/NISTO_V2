import { apiClient } from './axios'

export interface ConnectionFromApi {
  id: number
  source_device_id: number
  target_device_id: number
  link_type: string
  properties: Record<string, string>
}

export interface CreateConnectionRequest {
  source_device_id: number
  target_device_id: number
  link_type: string
  properties?: Record<string, string>
}

export interface UpdateConnectionRequest {
  source_device_id?: number
  target_device_id?: number
  link_type?: string
  properties?: Record<string, string>
}

export const connectionsApi = {
  async getConnections(): Promise<ConnectionFromApi[]> {
    const response = await apiClient.get<ConnectionFromApi[]>('/connections')
    return response.data
  },

  async createConnection(payload: CreateConnectionRequest): Promise<ConnectionFromApi> {
    const response = await apiClient.post<ConnectionFromApi>('/connections', payload)
    return response.data
  },

  async updateConnection(id: number, updates: UpdateConnectionRequest): Promise<ConnectionFromApi> {
    const response = await apiClient.put<ConnectionFromApi>(`/connections/${id}`, updates)
    return response.data
  },

  async deleteConnection(id: number): Promise<void> {
    await apiClient.delete(`/connections/${id}`)
  },
}
