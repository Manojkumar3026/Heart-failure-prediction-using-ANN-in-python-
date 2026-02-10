"""Employee registration orchestration service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Employee
from backend.services.embedding_service import EmbeddingService
from backend.services.faiss_service import FaissService


class RegistrationService:
    def __init__(self, embedding_service: EmbeddingService, faiss_service: FaissService) -> None:
        self.embedding_service = embedding_service
        self.faiss_service = faiss_service

    async def register_employee(
        self,
        db: AsyncSession,
        employee_id: str,
        name: str,
        image_files,
    ) -> Employee:
        avg_embedding = await self.embedding_service.average_embedding(image_files)

        result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))
        employee = result.scalar_one_or_none()

        if employee is None:
            employee = Employee(employee_id=employee_id, name=name, embedding_vector=avg_embedding.tolist())
            db.add(employee)
            await db.flush()
        else:
            employee.name = name
            employee.embedding_vector = avg_embedding.tolist()

        await db.commit()
        await db.refresh(employee)

        self.faiss_service.upsert_embedding(employee.id, avg_embedding)
        return employee
