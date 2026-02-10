"""Embedding extraction service."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable, List

import numpy as np
from fastapi import HTTPException, UploadFile
from PIL import Image

from backend.models.facenet_model import FaceNetModel


class EmbeddingService:
    def __init__(self, model: FaceNetModel) -> None:
        self.model = model

    async def image_to_embedding(self, file: UploadFile) -> np.ndarray:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty image payload")

        try:
            image = Image.open(BytesIO(raw)).convert("RGB")
        except Exception as exc:  # pylint: disable=broad-except
            raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}") from exc

        tensor = self.model.embed_face(image)
        if tensor is None:
            raise HTTPException(status_code=422, detail="No detectable face in image")

        return tensor.numpy().astype(np.float32)

    async def average_embedding(self, files: Iterable[UploadFile]) -> np.ndarray:
        embeddings: List[np.ndarray] = []
        for file in files:
            emb = await self.image_to_embedding(file)
            embeddings.append(emb)

        if len(embeddings) < 3:
            raise HTTPException(
                status_code=422,
                detail="At least 3 valid face images are required for stable registration",
            )

        stack = np.stack(embeddings, axis=0)
        avg = np.mean(stack, axis=0)
        norm = np.linalg.norm(avg)
        if norm == 0:
            raise HTTPException(status_code=500, detail="Failed to normalize averaged embedding")
        return (avg / norm).astype(np.float32)
