# Security Notes (Practical)

This doc explains what is and isn’t possible for your requirements, and what tech choices map to them.

## 1) “Student can’t download the lecture”
### What we can do
- Never expose the original upload URL to students.
- Stream using HLS/DASH (many small segments), not a single MP4.
- Require signed URLs / short-lived tokens for:
  - the manifest file (playlist)
  - every media segment
- Rate-limit segment access and require authentication.

### Reality
- A determined user can still capture *what they can watch* (screen capture, camera capture).
- “No download” is best-effort unless DRM is used.

## 2) “Screen recording shows black screen”
### Reality (important)
- In standard web browsers you cannot guarantee this universally.
- You can reduce software capture in some environments, but there are always bypasses:
  - external camera
  - HDMI capture
  - rooted/jailbroken devices, etc.

### Strongest practical option
- DRM-protected playback (Widevine/FairPlay/PlayReady) + secure player
- Watermarking (visible or forensic) to discourage leaks

## 3) “Encrypted while watching”
### Minimum
- HTTPS/TLS so traffic is encrypted in transit.

### What you likely mean
- DRM-grade encryption where media is encrypted at rest and in delivery, and only decrypted in a protected player with a license.

## 4) “No 2 people using the same account at the same time”
### Implementable (backend)
- Single active session per user.
- On login:
  - either kick the previous session, OR reject the new login.
- On every API call/playback-token request:
  - check that the session matches the current active session.

### Notes
- For video playback, ensure the manifest/segment tokens are bound to the active session.

## 5) Recommended MVP security baseline
- JWT auth + refresh tokens
- Signed playback tokens (very short TTL)
- HLS streaming (not direct MP4)
- Single-session enforcement

## 6) If you want “Muvi-level” security
You’ll end up needing:
- DRM
- watermarking
- a managed video pipeline (or build license server + packaging)
