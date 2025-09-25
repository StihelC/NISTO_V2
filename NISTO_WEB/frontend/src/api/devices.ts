import { apiClient } from './axios'

export interface DeviceFromApi {
  id: number
  name: string
  type: string
  x?: number
  y?: number
  config: Record<string, string>
}

export interface CreateDeviceRequest {
  name: string
  type: string
  x?: number
  y?: number
  config?: Record<string, string>
}

export interface UpdateDeviceRequest {
  name?: string
  type?: string
  x?: number
  y?: number
  config?: Record<string, string>
}

export const devicesApi = {
  async getDevices(): Promise<DeviceFromApi[]> {
    const response = await apiClient.get<DeviceFromApi[]>('/devices')
    return response.data
  },

  async createDevice(device: CreateDeviceRequest): Promise<DeviceFromApi> {
    const response = await apiClient.post<DeviceFromApi>('/devices', device)
    return response.data
  },

  async updateDevice(id: number, updates: UpdateDeviceRequest): Promise<DeviceFromApi> {
    const response = await apiClient.put<DeviceFromApi>(`/devices/${id}`, updates)
    return response.data
  },

  async deleteDevice(id: number): Promise<void> {
    await apiClient.delete(`/devices/${id}`)
  },
}
