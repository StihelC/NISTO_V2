"""API routers for devices, connections, and projects."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import get_db

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
    
    # Load project devices and connections
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
    
    # Load project devices and connections
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
    
    return {"message": "Auto-save loaded successfully"}

