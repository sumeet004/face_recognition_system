# Face Recognition System

This repository contains a FastAPI backend and a Vite + React frontend for a simple face recognition system.

- `backend/` - FastAPI app that computes face embeddings with DeepFace, stores images in MongoDB GridFS, and serves upload/search endpoints.
- `frontend/` - Vite + React frontend to upload/search faces.


## Deployment Overview

Recommended deployment split:

- Frontend: Deploy to Vercel (static site). Use the env var `VITE_API_BASE` to point to the backend URL.
- Backend: Deploy as a container (Docker) to Render / Fly.io / Railway / a VM / cloud provider that supports long-running Python processes and large ML dependencies. Vercel is not suitable for the backend because DeepFace and model downloads are heavy and not serverless-friendly.
- Database: Use MongoDB Atlas (hosted MongoDB) and set `MONGODB_URI` in the backend environment.


## Quick Frontend Steps (Vercel)

1. In the frontend code, API base reads from `import.meta.env.VITE_API_BASE` (fallback to `http://localhost:8000`).
2. Push your repo to GitHub.
3. In Vercel, create a new project and import the repo. Set the project root to `frontend`.
4. Build command: `npm run build`.
5. Output directory: `dist`.
6. Add Environment Variable:
   - `VITE_API_BASE` = `https://<your-backend-domain>` (once backend is deployed).


## Backend Docker + Deploy (Render / Fly / Railway)

A sample `backend/Dockerfile` is included. Steps:

1. Ensure `requirements.txt` is up to date in `backend/`.
2. Build locally to test:

```powershell
cd "d:\My projects\face_recognition_system\backend"
docker build -t face-rec-backend .
# run (map port 8000)
docker run -p 8000:8000 --env MONGODB_URI="<your-uri>" face-rec-backend
```

3. Deploy to a Docker-supporting host (Render/Fly.io/Railway): connect your GitHub repo and point to the `backend` folder. Provide environment variables:

- `MONGODB_URI` (MongoDB Atlas connection string)
- `DB_NAME` (optional)

Notes:
- The first startup will download DeepFace model weights; expect the first boot to take longer.
- Include required system packages (OpenCV dependencies) — the Dockerfile installs basic libs (`libgl1`, `libglib2.0-0`, `ffmpeg`). Add more if your environment requires them.


## Environment variables

- Backend:
  - `MONGODB_URI` (required)
  - `DB_NAME` (optional)

- Frontend (Vercel):
  - `VITE_API_BASE` (e.g. `https://api.example.com`)


## Troubleshooting & Tips

- If DeepFace fails to initialize, check logs for missing native libs. Add required distro packages to the Dockerfile.
- Monitor logs for model download progress — the model files can be large.
- For production, enable HTTPS on the backend and tighten CORS origins in `backend/app.py`.


## Want help?
I can:
- Add a small `deploy.md` with step-by-step Render / Fly instructions.
- Add CI config to build and push Docker images automatically.
- Adjust Dockerfile for GPU-enabled hosts.
