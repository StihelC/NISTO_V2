import { apiClient } from './axios'

export interface ConnectionFromApi {
  id: number
  source_device_id: number
  target_device_id: number
  link_type: string
  properties: Record<string, string>
}

export const connectionsApi = {
  async getConnections(): Promise<ConnectionFromApi[]> {
    const response = await apiClient.get<ConnectionFromApi[]>('/connections')
    return response.data
  },
}
