# Enterprise Real-time Face Attendance Backend

Production-ready FastAPI backend for face recognition attendance.

## Stack
- FastAPI + async SQLAlchemy
- PostgreSQL (`DATABASE_URL`)
- MTCNN + FaceNet (`facenet-pytorch`)
- FAISS (`IndexFlatL2` by default, optional `IndexIVFFlat`)

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/attendance_db"
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Endpoints
- `POST /register-employee`
  - form: `employee_id`, `name`
  - files: `images` (exactly 5 images)
- `POST /attendance`
  - form-data: `image`, optional `device_id`
- `GET /health`

## Production Decisions
- Face recognition remains backend-only; client uses ML Kit only for detection and anti-spoof signals.
- FAISS index is loaded at startup and can bootstrap from DB embeddings.
- Incremental embedding updates are supported without full rebuild.
- For very large datasets, set `FAISS_USE_IVF=true` and retrain index with accumulated vectors.
