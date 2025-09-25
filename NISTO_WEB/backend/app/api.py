"""API routers for devices, connections, and projects."""

from __future__ import annotations

import io
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import get_db

def _calculate_risk_score(risk_level: str, vulnerability_count: int, connection_count: int) -> str:
    """Calculate a combined risk score based on multiple factors."""
    risk_weights = {
        'Very Low': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Critical': 5, 'Unknown': 2
    }
    
    risk_weight = risk_weights.get(risk_level, 2)
    vuln_weight = min(vulnerability_count, 5)  # Cap at 5
    conn_weight = min(connection_count // 2, 3)  # 0-1 conn=0, 2-3 conn=1, 4-5 conn=2, 6+ conn=3
    
    total_score = risk_weight + vuln_weight + conn_weight
    
    if total_score <= 3:
        return 'Low'
    elif total_score <= 6:
        return 'Medium'
    elif total_score <= 9:
        return 'High'
    else:
        return 'Critical'

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/devices", response_model=List[schemas.DeviceRead])
def list_devices(db: Session = Depends(get_db)) -> List[schemas.DeviceRead]:
    return crud.get_devices(db)


@router.post(
    "/devices",
    response_model=schemas.DeviceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    return crud.create_device(db, device)


@router.get("/devices/{device_id}", response_model=schemas.DeviceRead)
def get_device(device_id: int, db: Session = Depends(get_db)):
    db_device = crud.get_device(db, device_id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return db_device


@router.put("/devices/{device_id}", response_model=schemas.DeviceRead)
def update_device(
    device_id: int,
    device_update: schemas.DeviceUpdate,
    db: Session = Depends(get_db),
):
    db_device = crud.get_device(db, device_id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return crud.update_device(db, db_device, device_update)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    db_device = crud.get_device(db, device_id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    crud.delete_device(db, db_device)


@router.get("/connections", response_model=List[schemas.ConnectionRead])
def list_connections(db: Session = Depends(get_db)) -> List[schemas.ConnectionRead]:
    return crud.get_connections(db)


@router.post(
    "/connections",
    response_model=schemas.ConnectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_connection(
    connection: schemas.ConnectionCreate, db: Session = Depends(get_db)
):
    validate_connection_payload(connection, db)
    return crud.create_connection(db, connection)


@router.get("/connections/{connection_id}", response_model=schemas.ConnectionRead)
def get_connection(connection_id: int, db: Session = Depends(get_db)):
    db_connection = crud.get_connection(db, connection_id)
    if not db_connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return db_connection


@router.put("/connections/{connection_id}", response_model=schemas.ConnectionRead)
def update_connection(
    connection_id: int,
    connection_update: schemas.ConnectionUpdate,
    db: Session = Depends(get_db),
):
    db_connection = crud.get_connection(db, connection_id)
    if not db_connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    if connection_update.source_device_id or connection_update.target_device_id:
        validate_connection_update_payload(connection_update, db)
    return crud.update_connection(db, db_connection, connection_update)


@router.delete(
    "/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_connection(connection_id: int, db: Session = Depends(get_db)):
    db_connection = crud.get_connection(db, connection_id)
    if not db_connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    crud.delete_connection(db, db_connection)


def validate_connection_payload(
    connection: schemas.ConnectionCreate, db: Session
) -> None:
    if connection.source_device_id == connection.target_device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection cannot link a device to itself",
        )

    for device_id in [connection.source_device_id, connection.target_device_id]:
        if not crud.get_device(db, device_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device {device_id} does not exist",
            )


def validate_connection_update_payload(
    connection_update: schemas.ConnectionUpdate, db: Session
) -> None:
    if (
        connection_update.source_device_id is not None
        and connection_update.target_device_id is not None
        and connection_update.source_device_id == connection_update.target_device_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection cannot link a device to itself",
        )

    for device_id in [
        connection_update.source_device_id,
        connection_update.target_device_id,
    ]:
        if device_id is not None and not crud.get_device(db, device_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device {device_id} does not exist",
            )


# Boundary endpoints -----------------------------------------------------------

@router.get("/boundaries", response_model=List[schemas.BoundaryRead])
def list_boundaries(db: Session = Depends(get_db)) -> List[schemas.BoundaryRead]:
    return crud.get_boundaries(db)


@router.post(
    "/boundaries",
    response_model=schemas.BoundaryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_boundary(boundary: schemas.BoundaryCreate, db: Session = Depends(get_db)):
    return crud.create_boundary(db, boundary)


@router.get("/boundaries/{boundary_id}", response_model=schemas.BoundaryRead)
def get_boundary(boundary_id: str, db: Session = Depends(get_db)):
    db_boundary = crud.get_boundary(db, boundary_id)
    if not db_boundary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boundary not found")
    return db_boundary


@router.put("/boundaries/{boundary_id}", response_model=schemas.BoundaryRead)
def update_boundary(
    boundary_id: str,
    boundary_update: schemas.BoundaryUpdate,
    db: Session = Depends(get_db),
):
    db_boundary = crud.get_boundary(db, boundary_id)
    if not db_boundary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boundary not found")
    return crud.update_boundary(db, db_boundary, boundary_update)


@router.delete("/boundaries/{boundary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_boundary(boundary_id: str, db: Session = Depends(get_db)):
    db_boundary = crud.get_boundary(db, boundary_id)
    if not db_boundary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boundary not found")
    crud.delete_boundary(db, db_boundary)


# Project endpoints ------------------------------------------------------------

@router.get("/projects", response_model=List[schemas.ProjectSummary])
def list_projects(db: Session = Depends(get_db)) -> List[schemas.ProjectSummary]:
    return crud.get_projects(db)


@router.post(
    "/projects",
    response_model=schemas.ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db, project)


@router.get("/projects/{project_id}", response_model=schemas.ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return db_project


@router.put("/projects/{project_id}", response_model=schemas.ProjectRead)
def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return crud.update_project(db, db_project, project_update)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    crud.delete_project(db, db_project)


@router.post("/projects/save-current", response_model=schemas.ProjectRead)
def save_current_state(
    project_create: schemas.ProjectBase, db: Session = Depends(get_db)
):
    """Save the current devices and connections as a new project."""
    current_state = crud.get_current_state(db)
    project = schemas.ProjectCreate(
        name=project_create.name,
        description=project_create.description,
        project_data=current_state,
    )
    return crud.create_project(db, project)


@router.post("/projects/{project_id}/load", status_code=status.HTTP_200_OK)
def load_project(project_id: int, db: Session = Depends(get_db)):
    """Load a project by replacing current devices and connections."""
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    
    # Clear current data
    for device in crud.get_devices(db):
        crud.delete_device(db, device)
    for boundary in crud.get_boundaries(db):
        crud.delete_boundary(db, boundary)
    
    # Load project devices, connections, and boundaries
    project_data = db_project.project_data
    device_mapping = {}  # old_id -> new_id
    
    # Create devices
    for device_data in project_data.get("devices", []):
        old_id = device_data["id"]
        device_create = schemas.DeviceCreate(
            name=device_data["name"],
            type=device_data["type"],
            x=device_data.get("x"),
            y=device_data.get("y"),
            config=device_data.get("config", {}),
        )
        new_device = crud.create_device(db, device_create)
        device_mapping[old_id] = new_device.id
    
    # Create connections
    for conn_data in project_data.get("connections", []):
        if (
            conn_data["source_device_id"] in device_mapping
            and conn_data["target_device_id"] in device_mapping
        ):
            connection_create = schemas.ConnectionCreate(
                source_device_id=device_mapping[conn_data["source_device_id"]],
                target_device_id=device_mapping[conn_data["target_device_id"]],
                link_type=conn_data["link_type"],
                properties=conn_data.get("properties", {}),
            )
            crud.create_connection(db, connection_create)
    
    # Create boundaries
    for boundary_data in project_data.get("boundaries", []):
        boundary_create = schemas.BoundaryCreate(
            id=boundary_data["id"],
            type=boundary_data["type"],
            label=boundary_data["label"],
            points=boundary_data["points"],
            closed=boundary_data.get("closed", True),
            style=boundary_data["style"],
            created=boundary_data["created"],
        )
        crud.create_boundary(db, boundary_create)
    
    return {"message": "Project loaded successfully"}


@router.post("/projects/auto-save", response_model=schemas.ProjectRead)
def auto_save(db: Session = Depends(get_db)):
    """Auto-save the current state."""
    current_state = crud.get_current_state(db)
    return crud.create_or_update_auto_save(db, current_state)


@router.get("/projects/auto-save/load", status_code=status.HTTP_200_OK)
def load_auto_save(db: Session = Depends(get_db)):
    """Load the auto-saved project."""
    auto_save = crud.get_auto_save_project(db)
    if not auto_save:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No auto-save found"
        )
    
    # Use the same logic as load_project
    # Clear current data
    for device in crud.get_devices(db):
        crud.delete_device(db, device)
    for boundary in crud.get_boundaries(db):
        crud.delete_boundary(db, boundary)
    
    # Load project devices, connections, and boundaries
    project_data = auto_save.project_data
    device_mapping = {}  # old_id -> new_id
    
    # Create devices
    for device_data in project_data.get("devices", []):
        old_id = device_data["id"]
        device_create = schemas.DeviceCreate(
            name=device_data["name"],
            type=device_data["type"],
            x=device_data.get("x"),
            y=device_data.get("y"),
            config=device_data.get("config", {}),
        )
        new_device = crud.create_device(db, device_create)
        device_mapping[old_id] = new_device.id
    
    # Create connections
    for conn_data in project_data.get("connections", []):
        if (
            conn_data["source_device_id"] in device_mapping
            and conn_data["target_device_id"] in device_mapping
        ):
            connection_create = schemas.ConnectionCreate(
                source_device_id=device_mapping[conn_data["source_device_id"]],
                target_device_id=device_mapping[conn_data["target_device_id"]],
                link_type=conn_data["link_type"],
                properties=conn_data.get("properties", {}),
            )
            crud.create_connection(db, connection_create)
    
    # Create boundaries
    for boundary_data in project_data.get("boundaries", []):
        boundary_create = schemas.BoundaryCreate(
            id=boundary_data["id"],
            type=boundary_data["type"],
            label=boundary_data["label"],
            points=boundary_data["points"],
            closed=boundary_data.get("closed", True),
            style=boundary_data["style"],
            created=boundary_data["created"],
        )
        crud.create_boundary(db, boundary_create)
    
    return {"message": "Auto-save loaded successfully"}


# Export endpoints -------------------------------------------------------------

@router.get("/export/csv")
def export_topology_csv(db: Session = Depends(get_db)):
    """Export topology data as CSV with devices and connections."""
    devices = crud.get_devices(db)
    connections = crud.get_connections(db)
    
    # Debug logging
    print(f"DEBUG: Found {len(devices)} devices and {len(connections)} connections")
    print("DEBUG: Using ENHANCED export with connectivity and RMF data!")
    
    # Build connectivity mappings
    device_connections = {}  # device_id -> {'incoming': [], 'outgoing': []}
    for connection in connections:
        # Outgoing connections (device is source)
        if connection.source_device_id not in device_connections:
            device_connections[connection.source_device_id] = {'incoming': [], 'outgoing': []}
        device_connections[connection.source_device_id]['outgoing'].append({
            'target_id': connection.target_device_id,
            'target_name': connection.target_device.name if connection.target_device else f'Device_{connection.target_device_id}',
            'link_type': connection.link_type,
            'properties': connection.properties or {}
        })
        
        # Incoming connections (device is target)
        if connection.target_device_id not in device_connections:
            device_connections[connection.target_device_id] = {'incoming': [], 'outgoing': []}
        device_connections[connection.target_device_id]['incoming'].append({
            'source_id': connection.source_device_id,
            'source_name': connection.source_device.name if connection.source_device else f'Device_{connection.source_device_id}',
            'link_type': connection.link_type,
            'properties': connection.properties or {}
        })
    
    # Prepare devices data with comprehensive property handling + connectivity + RMF
    devices_data = []
    all_device_config_keys = set()
    
    # First pass: collect all possible config keys
    for device in devices:
        if device.config:
            all_device_config_keys.update(device.config.keys())
    
    # Second pass: create device rows with all config columns + connectivity + RMF
    for device in devices:
        # Get connectivity info for this device
        conn_info = device_connections.get(device.id, {'incoming': [], 'outgoing': []})
        
        # Build connectivity strings
        connected_to_names = [conn['target_name'] for conn in conn_info['outgoing']]
        connected_to_types = [conn['link_type'] for conn in conn_info['outgoing']]
        connected_from_names = [conn['source_name'] for conn in conn_info['incoming']]
        connected_from_types = [conn['link_type'] for conn in conn_info['incoming']]
        
        # Calculate risk metrics
        total_connections = len(conn_info['incoming']) + len(conn_info['outgoing'])
        vulnerability_count = int(device.config.get('vulnerabilities', '0') if device.config else '0')
        risk_level = device.config.get('riskLevel', 'Unknown') if device.config else 'Unknown'
        compliance_status = device.config.get('complianceStatus', 'Unknown') if device.config else 'Unknown'
        
        device_row = {
            'id': device.id,
            'name': device.name,
            'type': device.type,
            'x_position': device.x if device.x is not None else '',
            'y_position': device.y if device.y is not None else '',
            
            # Connectivity Information
            'total_connections': total_connections,
            'outgoing_connections_count': len(conn_info['outgoing']),
            'incoming_connections_count': len(conn_info['incoming']),
            'connected_to_devices': '; '.join(connected_to_names) if connected_to_names else '',
            'connected_to_link_types': '; '.join(connected_to_types) if connected_to_types else '',
            'connected_from_devices': '; '.join(connected_from_names) if connected_from_names else '',
            'connected_from_link_types': '; '.join(connected_from_types) if connected_from_types else '',
            
            # RMF and Security Information
            'rmf_risk_level': risk_level,
            'rmf_vulnerability_count': vulnerability_count,
            'rmf_compliance_status': compliance_status,
            'rmf_monitoring_enabled': device.config.get('monitoringEnabled', 'Unknown') if device.config else 'Unknown',
            'rmf_department': device.config.get('department', 'Unknown') if device.config else 'Unknown',
            
            # Risk Assessment
            'connectivity_risk_factor': 'High' if total_connections > 3 else 'Medium' if total_connections > 1 else 'Low',
            'combined_risk_score': _calculate_risk_score(risk_level, vulnerability_count, total_connections),
        }
        
        # Add all possible config properties as individual columns (detailed properties)
        for key in sorted(all_device_config_keys):
            # Convert camelCase to Title Case for user-friendly column names
            friendly_key = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title()
            device_row[friendly_key] = device.config.get(key, '') if device.config else ''
            
        devices_data.append(device_row)
    
    # Prepare connections data with comprehensive property handling
    connections_data = []
    all_connection_property_keys = set()
    
    # First pass: collect all possible property keys
    for connection in connections:
        if connection.properties:
            all_connection_property_keys.update(connection.properties.keys())
    
    # Second pass: create connection rows with all property columns
    for connection in connections:
        connection_row = {
            'id': connection.id,
            'source_device_id': connection.source_device_id,
            'target_device_id': connection.target_device_id,
            'source_device_name': connection.source_device.name if connection.source_device else '',
            'target_device_name': connection.target_device.name if connection.target_device else '',
            'link_type': connection.link_type,
        }
        
        # Add all possible connection properties as individual columns
        for key in sorted(all_connection_property_keys):
            connection_row[f'property_{key}'] = connection.properties.get(key, '') if connection.properties else ''
            
        connections_data.append(connection_row)
    
    # Create pandas DataFrames
    devices_df = pd.DataFrame(devices_data)
    connections_df = pd.DataFrame(connections_data)
    
    # Create a CSV buffer
    output = io.StringIO()
    
    # Write export metadata
    from datetime import datetime
    output.write(f"# NISTO Topology Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write(f"# Total Devices: {len(devices_data)}\n")
    output.write(f"# Total Connections: {len(connections_data)}\n")
    output.write(f"# Device Config Properties: {', '.join(sorted(all_device_config_keys)) if all_device_config_keys else 'None'}\n")
    output.write(f"# Connection Properties: {', '.join(sorted(all_connection_property_keys)) if all_connection_property_keys else 'None'}\n")
    output.write("\n")
    
    # Write devices section
    output.write("# DEVICES\n")
    if not devices_df.empty:
        devices_df.to_csv(output, index=False)
    else:
        output.write("No devices found\n")
    
    output.write("\n\n# CONNECTIONS\n")
    if not connections_df.empty:
        connections_df.to_csv(output, index=False)
    else:
        output.write("No connections found\n")
    
    # Get the CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Return as streaming response
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=topology_export.csv"}
    )


@router.get("/export/excel")
def export_topology_excel(db: Session = Depends(get_db)):
    """Export topology data as Excel with separate sheets for devices and connections."""
    devices = crud.get_devices(db)
    connections = crud.get_connections(db)
    
    # Debug logging
    print(f"DEBUG: Found {len(devices)} devices and {len(connections)} connections for Excel export")
    
    # Build connectivity mappings (same as CSV export)
    device_connections = {}  # device_id -> {'incoming': [], 'outgoing': []}
    for connection in connections:
        # Outgoing connections (device is source)
        if connection.source_device_id not in device_connections:
            device_connections[connection.source_device_id] = {'incoming': [], 'outgoing': []}
        device_connections[connection.source_device_id]['outgoing'].append({
            'target_id': connection.target_device_id,
            'target_name': connection.target_device.name if connection.target_device else f'Device_{connection.target_device_id}',
            'link_type': connection.link_type,
            'properties': connection.properties or {}
        })
        
        # Incoming connections (device is target)
        if connection.target_device_id not in device_connections:
            device_connections[connection.target_device_id] = {'incoming': [], 'outgoing': []}
        device_connections[connection.target_device_id]['incoming'].append({
            'source_id': connection.source_device_id,
            'source_name': connection.source_device.name if connection.source_device else f'Device_{connection.source_device_id}',
            'link_type': connection.link_type,
            'properties': connection.properties or {}
        })
    
    # Prepare devices data with comprehensive property handling + connectivity + RMF
    devices_data = []
    all_device_config_keys = set()
    
    # First pass: collect all possible config keys
    for device in devices:
        if device.config:
            all_device_config_keys.update(device.config.keys())
    
    # Second pass: create device rows with all config columns + connectivity + RMF
    for device in devices:
        # Get connectivity info for this device
        conn_info = device_connections.get(device.id, {'incoming': [], 'outgoing': []})
        
        # Build connectivity strings
        connected_to_names = [conn['target_name'] for conn in conn_info['outgoing']]
        connected_to_types = [conn['link_type'] for conn in conn_info['outgoing']]
        connected_from_names = [conn['source_name'] for conn in conn_info['incoming']]
        connected_from_types = [conn['link_type'] for conn in conn_info['incoming']]
        
        # Calculate risk metrics
        total_connections = len(conn_info['incoming']) + len(conn_info['outgoing'])
        vulnerability_count = int(device.config.get('vulnerabilities', '0') if device.config else '0')
        risk_level = device.config.get('riskLevel', 'Unknown') if device.config else 'Unknown'
        compliance_status = device.config.get('complianceStatus', 'Unknown') if device.config else 'Unknown'
        
        device_row = {
            'ID': device.id,
            'Name': device.name,
            'Type': device.type,
            'X Position': device.x if device.x is not None else '',
            'Y Position': device.y if device.y is not None else '',
            
            # Connectivity Information  
            'Total Connections': total_connections,
            'Outgoing Connections': len(conn_info['outgoing']),
            'Incoming Connections': len(conn_info['incoming']),
            'Connected To Devices': '; '.join(connected_to_names) if connected_to_names else '',
            'Connected To Link Types': '; '.join(connected_to_types) if connected_to_types else '',
            'Connected From Devices': '; '.join(connected_from_names) if connected_from_names else '',
            'Connected From Link Types': '; '.join(connected_from_types) if connected_from_types else '',
            
            # RMF and Security Information
            'RMF Risk Level': risk_level,
            'RMF Vulnerability Count': vulnerability_count,
            'RMF Compliance Status': compliance_status,
            'RMF Monitoring Enabled': device.config.get('monitoringEnabled', 'Unknown') if device.config else 'Unknown',
            'RMF Department': device.config.get('department', 'Unknown') if device.config else 'Unknown',
            
            # Risk Assessment
            'Connectivity Risk Factor': 'High' if total_connections > 3 else 'Medium' if total_connections > 1 else 'Low',
            'Combined Risk Score': _calculate_risk_score(risk_level, vulnerability_count, total_connections),
        }
        
        # Add all possible config properties as individual columns (detailed properties)
        for key in sorted(all_device_config_keys):
            # Convert camelCase to Title Case for user-friendly column names
            friendly_key = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title()
            device_row[friendly_key] = device.config.get(key, '') if device.config else ''
            
        devices_data.append(device_row)
    
    # Prepare connections data with comprehensive property handling
    connections_data = []
    all_connection_property_keys = set()
    
    # First pass: collect all possible property keys
    for connection in connections:
        if connection.properties:
            all_connection_property_keys.update(connection.properties.keys())
    
    # Second pass: create connection rows with all property columns  
    for connection in connections:
        connection_row = {
            'ID': connection.id,
            'Source Device ID': connection.source_device_id,
            'Target Device ID': connection.target_device_id,
            'Source Device Name': connection.source_device.name if connection.source_device else '',
            'Target Device Name': connection.target_device.name if connection.target_device else '',
            'Link Type': connection.link_type,
        }
        
        # Add all possible connection properties as individual columns
        for key in sorted(all_connection_property_keys):
            connection_row[f'Property: {key}'] = connection.properties.get(key, '') if connection.properties else ''
            
        connections_data.append(connection_row)
    
    # Create pandas DataFrames
    devices_df = pd.DataFrame(devices_data)
    connections_df = pd.DataFrame(connections_data)
    
    # Create Excel buffer
    output = io.BytesIO()
    
    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not devices_df.empty:
            devices_df.to_excel(writer, sheet_name='Devices', index=False)
        else:
            pd.DataFrame([{"Message": "No devices found"}]).to_excel(writer, sheet_name='Devices', index=False)
        
        if not connections_df.empty:
            connections_df.to_excel(writer, sheet_name='Connections', index=False)
        else:
            pd.DataFrame([{"Message": "No connections found"}]).to_excel(writer, sheet_name='Connections', index=False)
        
        # Add a summary sheet
        from datetime import datetime
        summary_data = {
            'Metric': ['Total Devices', 'Total Connections', 'Export Date'],
            'Value': [len(devices), len(connections), datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Reset buffer position
    output.seek(0)
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=topology_export.xlsx"}
    )


@router.get("/export/debug")
def debug_topology_data(db: Session = Depends(get_db)):
    """Debug endpoint to inspect topology data structure."""
    devices = crud.get_devices(db)
    connections = crud.get_connections(db)
    
    debug_info = {
        "devices_count": len(devices),
        "connections_count": len(connections),
        "devices": [],
        "connections": [],
    }
    
    # Add device details
    for device in devices:
        device_info = {
            "id": device.id,
            "name": device.name,
            "type": device.type,
            "x": device.x,
            "y": device.y,
            "config": device.config,
            "config_keys": list(device.config.keys()) if device.config else [],
        }
        debug_info["devices"].append(device_info)
    
    # Add connection details  
    for connection in connections:
        connection_info = {
            "id": connection.id,
            "source_device_id": connection.source_device_id,
            "target_device_id": connection.target_device_id,
            "link_type": connection.link_type,
            "properties": connection.properties,
            "property_keys": list(connection.properties.keys()) if connection.properties else [],
            "source_device_name": connection.source_device.name if connection.source_device else None,
            "target_device_name": connection.target_device.name if connection.target_device else None,
        }
        debug_info["connections"].append(connection_info)
    
    return debug_info


@router.get("/export/enhanced-csv")  
def export_enhanced_topology_csv(db: Session = Depends(get_db)):
    """Export topology data as CSV with enhanced connectivity and RMF data in device rows."""
    devices = crud.get_devices(db)
    connections = crud.get_connections(db)
    
    print(f"ENHANCED DEBUG: Found {len(devices)} devices and {len(connections)} connections")
    
    # Build connectivity mappings
    device_connections = {}
    for connection in connections:
        # Track outgoing connections  
        if connection.source_device_id not in device_connections:
            device_connections[connection.source_device_id] = {'incoming': [], 'outgoing': []}
        device_connections[connection.source_device_id]['outgoing'].append({
            'target_name': connection.target_device.name if connection.target_device else f'Device_{connection.target_device_id}',
            'link_type': connection.link_type
        })
        
        # Track incoming connections
        if connection.target_device_id not in device_connections:
            device_connections[connection.target_device_id] = {'incoming': [], 'outgoing': []}
        device_connections[connection.target_device_id]['incoming'].append({
            'source_name': connection.source_device.name if connection.source_device else f'Device_{connection.source_device_id}',
            'link_type': connection.link_type
        })
    
    # Build enhanced device data
    devices_data = []
    for device in devices:
        conn_info = device_connections.get(device.id, {'incoming': [], 'outgoing': []})
        
        connected_to = '; '.join([c['target_name'] for c in conn_info['outgoing']]) if conn_info['outgoing'] else ''
        connected_from = '; '.join([c['source_name'] for c in conn_info['incoming']]) if conn_info['incoming'] else ''
        total_connections = len(conn_info['incoming']) + len(conn_info['outgoing'])
        
        # Get RMF data from config
        risk_level = device.config.get('riskLevel', 'Unknown') if device.config else 'Unknown'
        vulnerability_count = int(device.config.get('vulnerabilities', '0') if device.config else '0')
        compliance_status = device.config.get('complianceStatus', 'Unknown') if device.config else 'Unknown'
        department = device.config.get('department', 'Unknown') if device.config else 'Unknown'
        monitoring = device.config.get('monitoringEnabled', 'Unknown') if device.config else 'Unknown'
        
        risk_score = _calculate_risk_score(risk_level, vulnerability_count, total_connections)
        
        device_row = {
            'ID': device.id,
            'Device Name': device.name,
            'Device Type': device.type,
            'X Coordinate': device.x if device.x is not None else '',
            'Y Coordinate': device.y if device.y is not None else '',
            'Total Connections': total_connections,
            'Connected To': connected_to,
            'Connected From': connected_from,
            'Risk Level': risk_level,
            'Vulnerability Count': vulnerability_count,
            'Compliance Status': compliance_status,
            'Department': department,
            'Monitoring Enabled': monitoring,
            'Overall Risk Score': risk_score,
            'Network Risk Level': 'High' if total_connections > 3 else 'Medium' if total_connections > 1 else 'Low'
        }
        devices_data.append(device_row)
    
    # Create CSV
    devices_df = pd.DataFrame(devices_data)
    
    output = io.StringIO()
    output.write(f"# Enhanced NISTO Topology Export - Device-Centric with Connectivity & RMF Data\n")
    output.write(f"# Generated: {pd.Timestamp.now()}\n")
    output.write(f"# Total Devices: {len(devices_data)}\n")
    output.write(f"# Total Connections: {len(connections)}\n")
    output.write("\n")
    
    devices_df.to_csv(output, index=False)
    csv_content = output.getvalue()
    output.close()
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=enhanced_topology_export.csv"}
    )

