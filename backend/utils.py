import numpy as np
from deepface import DeepFace
import tempfile
import os

def get_embedding_from_bytes(img_bytes, model_name="Facenet512", detector="retinaface"):
    # Save temporarily
    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    with open(tmp_path, "wb") as f:
        f.write(img_bytes)

    # Compute embedding
    reps = DeepFace.represent(
        img_path=tmp_path,
        model_name=model_name,
        detector_backend=detector
    )

    # Clean up
    os.remove(tmp_path)

    if not reps:
        raise ValueError("No face detected!")

    emb = np.array(reps[0]["embedding"], dtype=float)
    return emb
