"""API routers for devices and connections."""

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

