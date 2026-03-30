# What’s Done Till Now (Detailed)

## 1. Documentation & Planning
- **PRD, Architecture, Security docs**: Minimal product requirements, architecture, and security constraints written in `docs/`.
- **Security notes**: Documented realistic browser security limits (no true screen-record block, but single-session, signed URLs, and HLS implemented).

## 2. Backend API (Django 5 + DRF)
- **Custom User model**: Roles (`student`, `instructor`), single-session enforced via `token_version`.
- **JWT Auth**: SimpleJWT, extended to invalidate old tokens on new login.
- **Lecture model**: Title, video file, uploaded_by, HLS fields.
- **API endpoints**:
  - `/api/auth/token/` — login, returns JWT
  - `/api/lectures/` — list (all), upload (instructor only)
  - `/api/lectures/<id>/playback/` — returns signed playback URL (HLS or direct stream)
  - `/api/lectures/<id>/stream/` — signed, short-lived video streaming (with HTTP Range)
  - `/api/lectures/<id>/hls/manifest/` — signed HLS manifest (rewrites segment URLs)
  - `/api/lectures/<id>/hls/asset/<path>/` — signed HLS segment delivery
  - `/api/lectures/<id>/transcode_hls/` — instructor-only, triggers HLS transcoding

## 3. Instructor UI
- **Upload page**: `/upload/` — login, pick title + file, uploads to `/api/lectures/`.
- **Lecture list**: `/lectures/` — login, see all lectures, each with:
  - “Watch” link (opens `/watch/?lecture_id=...`)
  - “Transcode HLS” button (instructor only, calls new API)

## 4. Student UI
- **Watch page**: `/watch/` — login, enter lecture id (or use link from list), plays video using HLS.js if available, falls back to direct stream.

## 5. HLS Pipeline
- **FFmpeg integration**: Management command and API endpoint to transcode uploaded videos to HLS (segments + manifest).
- **Signed URLs**: All playback and segment access is via short-lived signed URLs, not public media.

## 6. Security & Hardening
- **Single-session**: Only one active login per user (JWTs invalidated on new login).
- **No direct media URLs**: All video access is via signed endpoints.
- **HLS segment path traversal protection**: Only allows safe segment access.
- **Optional Postgres/Redis**: Docker Compose and `.env` support for production-like local dev.

## 7. Dev & Infra
- **README**: Full run instructions, API, and UI usage.
- **Docker Compose**: For Postgres/Redis (optional).
- **FFmpeg**: Windows install instructions, used for HLS.

---

**Next steps could include:**
- More UI polish (list lectures for students, upload progress, etc.)
- Rate limiting, CORS/CSRF hardening
- Production deployment (gunicorn, static files, etc.)
- Multi-bitrate HLS, watermarking, or DRM (if needed)
