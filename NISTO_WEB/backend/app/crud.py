"""CRUD utilities for devices and connections."""

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

