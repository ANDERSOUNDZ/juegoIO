# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time hand finger tracking system using OpenCV + MediaPipe that stores finger states in PostgreSQL and serves a Doodle Jump-style platformer game controlled by hand gestures via a Flask web server.

## Architecture

**Single-server monolith** — `server.py` runs everything in one process:

- **Camera thread** (`camera_loop`): Opens local webcam via `cv2.VideoCapture(0)`, runs MediaPipe HandLandmarker in VIDEO mode, detects 5 finger states (up/down), draws landmarks on frame, encodes to JPEG, and shares via thread-safe globals (`frame_atual`, `dedos_atual`).
- **DBWorker**: Async queue-based worker thread that inserts finger states into PostgreSQL (`control_juego` table). Sends on state change or every 200ms heartbeat.
- **Flask routes**: `/` serves the game UI, `/video_feed` streams MJPEG frames, `/finger_data` returns current finger JSON, `/set_nivel/<n>` changes difficulty.
- **Client** (`templates/index.html`): Displays video stream via `<img>` tag pointing to `/video_feed`, polls `/finger_data` for game input, renders a canvas-based platformer.

Key design detail: the camera runs on the **server side** — the server captures its own webcam and streams processed frames to clients. Clients do not send video.

## Commands

```bash
# Start PostgreSQL + pgAdmin
docker compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Run the server (starts camera + Flask on port 5000)
python server.py

# Stop Docker services (preserve data)
docker compose down

# Stop Docker services and delete DB data
docker compose down -v

# Access DB directly
docker compose exec postgres psql -U postgres -d mario_db
```

## Database

PostgreSQL 16 via Docker. DB `mario_db`, table `control_juego` with columns: `id`, `timestamp`, `nivel` (1-5), `pulgar`, `indice`, `medio`, `anular`, `menique` (0/1 each). pgAdmin available at `localhost:5050` (admin@admin.com / admin).

Connection config is hardcoded at top of `server.py` (localhost:5432, postgres/admin).

## Game Controls

Thumb up = jump, index up = move right, middle up = move left. Keyboard arrows also work. Keys 1-5 change difficulty level, R restarts.
