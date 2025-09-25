"""SQLAlchemy models for core NISTO entities."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False, default="generic")
    x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    config: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)

    connections_out: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="source_device",
        cascade="all, delete-orphan",
        foreign_keys="Connection.source_device_id",
        passive_deletes=True,
    )
    connections_in: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="target_device",
        cascade="all, delete-orphan",
        foreign_keys="Connection.target_device_id",
        passive_deletes=True,
    )


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    target_device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(String, nullable=False, default="ethernet")
    properties: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)

    source_device: Mapped[Device] = relationship(
        "Device", back_populates="connections_out", foreign_keys=[source_device_id]
    )
    target_device: Mapped[Device] = relationship(
        "Device", back_populates="connections_in", foreign_keys=[target_device_id]
    )


class Boundary(Base):
    __tablename__ = "boundaries"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)  # UUID from frontend
    type: Mapped[str] = mapped_column(String, nullable=False)  # ato, building, etc.
    label: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[list] = mapped_column(JSON, nullable=False)  # Array of {x, y} points
    closed: Mapped[bool] = mapped_column(Integer, default=True)
    style: Mapped[Dict] = mapped_column(JSON, nullable=False)  # Style properties
    created: Mapped[str] = mapped_column(String, nullable=False)  # ISO date string
    # New device-like properties
    x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Position x
    y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Position y
    width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Boundary width
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Boundary height
    config: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)  # Custom properties


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_data: Mapped[Dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_auto_save: Mapped[bool] = mapped_column(Integer, default=False)  # For auto-save slot

