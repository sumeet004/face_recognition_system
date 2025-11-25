# Deploying the Backend to Render (Docker)

This guide walks through deploying the FastAPI backend (with DeepFace) to Render using Docker. Render is a good choice because it runs long-lived containers and gives access to logs, environment variables and instance sizing.

> Important: The backend performs heavy ML work (DeepFace) and downloads model weights on first run. Expect the first deployment to take longer. Choose an instance with enough CPU/RAM for acceptable latency.

---

## 1. Prepare your repo
- Ensure the `backend/Dockerfile` exists at `backend/Dockerfile` (this repo includes one).
- Confirm `backend/requirements.txt` lists all Python deps.
- Make sure `backend/.dockerignore` excludes local artifacts and secrets (it does in this repo).
- Commit and push your changes to GitHub.

---

## 2. Create MongoDB (Atlas)
Render won't host your DB. Use MongoDB Atlas (or another hosted Mongo):
1. Create an Atlas account and cluster (free tier available).
2. Create a DB user and copy the connection string.
3. Add network access for your backend (you can allow access from anywhere for testing, but restrict for production).
4. Note the connection string — you'll set it as `MONGODB_URI` in Render.

---

## 3. Create a new Render service (Docker)
1. Go to https://dashboard.render.com and sign in.
2. Click **New** → **Web Service**.
3. Connect your GitHub account and select the repository.
4. For **Environment**, choose **Docker** (Render will use the `backend/Dockerfile`).
5. **Name** the service (e.g., `face-rec-backend`).
6. For **Branch**, choose the branch you want to deploy (e.g., `main`).
7. For **Root**, set the path to `backend` (or leave blank if Dockerfile is at repo root). Render will detect the Dockerfile.
8. Select the **Region** closest to your users.

### Instance Type / Sizing
- Start with `Starter` or `Standard` and increase if you see performance issues. DeepFace embedding on CPU is CPU- and memory-intensive; consider `Standard` or larger for production.
- If you expect heavy traffic or need GPU acceleration, use a more powerful plan or a GPU host (note: Render does not provide GPU tiers at the time of writing; use a cloud VM or specialized host for GPU).

---

## 4. Set Environment Variables
In the Render service settings, add the following env vars (Service → Environment):
- `MONGODB_URI` = `mongodb+srv://<user>:<pass>@cluster0.mongodb.net/<dbname>?retryWrites=true&w=majority`
- `DB_NAME` = `face_db` (optional)

Optional / useful:
- `LOG_LEVEL` = `INFO` (or `DEBUG` while debugging)
- `MAX_IMAGE_DIM` (if you wired this in your code as env-configurable)

---

### Health check and Start Command
- Render will use the Docker `CMD` to start the container (the included Dockerfile runs `uvicorn app:app ...`).
- Set a **Health Check Path** to `/health` (recommended). This helps Render detect when the service is ready and healthy.

We added a simple `/health` endpoint in `backend/app.py` that returns a 200 JSON payload and the current embedding cache size. Use `/health` as the Render health check path.

Example minimal health endpoint (already added to this repo):
```python
@app.get("/health")
async def health():
    # returns 'ok' when MongoDB ping succeeds and current cache count
    return {"status": "ok", "cache_count": len(embedding_cache)}
```

Quick test (locally):
```powershell
Invoke-RestMethod http://localhost:8000/health
# or with curl
curl http://localhost:8000/health
```

---

## 6. Deploy & Monitor
- Click **Create Web Service**. Render will build the Docker image and start the container.
- Monitor the build logs — they show pip installs and system package steps.
- When the container starts, check service logs for DeepFace/model initialization messages. The first run may download models and take several minutes.

---

## 7. After Deploy: domain & environment
- Once deployed, Render gives a public URL (e.g., `https://face-rec-backend.onrender.com`).
- Set your frontend `VITE_API_BASE` (on Vercel) to this URL.
- Update CORS in `backend/app.py` to restrict origins to your frontend domain for production.

Example CORS tightening in `app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-front-end.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. Troubleshooting
- "Model download is slow" — be patient; watch logs. The model files can be large.
- "Missing system libs" — errors from OpenCV or DeepFace usually tell you which libc or libGL package is missing; add them to the Dockerfile `apt-get install` line and redeploy.
- "Out of memory / OOM" — increase instance size.
- "Requests time out" — consider increasing resource limits or adding a queue/worker model for embedding extraction.

---

## 9. Scaling & performance recommendations
- Use a larger instance size for faster embeddings or set up an async queue (Celery/RQ) to offload embedding computation to worker processes.
- For low-latency production, run on GPU-enabled hosts and install GPU-accelerated PyTorch/TensorFlow packages.
- Store thumbnails instead of full images in responses to reduce payload size.

---

## 10. Optional: Render YAML / Infrastructure as Code
Render supports `render.yaml` for IaC — see Render docs if you prefer to declare services / environment variables in code.

---

If you want, I can:
- Add a `/health` endpoint to `backend/app.py` and patch the Dockerfile to speed builds.
- Create a sample `render.yaml` with the service and env var declaration.
- Add a small `deploy-render.md` with screenshots for each Render dashboard step.

Which of these follow-ups would you like?