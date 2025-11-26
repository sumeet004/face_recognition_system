import os

# Force DeepFace to use PyTorch backend
os.environ["DEEPFACE_BACKEND"] = "torch"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import io
import logging
import tempfile
import numpy as np
from PIL import Image
from deepface import DeepFace

logger = logging.getLogger("face_recognition_system.utils")

# Configuration: preferred detector and image resizing
PREFERRED_DETECTOR = "retinaface"  # better accuracy for face detection
MAX_IMAGE_DIM = 480  # resize largest side to this (px)

# Cache built models
_MODEL_CACHE = {}


def _get_model(model_name: str):
    """Return a prebuilt DeepFace model (cached)."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    logger.info("Building DeepFace model: %s", model_name)
    model = DeepFace.build_model(model_name)
    _MODEL_CACHE[model_name] = model
    return model


def _prepare_image_file(img_bytes: bytes, max_dim: int = MAX_IMAGE_DIM) -> str:
    """Write bytes to a temporary JPEG file after resizing."""
    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    try:
        with Image.open(io.BytesIO(img_bytes)) as im:
            im = im.convert("RGB")
            w, h = im.size
            max_side = max(w, h)
            if max_side > max_dim:
                scale = max_dim / float(max_side)
                new_size = (int(w * scale), int(h * scale))
                im = im.resize(new_size, Image.LANCZOS)

            im.save(tmp_path, format="JPEG", quality=85)
    except Exception as e:
        logger.exception("Failed to prepare temp image: %s", str(e))
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise

    return tmp_path


def get_embedding_from_bytes(img_bytes, model_name="ArcFace", detector: str = None):
    """Get embedding from raw image bytes."""
    detector_backend = detector or PREFERRED_DETECTOR
    tmp_path = None

    try:
        tmp_path = _prepare_image_file(img_bytes, MAX_IMAGE_DIM)

        reps = DeepFace.represent(
            img_path=tmp_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=False,
            align=True,
        )

        if not reps:
            raise ValueError("No face detected")

        if isinstance(reps, dict):
            emb_val = reps.get("embedding") or reps.get("rep")
        elif isinstance(reps, list) and len(reps) > 0 and isinstance(reps[0], dict):
            emb_val = reps[0].get("embedding") or reps[0].get("rep")
        else:
            emb_val = reps

        return np.array(emb_val, dtype=float)

    except Exception as e:
        logger.exception("Embedding extraction failed: %s", str(e))
        raise

    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# Preload ArcFace model at import
try:
    _get_model("ArcFace")
    logger.info("Preloaded ArcFace model at import time.")
except Exception as e:
    logger.warning("Model preload failed: %s", str(e))
