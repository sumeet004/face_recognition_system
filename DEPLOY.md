# Deployment Guide

This document shows practical steps to deploy the project:
- Frontend (Vite + React) to **Vercel** (recommended)
- Backend (FastAPI + DeepFace) as a Docker container to **Render**, **Fly.io**, **Railway**, or any Docker-capable host
- MongoDB using **MongoDB Atlas** (recommended)

Important: the backend runs heavy ML models (DeepFace). Do NOT deploy the backend to Vercel serverless functions. Use a long-running container/VM.

---

## Prerequisites
- GitHub repository with this project pushed
- Docker installed locally (for building/testing the backend image)
- An account for your chosen host (Vercel + Render/Fly/Railway) and MongoDB Atlas
- Optional: a paid/appropriate instance if you require GPU acceleration (for faster embeddings)

---

## Environment variable names
- Backend:
  - `MONGODB_URI` (required) – MongoDB connection string (Atlas)
  - `DB_NAME` (optional, default `face_db`)
- Frontend (Vercel):
  - `VITE_API_BASE` – full URL of the backend API, e.g. `https://my-backend.onrender.com`

---

## 1) Frontend: Deploy to Vercel
Vercel is the recommended host for your static Vite app.

1. Push your repo to GitHub.
2. Go to https://vercel.com and create/import a new project from your GitHub repo.
3. During import set:
   - Root directory: `frontend`
   - Framework preset: `Vite` (or leave it to auto-detect)
   - Build command: `npm run build`
   - Output directory: `dist`
4. Add the environment variable in Vercel dashboard (Project > Settings > Environment Variables):
   - `VITE_API_BASE` = `https://<your-backend-domain>`
5. Deploy and open the provided Vercel URL. The frontend will call the backend at `VITE_API_BASE`.

Local test (optional):
```powershell
cd 'd:\My projects\face_recognition_system\frontend'
npm install
npm run dev
# or build locally
npm run build
npx serve dist
```

---

## 2) Backend: Docker-based deployment (recommended)
Create, test, and push a Docker image. A `backend/Dockerfile` is provided in this repo.

### Build & run locally (test)
```powershell
cd 'd:\My projects\face_recognition_system\backend'
# Build
docker build -t face-rec-backend .
# Run (replace MONGODB_URI with your connection string)
docker run -p 8000:8000 --env MONGODB_URI="mongodb+srv://<user>:<pass>@cluster0.mongodb.net/<dbname>?retryWrites=true&w=majority" face-rec-backend
```
Open `http://localhost:8000/docs` to verify the API.

Notes:
- The first boot will be slow if DeepFace downloads models.
- To reduce runtime, ensure `requirements.txt` lists specific versions and that the Dockerfile includes system libs (`libgl1`, `libglib2.0-0`, etc.).

### Deploy to Render (Docker)
1. Push the repo to GitHub.
2. Create a new service on Render: `New` → `Web Service` → Connect GitHub.
3. Select your repository and point to the `backend` folder (set the root if needed).
4. Choose `Docker` as the environment (Render will use your `Dockerfile`).
5. Set environment variables on Render:
   - `MONGODB_URI`
   - `DB_NAME` (optional)
6. Choose instance size (start with small, increase if model performance is poor).
7. Deploy — watch logs for model download progress.

### Deploy to Fly.io (Docker)
1. Install `flyctl` and login: https://fly.io/docs/
2. Create an app and deploy from the `backend` folder:
```bash
flyctl launch --name face-rec-backend --no-deploy
# adjust config if needed in fly.toml
flyctl deploy
```
3. Set secrets:
```bash
flyctl secrets set MONGODB_URI="<uri>"
```

### Deploy to Railway
Railway supports Docker deployments and GitHub integration. Use Railway dashboard to create a Docker service and set env vars.

---

## 3) MongoDB Atlas (recommended)
1. Create an Atlas account and create a free cluster.
2. Create a database user with a password and copy the connection string.
3. Update network access (add your backend host IP or allow access from anywhere for testing — prefer CIDR restrictions for production).
4. Set `MONGODB_URI` in your backend host to the Atlas connection string.

Example connection string format:
```
mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/myFirstDatabase?retryWrites=true&w=majority
```

---

## 4) Vite + Env variable (frontend)
The frontend code reads `VITE_API_BASE`:
```js
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
```
Make sure to set `VITE_API_BASE` on Vercel to the backend production URL.

---

## 5) CI: Build and publish backend image (optional)
This example pushes a Docker image to GitHub Container Registry (GHCR) using GitHub Actions. You can adapt it to push to Docker Hub or another registry.

Create `.github/workflows/docker-publish.yml` with the following (example):
```yaml
name: Build and Publish Backend Docker Image

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/face-rec-backend:latest
```
After publishing the image you can configure Render/Fly to deploy from that image or keep Render's GitHub integration to build automatically.

---

## 6) Notes & troubleshooting
- Model downloads: first startup may take several minutes while DeepFace downloads weights. Monitor backend logs.
- Missing native libs: if DeepFace/OpenCV fails, add the required OS packages into the Dockerfile and rebuild.
- Performance: for production speed consider a machine with GPU and matching torch/tensorflow GPU packages, or a worker architecture.
- CORS: backend currently allows `*`. For production set allowed origins to your Vercel URL.

---

## 7) Extras I can add for you
- Render-specific `deploy.md` with screenshots & host-specific nuances.
- GitHub Actions workflow to automatically deploy to Render/Fly when CI passes.
- GPU-enabled Dockerfile variant (for cloud hosts with GPUs).

If you want me to add any of these, tell me which one and I will create the files.
