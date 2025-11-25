import os
import base64
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv
from bson import ObjectId

from utils import get_embedding_from_bytes
import logging

# basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("face_recognition_system")

# -----------------------------------------------------
# GLOBAL CACHE
# -----------------------------------------------------
embedding_cache = []

# -----------------------------------------------------
# ENV + MONGO CONNECTION
# -----------------------------------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI:
    raise RuntimeError("❌ ERROR: MONGODB_URI is missing from .env")

if not DB_NAME:
    print("⚠️ WARNING: DB_NAME not found. Using default 'face_db'")
    DB_NAME = "face_db"

# Connect to Mongo
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
except Exception as e:
    raise RuntimeError(f"❌ Cannot connect to MongoDB.\nDetails: {str(e)}")

db = client[DB_NAME]

try:
    fs = gridfs.GridFS(db)
    faces_col = db["faces"]
except Exception as e:
    raise RuntimeError(f"❌ Error initializing GridFS or collection: {str(e)}")

# Create indexes
try:
    faces_col.create_index("person_name")
    faces_col.create_index("gridfs_id")
    print("✅ MongoDB indexes created (person_name, gridfs_id)")
except Exception as e:
    print(f"⚠️ Index creation failed: {str(e)}")

print(f"✅ Connected to MongoDB database: {DB_NAME}")

# -----------------------------------------------------
# Load embeddings into cache
# -----------------------------------------------------
def load_embedding_cache():
    global embedding_cache
    embedding_cache = []

    print("⏳ Loading embeddings into RAM cache...")

    try:
        cursor = faces_col.find({}, {
            "filename": 1,
            "person_name": 1,
            "gridfs_id": 1,
            "embedding": 1
        })
    except Exception as e:
        print(f"❌ Failed to load cache: {str(e)}")
        return

    for doc in cursor:
        emb = doc.get("embedding")
        if not emb:
            continue

        try:
            emb = np.array(emb, dtype=float)
            emb = emb / np.linalg.norm(emb)
        except:
            continue

        embedding_cache.append({
            "filename": doc.get("filename"),
            "person_name": doc.get("person_name"),
            "gridfs_id": doc.get("gridfs_id"),
            "embedding": emb
        })

    print(f"✅ Cache loaded: {len(embedding_cache)} embeddings.")

logger.info("Loaded %d embeddings into cache.", len(embedding_cache))

# Load cache on startup
load_embedding_cache()

# -----------------------------------------------------
# FASTAPI APP + CORS
# -----------------------------------------------------
app = FastAPI(title="Face Recognition Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Lightweight health endpoint for deployment health checks."""
    try:
        # quick DB ping
        client.admin.command('ping')
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "cache_count": len(embedding_cache)
    }

# -----------------------------------------------------
# 📤 UPLOAD: Extract embedding + store image in GridFS
# -----------------------------------------------------
@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    person_name: str = Form(...)
):
    if not person_name or person_name.strip() == "":
        raise HTTPException(status_code=400, detail="Person name is required.")

    # Read file
    try:
        content = await file.read()
    except Exception as e:
        logger.exception("Failed to read uploaded file: %s", str(e))
        raise HTTPException(status_code=400, detail="Cannot read uploaded file.")

    if not content:
        logger.warning("Empty file uploaded: filename=%s", getattr(file, 'filename', None))
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Get embedding
    try:
        emb = get_embedding_from_bytes(content)
    except ValueError as ve:
        logger.warning("No face detected during upload: filename=%s, err=%s", getattr(file, 'filename', None), str(ve))
        raise HTTPException(status_code=400, detail=f"No face detected: {str(ve)}")
    except Exception as e:
        logger.exception("Embedding error during upload for filename=%s: %s", getattr(file, 'filename', None), str(e))
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    emb = emb / np.linalg.norm(emb)

    # Save image to GridFS
    try:
        grid_id = fs.put(
            content,
            filename=file.filename,
            contentType=file.content_type
        )
    except Exception as e:
        logger.exception("GridFS error while storing file=%s: %s", getattr(file, 'filename', None), str(e))
        raise HTTPException(status_code=500, detail=f"GridFS error: {str(e)}")

    # Save metadata
    doc = {
        "person_name": person_name.strip(),
        "filename": file.filename,
        "gridfs_id": grid_id,
        "embedding": emb.tolist()
    }

    try:
        res = faces_col.insert_one(doc)
    except Exception as e:
        try:
            fs.delete(grid_id)
        except:
            pass
        logger.exception("DB insert error for file=%s: %s", getattr(file, 'filename', None), str(e))
        raise HTTPException(status_code=500, detail=f"DB insert error: {str(e)}")

    # Update cache
    embedding_cache.append({
        "filename": file.filename,
        "person_name": person_name.strip(),
        "gridfs_id": grid_id,
        "embedding": emb
    })

    return {
        "status": "success",
        "message": f"Face of '{person_name}' uploaded successfully.",
        "id": str(res.inserted_id),
        "filename": file.filename
    }

