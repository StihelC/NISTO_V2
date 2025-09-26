import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  fetchProjects,
  saveCurrentAsProject,
  loadProject,
  deleteProject,
  loadAutoSave,
  clearError,
  fetchDevices,
  fetchConnections,
  type AppDispatch,
  type RootState,
} from '../store'

interface SaveLoadModalProps {
  isOpen: boolean
  onClose: () => void
  mode: 'save' | 'load'
}

export const SaveLoadModal: React.FC<SaveLoadModalProps> = ({
  isOpen,
  onClose,
  mode,
}) => {
  const dispatch = useDispatch<AppDispatch>()
  const { projects, isLoading, error } = useSelector(
    (state: RootState) => state.projects
  )
  
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)

  useEffect(() => {
    if (isOpen) {
      dispatch(fetchProjects())
      setProjectName('')
      setProjectDescription('')
      setSelectedProjectId(null)
    }
  }, [isOpen, dispatch])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        dispatch(clearError())
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, dispatch])

  const handleSave = async () => {
    if (!projectName.trim()) return

    try {
      await dispatch(saveCurrentAsProject({
        name: projectName.trim(),
        description: projectDescription.trim() || undefined,
      })).unwrap()
      onClose()
    } catch (error) {
      // Error handled by Redux
    }
  }

  const handleLoad = async (projectId: number) => {
    try {
      await dispatch(loadProject(projectId)).unwrap()
      // Refresh the frontend state
      await Promise.all([
        dispatch(fetchDevices()),
        dispatch(fetchConnections())
      ])
      onClose()
    } catch (error) {
      // Error handled by Redux
    }
  }

  const handleLoadAutoSave = async () => {
    try {
      await dispatch(loadAutoSave()).unwrap()
      // Refresh the frontend state
      await Promise.all([
        dispatch(fetchDevices()),
        dispatch(fetchConnections())
      ])
      onClose()
    } catch (error) {
      // Error handled by Redux
    }
  }

  const handleDelete = async (projectId: number, event: React.MouseEvent) => {
    event.stopPropagation()
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await dispatch(deleteProject(projectId)).unwrap()
      } catch (error) {
        // Error handled by Redux
      }
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{mode === 'save' ? 'Save Project' : 'Load Project'}</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="modal-body">
          {mode === 'save' ? (
            <div className="save-form">
              <div className="form-group">
                <label htmlFor="projectName">Project Name *</label>
                <input
                  id="projectName"
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                  maxLength={100}
                />
              </div>
              <div className="form-group">
                <label htmlFor="projectDescription">Description</label>
                <textarea
                  id="projectDescription"
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="Optional description"
                  rows={3}
                  maxLength={500}
                />
              </div>
              <div className="form-actions">
                <button
                  className="btn btn-primary"
                  onClick={handleSave}
                  disabled={!projectName.trim() || isLoading}
                >
                  {isLoading ? 'Saving...' : 'Save Project'}
                </button>
                <button className="btn btn-secondary" onClick={onClose}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="load-projects">
              {/* Auto-save section */}
              <div className="auto-save-section">
                <h3>Auto Save</h3>
                <button
                  className="btn btn-auto-save"
                  onClick={handleLoadAutoSave}
                  disabled={isLoading}
                >
                  {isLoading ? 'Loading...' : 'Load Auto Save'}
                </button>
                <p className="auto-save-note">
                  Load the last automatically saved state
                </p>
              </div>

              <hr />

              {/* Saved projects */}
              <div className="projects-section">
                <h3>Saved Projects</h3>
                {isLoading && projects.length === 0 ? (
                  <div className="loading">Loading projects...</div>
                ) : projects.length === 0 ? (
                  <div className="no-projects">No saved projects found</div>
                ) : (
                  <div className="projects-list">
                    {projects
                      .filter(p => !p.is_auto_save)
                      .map((project) => (
                        <div
                          key={project.id}
                          className={`project-item ${
                            selectedProjectId === project.id ? 'selected' : ''
                          }`}
                          onClick={() => setSelectedProjectId(project.id)}
                        >
                          <div className="project-info">
                            <h4>{project.name}</h4>
                            {project.description && (
                              <p className="project-description">
                                {project.description}
                              </p>
                            )}
                            <div className="project-meta">
                              <span>{project.device_count} devices</span>
                              <span>{project.connection_count} connections</span>
                              <span>Updated: {formatDate(project.updated_at)}</span>
                            </div>
                          </div>
                          <div className="project-actions">
                            <button
                              className="btn btn-small btn-primary"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleLoad(project.id)
                              }}
                              disabled={isLoading}
                            >
                              Load
                            </button>
                            <button
                              className="btn btn-small btn-danger"
                              onClick={(e) => handleDelete(project.id, e)}
                              disabled={isLoading}
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))
                    }
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
