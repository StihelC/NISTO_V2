import { apiClient } from './axios'

export interface ProjectSummary {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
  is_auto_save: boolean
  device_count: number
  connection_count: number
}

export interface ProjectData {
  devices: any[]
  connections: any[]
  ui_state?: any
}

export interface Project {
  id: number
  name: string
  description?: string
  project_data: ProjectData
  created_at: string
  updated_at: string
  is_auto_save: boolean
}

export interface CreateProjectRequest {
  name: string
  description?: string
}

export interface SaveCurrentRequest {
  name: string
  description?: string
}

export const projectsApi = {
  // Get all projects
  async getProjects(): Promise<ProjectSummary[]> {
    const response = await apiClient.get<ProjectSummary[]>('/projects')
    return response.data
  },

  // Get a specific project
  async getProject(id: number): Promise<Project> {
    const response = await apiClient.get<Project>(`/projects/${id}`)
    return response.data
  },

  // Save current state as a new project
  async saveCurrent(data: SaveCurrentRequest): Promise<Project> {
    const response = await apiClient.post<Project>('/projects/save-current', data)
    return response.data
  },

  // Load a project (replaces current state)
  async loadProject(id: number): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(`/projects/${id}/load`)
    return response.data
  },

  // Delete a project
  async deleteProject(id: number): Promise<void> {
    await apiClient.delete(`/projects/${id}`)
  },

  // Auto-save current state
  async autoSave(): Promise<Project> {
    const response = await apiClient.post<Project>('/projects/auto-save')
    return response.data
  },

  // Load auto-saved project
  async loadAutoSave(): Promise<{ message: string }> {
    const response = await apiClient.get<{ message: string }>('/projects/auto-save/load')
    return response.data
  },
}
