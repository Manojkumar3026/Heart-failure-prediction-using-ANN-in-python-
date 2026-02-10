"""SQLAlchemy ORM models for employee and attendance."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.db import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)

    attendances: Mapped[list["Attendance"]] = relationship(back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="present", nullable=False)

    employee: Mapped[Employee] = relationship(back_populates="attendances")


Index("ix_attendances_employee_ts", Attendance.employee_id, Attendance.timestamp)
