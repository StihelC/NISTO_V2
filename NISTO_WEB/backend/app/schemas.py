"""Pydantic schemas for API request and response models."""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(default="generic")
    x: Optional[float] = None
    y: Optional[float] = None
    config: Dict[str, str] = Field(default_factory=dict)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    type: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    config: Optional[Dict[str, str]] = None


class DeviceRead(DeviceBase):
    id: int

    class Config:
        from_attributes = True


class ConnectionBase(BaseModel):
    source_device_id: int
    target_device_id: int
    link_type: str = Field(default="ethernet")
    properties: Dict[str, str] = Field(default_factory=dict)


class ConnectionCreate(ConnectionBase):
    pass


class ConnectionUpdate(BaseModel):
    source_device_id: Optional[int] = None
    target_device_id: Optional[int] = None
    link_type: Optional[str] = None
    properties: Optional[Dict[str, str]] = None


class ConnectionRead(ConnectionBase):
    id: int

    class Config:
        from_attributes = True

