"""SQLAlchemy models for core NISTO entities."""

from __future__ import annotations

from typing import Dict, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer, String
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

