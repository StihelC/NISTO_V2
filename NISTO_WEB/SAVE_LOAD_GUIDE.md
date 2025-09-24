# NISTO Save/Load Functionality Guide

## Overview

The NISTO web application now includes comprehensive save/load functionality that allows users to:

1. **Save current progress** - Save the current network topology as named projects
2. **Load saved projects** - Restore previously saved network configurations
3. **Auto-save** - Automatically saves progress every 30 seconds when changes are detected
4. **Manage projects** - List, delete, and organize saved projects

## Features Implemented

### Backend Features
- **Project API Endpoints** (`/api/projects/*`)
  - `GET /api/projects` - List all saved projects
  - `POST /api/projects/save-current` - Save current state as a new project
  - `GET /api/projects/{id}` - Get a specific project
  - `POST /api/projects/{id}/load` - Load a project (replaces current state)
  - `DELETE /api/projects/{id}` - Delete a project
  - `POST /api/projects/auto-save` - Auto-save current state
  - `GET /api/projects/auto-save/load` - Load auto-saved state

- **Project Data Model**
  - Stores complete device and connection data
  - Includes metadata (name, description, timestamps)
  - Supports auto-save tracking
  - Maintains creation and update timestamps

### Frontend Features
- **Save/Load Modal Interface**
  - Clean, intuitive modal dialogs
  - Save form with name and description fields
  - Project list with metadata display
  - Auto-save loading option

- **Auto-Save Integration**
  - Monitors device and connection changes
  - Debounced saving (2-second delay after changes stop)
  - Visual indicators for auto-save status
  - Non-intrusive background operation

- **State Management**
  - Redux integration for project state
  - Error handling and user feedback
  - Real-time UI updates after loading projects

## How to Test the Save/Load Functionality

### Prerequisites
1. Backend server running on `http://localhost:8002`
2. Frontend server running on `http://localhost:5173`

### Testing Save Functionality

1. **Create some test data:**
   - Add a few devices using the "Add Device" button
   - Create connections between devices
   - Edit device properties or connection settings

2. **Save the project:**
   - Click the "Save" button in the top header
   - Enter a project name (required)
   - Optionally add a description
   - Click "Save Project"
   - You should see the modal close and the project is saved

3. **Verify save worked:**
   - Click "Load" button to see your saved project in the list
   - Check that device/connection counts are correct
   - Note the timestamp showing when it was saved

### Testing Load Functionality

1. **Create different states:**
   - Save a project with some devices (e.g., "Network A")
   - Clear/modify the current topology
   - Save another project (e.g., "Network B")

2. **Load a saved project:**
   - Click the "Load" button
   - Select a project from the list
   - Click the "Load" button next to the project
   - Verify that the current topology is replaced with the loaded project

3. **Test auto-save loading:**
   - Make some changes to devices/connections
   - Wait for auto-save to trigger (status shows in header)
   - Clear the topology manually
   - Click "Load" → "Load Auto Save"
   - Verify your recent changes are restored

### Testing Auto-Save

1. **Monitor auto-save behavior:**
   - Make changes to devices or connections
   - Watch the header for "Auto-saving..." indicator
   - See "Last saved: [time]" after auto-save completes

2. **Verify auto-save works:**
   - Create some devices
   - Wait 30+ seconds for auto-save
   - Refresh the page (this clears the current state)
   - Use "Load" → "Load Auto Save" to restore

### Testing Project Management

1. **Delete projects:**
   - Go to Load modal
   - Click "Delete" next to any saved project
   - Confirm deletion
   - Verify project is removed from list

2. **Project metadata:**
   - Check that project names and descriptions display correctly
   - Verify device/connection counts are accurate
   - Confirm timestamps update when projects are modified

## API Testing (Manual)

You can also test the backend API directly:

```bash
# Get all projects
curl http://localhost:8002/api/projects

# Save current state (requires devices/connections to exist first)
curl -X POST http://localhost:8002/api/projects/save-current \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "Test description"}'

# Auto-save current state
curl -X POST http://localhost:8002/api/projects/auto-save

# Load a project (replace {id} with actual project ID)
curl -X POST http://localhost:8002/api/projects/{id}/load
```

## Technical Architecture

### Backend
- **SQLAlchemy Models**: `Project` table with JSON storage for topology data
- **FastAPI Endpoints**: RESTful API with proper error handling
- **CRUD Operations**: Full project lifecycle management
- **Data Serialization**: Automatic conversion between API and database formats

### Frontend
- **Redux Store**: `projectsSlice` manages project state
- **React Components**: `SaveLoadModal` provides user interface
- **Custom Hook**: `useAutoSave` handles automatic saving logic
- **API Integration**: Type-safe API calls with error handling

## Troubleshooting

### Common Issues

1. **"Export not found" errors:**
   - This was fixed by ensuring proper TypeScript exports
   - Clear browser cache if issues persist

2. **Permission denied errors:**
   - Backend database file permissions were corrected
   - Frontend node_modules issues bypassed with existing servers

3. **Server not responding:**
   - Backend runs on port 8002 (changed from 8001 to avoid conflicts)
   - Frontend accessible at http://localhost:5173

4. **Auto-save not working:**
   - Check that useAutoSave hook is properly integrated
   - Verify that state changes are being detected
   - Look for error messages in browser console

### Database Location
- SQLite database: `/home/cam/Desktop/NISTO_V2/NISTO_WEB/backend/data/nisto.db`
- Tables: `devices`, `connections`, `projects`

## Future Enhancements

Potential improvements to the save/load system:
1. **Export/Import**: Allow exporting projects as files
2. **Project Templates**: Save common network patterns as templates
3. **Version History**: Track changes to projects over time
4. **Collaborative Features**: Share projects between users
5. **Backup/Restore**: Automatic backup of all projects
6. **Search/Filter**: Find projects by name, description, or content

## Summary

The save/load functionality is now fully implemented and working! Users can:
- ✅ Save their work with meaningful names and descriptions
- ✅ Load previously saved projects
- ✅ Benefit from automatic saving every 30 seconds
- ✅ Manage their project library
- ✅ Never lose their progress

The system is designed to be user-friendly, reliable, and extensible for future enhancements.
