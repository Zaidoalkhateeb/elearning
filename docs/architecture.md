# Architecture (Minimal Upload → Watch)

## 1) Components
- Web app (frontend): login, upload page (instructor), player page (student)
- Backend API: authentication + authorization + lecture metadata
- Database: store users + lecture metadata
- Object storage: store uploaded originals and/or transcoded outputs
- (Optional) Encoder/transcoder: generate HLS/DASH outputs

## 2) Minimal “secure playback” flow
1. Student requests a lecture page
2. Backend verifies student session
3. Backend returns a short-lived playback token (or signed manifest URL)
4. Player uses that token to fetch the manifest and media segments

## 3) Recommended video approach by security level
### Level A (basic, fastest)
- Store original file in object storage
- Serve via HTTPS with signed URLs
- Downside: not DRM; easier to capture

### Level B (recommended)
- Transcode to HLS
- Use signed URLs for manifest + segments
- Rotate/expire tokens frequently

### Level C (strongest practical)
- DRM-enabled streaming (DASH/HLS with EME)
- License server (Widevine/FairPlay/PlayReady)
- Optional watermarking

## 4) Single-session enforcement (no 2 devices)
- Store current session id/token id per user
- When user logs in:
  - invalidate previous session (or reject new login)
- For every API request and playback-token request:
  - verify it matches the active session id

## 5) What “encrypted while watching” means
- Always: HTTPS (transport encryption)
- Strong: DRM (content encryption + key control via license server)
