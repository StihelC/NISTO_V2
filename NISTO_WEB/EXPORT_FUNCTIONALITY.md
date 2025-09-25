# Topology Export Functionality

This document describes the newly implemented export functionality for the NISTO topology application.

## Features Implemented

### 📊 Data Export
- **CSV Export**: Exports all devices and connections with positions and properties in CSV format
- **Excel Export**: Creates an Excel file with separate sheets for devices, connections, and a summary

### 🖼️ Image Export  
- **PNG Export**: Exports the visual topology as a high-quality PNG image
- **SVG Export**: Exports the topology as a scalable SVG file

## How to Use

### 1. Access Export Functionality
- Look for the export button (📤) in the topology view header (next to zoom controls)
- Click the export button to open the export modal

### 2. Data Exports
The CSV and Excel exports include:

**Device Data:**
- ID, Name, Type
- X and Y positions on the canvas
- All configuration properties (risk level, compliance status, vulnerabilities, etc.)

**Connection Data:**
- ID, Source and Target device IDs and names
- Link type (ethernet, fiber, etc.)
- All connection properties

**Excel Format:**
- **Devices Sheet**: All device information
- **Connections Sheet**: All connection information  
- **Summary Sheet**: Total counts and export timestamp

### 3. Image Exports
- **PNG**: Perfect for documentation, presentations, or sharing
- **SVG**: Vector format that scales without quality loss, ideal for printing

## Technical Implementation

### Backend (FastAPI + Pandas)
- `/api/export/csv` - Returns CSV file with topology data
- `/api/export/excel` - Returns Excel file with multiple sheets
- Uses pandas DataFrames for data processing
- Streams files as downloadable responses

### Frontend (React + TypeScript)
- Export modal component with intuitive UI
- Canvas-to-image conversion for visual exports
- File download handling with proper filenames
- Error handling and user feedback

## File Formats

### CSV Export
```
# DEVICES
id,name,type,x_position,y_position,config_riskLevel,config_vulnerabilities,...
1,Router-1,router,200.5,150.0,Moderate,2,...

# CONNECTIONS  
id,source_device_id,target_device_id,source_device_name,target_device_name,link_type,...
1,1,2,Router-1,Switch-1,ethernet,...
```

### Excel Export
- **Devices** sheet with formatted headers
- **Connections** sheet with device name lookups
- **Summary** sheet with metrics and export date

## Benefits

1. **Data Analysis**: Export topology data to Excel for advanced analysis and reporting
2. **Documentation**: Generate images for network documentation and presentations  
3. **Backup**: Create data exports as backups of your topology configurations
4. **Integration**: Import CSV data into other network management tools
5. **Sharing**: Share visual representations with stakeholders

## Future Enhancements

Possible future improvements:
- PDF export with formatted reports
- JSON export for API integrations
- Scheduled exports
- Export filtering and customization
- Bulk export of multiple projects

## Example Use Cases

1. **Network Audit**: Export device list with security configurations to Excel for compliance review
2. **Presentation**: Export PNG images for including in project proposals or documentation
3. **Backup**: Regular CSV exports to maintain data backups outside the application
4. **Analysis**: Export connection data to analyze network topology patterns
5. **Documentation**: Generate SVG diagrams for technical documentation that scales to any size
