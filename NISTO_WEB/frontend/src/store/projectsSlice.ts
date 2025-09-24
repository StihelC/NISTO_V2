import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { projectsApi } from '../api/projects'
import type { Project, ProjectSummary } from '../api/projects'

export interface ProjectsState {
  projects: ProjectSummary[]
  currentProject: Project | null
  isLoading: boolean
  error: string | null
  autoSaving: boolean
  lastAutoSave: string | null
}

const initialState: ProjectsState = {
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,
  autoSaving: false,
  lastAutoSave: null,
}

// Async thunks
export const fetchProjects = createAsyncThunk(
  'projects/fetchProjects',
  async (_, { rejectWithValue }) => {
    try {
      return await projectsApi.getProjects()
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch projects')
    }
  }
)

export const saveCurrentAsProject = createAsyncThunk(
  'projects/saveCurrent',
  async (data: { name: string; description?: string }, { rejectWithValue }) => {
    try {
      return await projectsApi.saveCurrent(data)
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to save project')
    }
  }
)

export const loadProject = createAsyncThunk(
  'projects/loadProject',
  async (id: number, { rejectWithValue }) => {
    try {
      await projectsApi.loadProject(id)
      const project = await projectsApi.getProject(id)
      return project
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to load project')
    }
  }
)

export const deleteProject = createAsyncThunk(
  'projects/deleteProject',
  async (id: number, { rejectWithValue }) => {
    try {
      await projectsApi.deleteProject(id)
      return id
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete project')
    }
  }
)

export const autoSaveProject = createAsyncThunk(
  'projects/autoSave',
  async (_, { rejectWithValue }) => {
    try {
      return await projectsApi.autoSave()
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to auto-save')
    }
  }
)

export const loadAutoSave = createAsyncThunk(
  'projects/loadAutoSave',
  async (_, { rejectWithValue }) => {
    try {
      await projectsApi.loadAutoSave()
      return 'Auto-save loaded successfully'
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to load auto-save')
    }
  }
)

const projectsSlice = createSlice({
  name: 'projects',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setCurrentProject: (state, action) => {
      state.currentProject = action.payload
    },
    clearCurrentProject: (state) => {
      state.currentProject = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch projects
      .addCase(fetchProjects.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.isLoading = false
        state.projects = action.payload
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

      // Save current as project
      .addCase(saveCurrentAsProject.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(saveCurrentAsProject.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentProject = action.payload
        // Refresh projects list
        state.projects.unshift({
          id: action.payload.id,
          name: action.payload.name,
          description: action.payload.description,
          created_at: action.payload.created_at,
          updated_at: action.payload.updated_at,
          is_auto_save: action.payload.is_auto_save,
          device_count: action.payload.project_data.devices.length,
          connection_count: action.payload.project_data.connections.length,
        })
      })
      .addCase(saveCurrentAsProject.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

      // Load project
      .addCase(loadProject.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loadProject.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentProject = action.payload
      })
      .addCase(loadProject.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

      // Delete project
      .addCase(deleteProject.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(deleteProject.fulfilled, (state, action) => {
        state.isLoading = false
        state.projects = state.projects.filter(p => p.id !== action.payload)
        if (state.currentProject?.id === action.payload) {
          state.currentProject = null
        }
      })
      .addCase(deleteProject.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

      // Auto-save
      .addCase(autoSaveProject.pending, (state) => {
        state.autoSaving = true
      })
      .addCase(autoSaveProject.fulfilled, (state, action) => {
        state.autoSaving = false
        state.lastAutoSave = new Date().toISOString()
        // Update or add auto-save project in list
        const existingIndex = state.projects.findIndex(p => p.is_auto_save)
        const autoSaveProject = {
          id: action.payload.id,
          name: action.payload.name,
          description: action.payload.description,
          created_at: action.payload.created_at,
          updated_at: action.payload.updated_at,
          is_auto_save: action.payload.is_auto_save,
          device_count: action.payload.project_data.devices.length,
          connection_count: action.payload.project_data.connections.length,
        }
        if (existingIndex >= 0) {
          state.projects[existingIndex] = autoSaveProject
        } else {
          state.projects.push(autoSaveProject)
        }
      })
      .addCase(autoSaveProject.rejected, (state, action) => {
        state.autoSaving = false
        state.error = action.payload as string
      })

      // Load auto-save
      .addCase(loadAutoSave.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loadAutoSave.fulfilled, (state) => {
        state.isLoading = false
        state.currentProject = null // Clear current project since we loaded from auto-save
      })
      .addCase(loadAutoSave.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, setCurrentProject, clearCurrentProject } = projectsSlice.actions
export default projectsSlice.reducer
