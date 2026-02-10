"""FAISS index management with persistence and migration hooks."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional, Tuple

import faiss
import numpy as np


class FaissService:
    def __init__(self, base_dir: Path, dimension: int = 512, use_ivf: bool = False) -> None:
        self.base_dir = base_dir
        self.dimension = dimension
        self.use_ivf = use_ivf
        self.index_path = base_dir / ("employees_ivf.index" if use_ivf else "employees_flat.index")
        self.meta_path = base_dir / "faiss_meta.json"
        self.lock = threading.Lock()
        self.index: faiss.IndexIDMap

    def _create_index(self) -> faiss.IndexIDMap:
        if self.use_ivf:
            quantizer = faiss.IndexFlatL2(self.dimension)
            ivf = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            return faiss.IndexIDMap(ivf)
        return faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension))

    def load(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = self._create_index()

    def persist(self) -> None:
        with self.lock:
            faiss.write_index(self.index, str(self.index_path))
            payload = {
                "index_type": "IndexIVFFlat" if self.use_ivf else "IndexFlatL2",
                "dimension": self.dimension,
                "ntotal": int(self.index.ntotal),
            }
            self.meta_path.write_text(json.dumps(payload, indent=2))

    def train_if_needed(self, vectors: np.ndarray) -> None:
        base = self.index.index if isinstance(self.index, faiss.IndexIDMap) else self.index
        if isinstance(base, faiss.IndexIVF) and not base.is_trained:
            base.train(vectors)

    def rebuild(self, ids: np.ndarray, vectors: np.ndarray) -> None:
        with self.lock:
            self.index = self._create_index()
            self.train_if_needed(vectors)
            self.index.add_with_ids(vectors.astype(np.float32), ids.astype(np.int64))
            self.persist()

    def upsert_embedding(self, employee_db_id: int, embedding: np.ndarray) -> None:
        vec = embedding.astype(np.float32).reshape(1, -1)
        row_id = np.array([employee_db_id], dtype=np.int64)
        with self.lock:
            self.index.remove_ids(row_id)
            self.train_if_needed(vec)
            self.index.add_with_ids(vec, row_id)
            self.persist()

    def search(self, embedding: np.ndarray, threshold: float) -> Optional[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return None

        vec = embedding.astype(np.float32).reshape(1, -1)
        distances, ids = self.index.search(vec, 1)
        matched_id = int(ids[0][0])
        distance = float(distances[0][0])

        if matched_id < 0 or distance > threshold:
            return None

        return matched_id, distance
