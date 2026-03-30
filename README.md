# Minimal eLearning (Instructor Upload → Student Watch)

This workspace contains a minimal backend API for:
- Instructor uploads lecture videos
- Student watches (streaming URL)
- Single-session enforcement (same account cannot be used simultaneously)

## What to run
The **real backend** is in `server/`.

### Start server
```powershell
Push-Location server
c:/Users/zaido/OneDrive/Desktop/elearning/.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

### Create admin user
```powershell
Push-Location server
c:/Users/zaido/OneDrive/Desktop/elearning/.venv/Scripts/python.exe manage.py createsuperuser
```

Admin: http://127.0.0.1:8000/admin/

## API
- POST `/api/auth/token/` (username/password) → returns JWTs (single-session)
- POST `/api/lectures/` (instructor only, multipart: `title`, `video_file`)
- GET `/api/lectures/` (auth)
- GET `/api/lectures/{id}/playback/` (auth) → returns a short-lived `playback_url`
- GET `/api/lectures/{id}/stream/?token=...` → serves the file (token expires quickly)
- GET `/api/lectures/{id}/hls/manifest/?token=...` → serves HLS manifest (if HLS generated)

## Watch page (minimal UI)
Open: http://127.0.0.1:8000/watch/

Lecture list (minimal UI): http://127.0.0.1:8000/lectures/

Instructor upload (minimal UI): http://127.0.0.1:8000/upload/

Lecture list now includes a “Transcode HLS” button for each lecture (instructor only). This triggers HLS segment generation for playback security and streaming.

It will:
- Log in via `/api/auth/token/`
- Fetch `/api/lectures/{id}/playback/`
- Play either HLS (`.m3u8`) via `hls.js` or fall back to the signed `/stream/` URL

To create test users:
- Go to http://127.0.0.1:8000/admin/
- Create a user and set `role` to `student` or `instructor`

## Notes
- The folder `backend_old_broken/` is an old mistaken scaffold kept only as a backup.
- Security reality constraints and options are in `docs/security.md`.
- Videos are NOT publicly served via `/media/...` anymore; playback must go through the signed `/stream/` URL.

## Optional: HLS (streaming segments)
This project supports serving HLS manifests/segments via signed URLs, but generating HLS requires **FFmpeg**.

1) Install FFmpeg (Windows)
- Install FFmpeg and ensure `ffmpeg -version` works in a new terminal.

2) Generate HLS for a lecture
```powershell
Push-Location server
c:/Users/zaido/OneDrive/Desktop/elearning/.venv/Scripts/python.exe manage.py transcode_hls <lecture_id>
```

Once a lecture is transcoded, `/api/lectures/{id}/playback/` will return the HLS manifest URL instead of `/stream/`.

## Optional: Postgres + Redis (local dev)
This project defaults to SQLite + in-memory cache. If you want Postgres/Redis locally:

1) Start containers (requires Docker Desktop)
```powershell
docker compose up -d
```

2) Create a local env file
- Copy `server/.env.example` to `server/.env`

3) Run migrations against Postgres
```powershell
Push-Location server
c:/Users/zaido/OneDrive/Desktop/elearning/.venv/Scripts/python.exe manage.py migrate
```
