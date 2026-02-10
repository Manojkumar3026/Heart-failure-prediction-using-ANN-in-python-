"""Attendance recognition + persistence service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Attendance, Employee
from backend.services.embedding_service import EmbeddingService
from backend.services.faiss_service import FaissService


@dataclass
class RecognitionResult:
    recognized: bool
    message: str
    employee: Employee | None = None
    distance: float | None = None


class AttendanceService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        faiss_service: FaissService,
        threshold: float = 0.95,
    ) -> None:
        self.embedding_service = embedding_service
        self.faiss_service = faiss_service
        self.threshold = threshold

    async def recognize_employee(self, image_file, db: AsyncSession) -> RecognitionResult:
        embedding = await self.embedding_service.image_to_embedding(image_file)
        match = self.faiss_service.search(embedding, threshold=self.threshold)
        if match is None:
            return RecognitionResult(recognized=False, message="Face not recognized")

        employee_db_id, distance = match
        result = await db.execute(select(Employee).where(Employee.id == employee_db_id))
        employee = result.scalar_one_or_none()
        if employee is None:
            return RecognitionResult(recognized=False, message="Face not recognized")

        return RecognitionResult(
            recognized=True,
            message="Attendance marked",
            employee=employee,
            distance=distance,
        )

    async def mark_attendance(
        self,
        db: AsyncSession,
        employee: Employee,
        device_id: str,
        status: str = "present",
    ) -> Attendance:
        record = Attendance(
            employee_id=employee.id,
            device_id=device_id,
            status=status,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
