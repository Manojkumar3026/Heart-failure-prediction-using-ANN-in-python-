from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import Base, engine, get_db_session
from backend.database.models import Employee
from backend.models.facenet_model import FaceNetModel
from backend.services.attendance_service import AttendanceService
from backend.services.embedding_service import EmbeddingService
from backend.services.faiss_service import FaissService
from backend.services.registration_service import RegistrationService

FAISS_DIR = Path(__file__).resolve().parent / "faiss_index"
RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", "0.95"))
USE_IVF = os.getenv("FAISS_USE_IVF", "false").lower() == "true"


class RegisterEmployeeResponse(BaseModel):
    message: str
    employee_id: str
    name: str


class AttendanceResponse(BaseModel):
    recognized: bool
    message: str
    employee_id: str | None = None
    name: str | None = None
    distance: float | None = None
    timestamp: str | None = None


class HealthResponse(BaseModel):
    status: str
    faiss_index_size: int = Field(..., description="Number of vectors currently loaded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    model = FaceNetModel()
    embedding_service = EmbeddingService(model)
    faiss_service = FaissService(base_dir=FAISS_DIR, use_ivf=USE_IVF)
    faiss_service.load()

    registration_service = RegistrationService(embedding_service, faiss_service)
    attendance_service = AttendanceService(embedding_service, faiss_service, RECOGNITION_THRESHOLD)

    # Bootstrap FAISS from database if empty or brand new.
    async with AsyncSession(engine, expire_on_commit=False) as session:
        result = await session.execute(select(Employee.id, Employee.embedding_vector))
        rows = result.all()
        if rows and faiss_service.index.ntotal == 0:
            ids = np.array([row[0] for row in rows], dtype=np.int64)
            vectors = np.array([row[1] for row in rows], dtype=np.float32)
            faiss_service.rebuild(ids, vectors)

    app.state.registration_service = registration_service
    app.state.attendance_service = attendance_service
    app.state.faiss_service = faiss_service

    yield


app = FastAPI(
    title="Enterprise Face Attendance API",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    faiss_service: FaissService = app.state.faiss_service
    return HealthResponse(status="ok", faiss_index_size=int(faiss_service.index.ntotal))


@app.post("/register-employee", response_model=RegisterEmployeeResponse)
async def register_employee(
    employee_id: Annotated[str, Form(...)],
    name: Annotated[str, Form(...)],
    images: Annotated[list[UploadFile], File(...)],
    db: AsyncSession = Depends(get_db_session),
):
    if len(images) != 5:
        raise HTTPException(status_code=422, detail="Exactly 5 registration images are required")

    service: RegistrationService = app.state.registration_service
    employee = await service.register_employee(
        db=db,
        employee_id=employee_id.strip(),
        name=name.strip(),
        image_files=images,
    )
    return RegisterEmployeeResponse(
        message="Employee registered successfully",
        employee_id=employee.employee_id,
        name=employee.name,
    )


@app.post("/attendance", response_model=AttendanceResponse)
async def mark_attendance(
    image: UploadFile = File(...),
    device_id: str = Form("mobile-device"),
    db: AsyncSession = Depends(get_db_session),
):
    service: AttendanceService = app.state.attendance_service
    recognition = await service.recognize_employee(image, db)

    if not recognition.recognized or recognition.employee is None:
        return AttendanceResponse(recognized=False, message="Not recognized")

    record = await service.mark_attendance(
        db=db,
        employee=recognition.employee,
        device_id=device_id,
    )
    return AttendanceResponse(
        recognized=True,
        message="Attendance marked",
        employee_id=recognition.employee.employee_id,
        name=recognition.employee.name,
        distance=recognition.distance,
        timestamp=record.timestamp.isoformat(),
    )
