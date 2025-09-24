import { apiClient } from './axios'

export interface DeviceFromApi {
  id: number
  name: string
  type: string
  x?: number
  y?: number
  config: Record<string, string>
}

export const devicesApi = {
  async getDevices(): Promise<DeviceFromApi[]> {
    const response = await apiClient.get<DeviceFromApi[]>('/devices')
    return response.data
  },
}