# -----------------------------------------------------
# 🔍 SEARCH (ultra-fast using RAM cache)
# -----------------------------------------------------
@app.post("/search")
async def search_image(
    file: UploadFile = File(...),
    threshold: float = 1.15,
    max_results: int = 20
):
    # Read file
    try:
        content = await file.read()
    except Exception as e:
        logger.exception("Failed to read search file: %s", str(e))
        raise HTTPException(status_code=400, detail="Cannot read uploaded file.")

    if not content:
        logger.warning("Empty search file uploaded: filename=%s", getattr(file, 'filename', None))
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Compute embedding
    try:
        input_emb = get_embedding_from_bytes(content)
    except ValueError as ve:
        logger.warning("No face detected during search: filename=%s, err=%s", getattr(file, 'filename', None), str(ve))
        raise HTTPException(status_code=400, detail=f"No face detected: {str(ve)}")
    except Exception as e:
        logger.exception("Embedding error during search for filename=%s: %s", getattr(file, 'filename', None), str(e))
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    # Normalize
    try:
        input_emb = input_emb / np.linalg.norm(input_emb)
    except Exception as e:
        logger.exception("Normalization error for search file=%s: %s", getattr(file, 'filename', None), str(e))
        raise HTTPException(status_code=500, detail="Normalization error.")

    matches = []

    # FAST search (RAM only)
    for entry in embedding_cache:
        stored_emb = entry["embedding"]

        try:
            dist = float(np.linalg.norm(input_emb - stored_emb))
        except Exception as e:
            logger.exception("Distance computation error: %s", str(e))
            continue

        if dist <= float(threshold):
            try:
                grid_id = entry["gridfs_id"]
                file_obj = fs.get(grid_id)
                img_bytes = file_obj.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            except Exception as e:
                logger.exception("Failed to read image from GridFS during search for grid_id=%s: %s", str(entry.get("gridfs_id")), str(e))
                continue

            matches.append({
                "filename": entry["filename"],
                "person_name": entry["person_name"],
                "distance": dist,
                "image_base64": img_b64
            })

    matches = sorted(matches, key=lambda x: x["distance"])[:int(max_results)]

    return {
        "count": len(matches),
        "matches": matches
    }

# -----------------------------------------------------
# 📁 GET ALL IMAGES OF A PERSON
# -----------------------------------------------------
@app.get("/person_images")
async def get_person_images(person_name: str):
    if not person_name or person_name.strip() == "":
        raise HTTPException(status_code=400, detail="Person name is required.")

    person_name = person_name.strip()

    try:
        cursor = faces_col.find(
            {"person_name": person_name},
            {"filename": 1, "gridfs_id": 1}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    results = []
    for doc in cursor:
        raw_id = doc.get("gridfs_id")

        try:
            grid_id = ObjectId(raw_id) if isinstance(raw_id, str) else raw_id
            file_obj = fs.get(grid_id)
            img_bytes = file_obj.read()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        except Exception:
            continue

        results.append({
            "filename": doc.get("filename", "unknown"),
            "image_base64": img_b64
        })

    return {
        "person_name": person_name,
        "count": len(results),
        "images": results
    }
# -----------------------------------------------------
# ❌ DELETE PERSON (all images + embeddings + cache)
# -----------------------------------------------------
@app.delete("/delete_person")
async def delete_person(person_name: str):
    if not person_name or person_name.strip() == "":
        raise HTTPException(status_code=400, detail="Person name is required.")

    person_name = person_name.strip()

    # Find all documents for this person
    try:
        cursor = faces_col.find({"person_name": person_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    docs = list(cursor)

    if len(docs) == 0:
        return {
            "status": "not_found",
            "message": f"No records found for '{person_name}'.",
            "deleted_images": 0
        }

    deleted_count = 0

    # Delete GridFS files
    for doc in docs:
        grid_id = doc.get("gridfs_id")

        try:
            if isinstance(grid_id, str):
                grid_id = ObjectId(grid_id)
            fs.delete(grid_id)
            deleted_count += 1
        except:
            pass

    # Delete MongoDB docs
    try:
        faces_col.delete_many({"person_name": person_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from DB: {str(e)}")

    # Update cache
    global embedding_cache
    before = len(embedding_cache)
    embedding_cache = [
        e for e in embedding_cache if e["person_name"] != person_name
    ]
    after = len(embedding_cache)

    return {
        "status": "success",
        "message": f"Deleted {deleted_count} images and all data for '{person_name}'.",
        "deleted_images": deleted_count,
        "cache_removed": before - after
    }
