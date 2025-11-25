import numpy as np
from deepface import DeepFace
import io
import os
import logging
import tempfile
import numpy as np
from PIL import Image
from deepface import DeepFace

logger = logging.getLogger("face_recognition_system.utils")

# Configuration: preferred detector and image resizing
PREFERRED_DETECTOR = "opencv"
MAX_IMAGE_DIM = 480  # resize largest side to this (px)

# Cache built models by name to avoid re-loading
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
    """Write bytes to a temporary JPEG file after converting to RGB and resizing."""
    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    try:
        with Image.open(io.BytesIO(img_bytes)) as im:
            im = im.convert("RGB")
            # Resize while preserving aspect ratio
            w, h = im.size
            max_side = max(w, h)
            if max_side > max_dim:
                scale = max_dim / float(max_side)
                new_size = (int(w * scale), int(h * scale))
                im = im.resize(new_size, Image.LANCZOS)

            im.save(tmp_path, format="JPEG", quality=85)
    except Exception as e:
        logger.exception("Failed to prepare temp image for embedding: %s", str(e))
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise

    return tmp_path


def get_embedding_from_bytes(img_bytes, model_name="ArcFace", detector: str = None):
    """Get a face embedding from raw image bytes using a cached model and single detector.

    - Resizes the image to `MAX_IMAGE_DIM` on the longest side to speed up detection.
    - Uses a cached model built with `DeepFace.build_model` to avoid repeated model init.
    - Uses `detector` if provided, otherwise `PREFERRED_DETECTOR`.
    """

    detector_backend = detector or PREFERRED_DETECTOR

    tmp_path = None
    try:
        tmp_path = _prepare_image_file(img_bytes, MAX_IMAGE_DIM)

        # Call DeepFace.represent. Older DeepFace versions don't accept a prebuilt
        # `model` argument, so pass only model_name and detector_backend here.
        reps = DeepFace.represent(
            img_path=tmp_path,
            model_name=model_name,
            detector_backend=detector_backend,
        )

        if not reps:
            raise ValueError("No face detected")

        emb_val = None
        if isinstance(reps, dict):
            emb_val = reps.get("embedding") or reps.get("rep")
        elif isinstance(reps, list) and len(reps) > 0:
            first = reps[0]
            if isinstance(first, dict):
                emb_val = first.get("embedding") or first.get("rep")

        if emb_val is None:
            # try casting reps directly
            try:
                emb = np.array(reps, dtype=float)
                if emb.size > 0:
                    return emb
            except Exception:
                pass

        emb = np.array(emb_val, dtype=float)
        return emb
    except Exception as e:
        logger.exception("Embedding extraction failed (detector=%s): %s", detector_backend, str(e))
        raise
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# Preload the default model once at import time to avoid per-request model init.
try:
    _get_model("ArcFace")
    logger.info("Preloaded ArcFace model at import time.")
except Exception as e:
    logger.warning("Preloading ArcFace model failed (will build on first request): %s", str(e))
