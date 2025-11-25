# Render Secrets / Environment Variables Guide

This file explains which secrets/environment variables your backend needs and how to set them securely on Render (recommended) using the Render Dashboard.

Do NOT commit secrets (connection strings, API keys, passwords) into the repo or `render.yaml`.

---

## Required backend secrets
- `MONGODB_URI` (required)
  - Your MongoDB Atlas connection string, e.g.
    `mongodb+srv://<user>:<password>@cluster0.abcd.mongodb.net/<dbname>?retryWrites=true&w=majority`
- `DB_NAME` (optional)
  - Database name (default in the app is `face_db` if unset)

Optional / recommended:
- `LOG_LEVEL` (e.g. `INFO`, `DEBUG`)
- `RENDER_ENV` (e.g. `production`) — if you need environment-specific code paths
- `SENTRY_DSN` (if you use Sentry for error monitoring)
- `MAX_IMAGE_DIM` (if you want to override the default resizing setting)

---

## Add secrets using the Render Dashboard (UI)
1. Go to https://dashboard.render.com and open your service (e.g. `face-rec-backend`).
2. In the service page, select **Environment** or **Environment & Secrets** (location varies).
3. Click **Add Environment Variable** (or **Add Secret**) and enter the key and value.
   - Key: `MONGODB_URI`
   - Value: paste the full Atlas connection string
4. Repeat for `DB_NAME` and other variables.
5. Click **Save**.

After saving, Render will apply the variables for your service. For some changes, Render may trigger a deploy — watch the deploy logs.

---

## Using the Render CLI (optional)
Render has a CLI you can install (`brew install render` or see Render docs). CLI commands change over time; refer to Render docs for exact commands. Typical workflow:

1. Install and log in: `render login`
2. Create or update environment variables for your service using the dashboard or CLI (see Render docs for the current CLI syntax).

Note: I recommend using the dashboard for secrets if you're not familiar with the CLI.

---

## Best practices
- Never store credentials in plaintext in the repository.
- Use a dedicated MongoDB user with a strong password and limited privileges.
- Rotate credentials periodically and immediately if you suspect leakage.
- Use `LOG_LEVEL=INFO` in production and `DEBUG` only while troubleshooting.
- Limit network access for the MongoDB cluster to only the required IPs (or use VPC peering where supported).

---

## Verifying secrets
1. After adding `MONGODB_URI`, trigger a deploy (or restart) and check the service logs in Render to confirm the server can connect to MongoDB.
2. Use the health endpoint to verify: `https://<your-render-url>/health` — it should return `{"status":"ok","cache_count":...}` when DB is reachable.

---

If you'd like, I can add a small script to the repo that tests the environment variables locally (reads `.env` and prints a safe summary), or add `render.yaml`-compatible secret references if you prefer infrastructure-as-code. Tell me which you prefer.