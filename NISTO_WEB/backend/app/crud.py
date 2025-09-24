"""CRUD utilities for devices, connections, and projects."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


# Device CRUD -----------------------------------------------------------------

def get_devices(db: Session) -> List[models.Device]:
    return db.query(models.Device).order_by(models.Device.id).all()


def get_device(db: Session, device_id: int) -> Optional[models.Device]:
    return db.query(models.Device).filter(models.Device.id == device_id).first()


def create_device(db: Session, device: schemas.DeviceCreate) -> models.Device:
    db_device = models.Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(
    db: Session, db_device: models.Device, device_update: schemas.DeviceUpdate
) -> models.Device:
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_device, field, value)
    db.commit()
    db.refresh(db_device)
    return db_device


def delete_device(db: Session, db_device: models.Device) -> None:
    db.delete(db_device)
    db.commit()


# Connection CRUD --------------------------------------------------------------

def get_connections(db: Session) -> List[models.Connection]:
    return db.query(models.Connection).order_by(models.Connection.id).all()


def get_connection(db: Session, connection_id: int) -> Optional[models.Connection]:
    return (
        db.query(models.Connection)
        .filter(models.Connection.id == connection_id)
        .first()
    )


def create_connection(
    db: Session, connection: schemas.ConnectionCreate
) -> models.Connection:
    db_connection = models.Connection(**connection.model_dump())
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def update_connection(
    db: Session,
    db_connection: models.Connection,
    connection_update: schemas.ConnectionUpdate,
) -> models.Connection:
    update_data = connection_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_connection, field, value)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def delete_connection(db: Session, db_connection: models.Connection) -> None:
    db.delete(db_connection)
    db.commit()


# Project CRUD -----------------------------------------------------------------

def get_projects(db: Session) -> List[schemas.ProjectSummary]:
    projects = db.query(models.Project).order_by(models.Project.updated_at.desc()).all()
    result = []
    for project in projects:
        device_count = len(project.project_data.get("devices", []))
        connection_count = len(project.project_data.get("connections", []))
        result.append(
            schemas.ProjectSummary(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
                is_auto_save=project.is_auto_save,
                device_count=device_count,
                connection_count=connection_count,
            )
        )
    return result


def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_auto_save_project(db: Session) -> Optional[models.Project]:
    return (
        db.query(models.Project)
        .filter(models.Project.is_auto_save == True)
        .first()
    )


def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(
        name=project.name,
        description=project.description,
        project_data=project.project_data.model_dump(),
        is_auto_save=False,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(
    db: Session, db_project: models.Project, project_update: schemas.ProjectUpdate
) -> models.Project:
    update_data = project_update.model_dump(exclude_unset=True)
    if "project_data" in update_data:
        update_data["project_data"] = update_data["project_data"].model_dump()
    
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, db_project: models.Project) -> None:
    db.delete(db_project)
    db.commit()


def create_or_update_auto_save(
    db: Session, project_data: schemas.ProjectData
) -> models.Project:
    """Create or update the auto-save project."""
    auto_save = get_auto_save_project(db)
    
    if auto_save:
        auto_save.project_data = project_data.model_dump()
        db.commit()
        db.refresh(auto_save)
        return auto_save
    else:
        db_project = models.Project(
            name="Auto Save",
            description="Automatically saved project",
            project_data=project_data.model_dump(),
            is_auto_save=True,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project


def get_current_state(db: Session) -> schemas.ProjectData:
    """Get current devices and connections as ProjectData."""
    devices = get_devices(db)
    connections = get_connections(db)
    
    return schemas.ProjectData(
        devices=[schemas.DeviceRead.model_validate(device) for device in devices],
        connections=[schemas.ConnectionRead.model_validate(conn) for conn in connections],
        ui_state=None,
    )

