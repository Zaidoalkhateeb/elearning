# Minimal eLearning Platform — PRD (Draft)

Date: 2026-03-30

## 1) Product goal
Build a minimal website where:
- Instructor uploads lecture videos (files).
- Student watches lecture videos (streaming/playback only).

No courses, sections, quizzes, payments, live classes, analytics, or anything else.

## 2) Roles
- Instructor
  - Can upload lecture video files.
- Student
  - Can view/play lectures.

## 3) Core user flows
### 3.1 Instructor
1. Login
2. Upload a lecture video file
3. See the lecture listed (title + status)

### 3.2 Student
1. Login
2. Open a lecture
3. Watch (play/pause/seek)

## 4) Data model (minimal)
- User
  - role: `instructor` | `student`
- Lecture
  - title
  - uploaded_by (instructor)
  - storage key (where the video lives)
  - playback manifest URL (for HLS/DASH)
  - created_at

## 5) Security requirements (requested)
### 5.1 Student can’t download
Goal: prevent downloading the *original upload* and make “Save video as…” impractical.

### 5.2 Screen recording shows black
Goal: if a student tries to screen record, recording captures black video.

### 5.3 Encrypted while watching
Goal: encrypted in transit (HTTPS) + encrypted media segments (DRM-grade if possible).

### 5.4 No simultaneous logins
Goal: same account can’t be used by 2 devices at the same time.

## 6) Reality constraints (important)
- In a normal web browser, you cannot 100% guarantee stopping screen recording in all cases.
  - Even if the browser blocks software screen capture, a user can record with an external camera or HDMI capture.
- What you *can* do is raise the bar:
  - DRM (Widevine/FairPlay/PlayReady) to protect the stream keys
  - Signed URLs + short-lived tokens
  - Watermarking (visible or forensic)
  - Single-session enforcement

## 7) MVP deliverables
- Backend API: auth + instructor upload + student playback authorization
- Storage: object storage (S3/R2)
- Streaming: HLS or DASH output (prefer HLS to start)
- Player: web player page (with auth)
