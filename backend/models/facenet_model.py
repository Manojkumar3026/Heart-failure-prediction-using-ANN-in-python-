"""FaceNet + MTCNN model wrappers.

ML Kit is used only in the Flutter client for face detection UX.
Backend performs authoritative face detection/alignment and recognition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image


@dataclass
class FaceNetConfig:
    image_size: int = 160
    margin: int = 16
    min_face_size: int = 40


class FaceNetModel:
    """Loads MTCNN + FaceNet once and reuses across requests."""

    def __init__(self, config: Optional[FaceNetConfig] = None) -> None:
        self.config = config or FaceNetConfig()
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        self.mtcnn = MTCNN(
            image_size=self.config.image_size,
            margin=self.config.margin,
            min_face_size=self.config.min_face_size,
            post_process=True,
            device=self.device,
            keep_all=False,
        )
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)

    def get_face_tensor(self, image: Image.Image) -> Optional[torch.Tensor]:
        """Detects and aligns a single most-prominent face."""
        aligned = self.mtcnn(image)
        if aligned is None:
            return None
        return aligned.unsqueeze(0).to(self.device)

    @torch.no_grad()
    def embed_face(self, image: Image.Image) -> Optional[torch.Tensor]:
        face = self.get_face_tensor(image)
        if face is None:
            return None
        emb = self.resnet(face)
        emb = torch.nn.functional.normalize(emb, p=2, dim=1)
        return emb.squeeze(0).cpu()
