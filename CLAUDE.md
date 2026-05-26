# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PIXO Therapy** — Therapeutic game platform for children/people with finger mobility issues. Games are controlled by hand gestures via MediaPipe hand tracking. Therapists manage patients, configure sensitivity, run game sessions, and track progress.

## Architecture

**Flask monolith** with modular package structure:

```
app/
  __init__.py          # App factory (create_app)
  config.py            # DB config, constants
  models.py            # SQLAlchemy models (User, Patient, Game, GameSession, etc.)
  auth.py              # Login/register (flask-login, session-based)
  routes.py            # Page routes (dashboard, patients, games, play, reports)
  db_worker.py         # Async queue worker for high-freq DB inserts
  hand_tracking.py     # MediaPipe detection logic
  ws.py                # WebSocket handler (hand tracking + session events)
  api/
    patients.py        # CRUD + sensitivity management
    games.py           # CRUD (JSON config storage)
    sessions.py        # Session lifecycle + reports
    sensitivity.py     # Presets management
templates/             # Jinja2 templates (multi-page, not SPA)
static/
  css/platform.css     # Retro pixel art theme
  js/
    hand-input.js      # Reusable WebSocket client for hand tracking
    game-loader.js     # Phaser 3 JSON config interpreter
```

### Key Design Decisions
- **SQLAlchemy for CRUD** + raw psycopg2 `DBWorker` for high-frequency finger events
- **Games as JSON configs** in DB, interpreted at runtime by Phaser 3 `game-loader.js`
- **Users table with roles** (therapist, admin, viewer) instead of separate tables
- **Multi-page with Flask templates**, JS per page, not SPA
- **Legacy game** preserved at `/legacy` route

## Commands

```bash
# Start PostgreSQL + pgAdmin
docker compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Run the server (starts Flask on port 5000)
python server.py

# Stop Docker services
docker compose down

# Stop and delete DB data
docker compose down -v

# Access DB directly
docker compose exec postgres psql -U postgres -d mario_db
```

## Database

PostgreSQL 16 via Docker. DB `mario_db`. Key tables:
- `users` — therapists/admins with roles
- `patients` — linked to therapist user
- `games` — JSON config (JSONB) defining complete Phaser game
- `game_sessions` — patient + game + therapist + score
- `finger_events` — per-finger state + landmark coordinates
- `sensitivity_presets` — system/custom presets (Principiante, Intermedio, Avanzado)
- `patient_sensitivity` — current config per patient
- `sensitivity_history` — audit trail of sensitivity changes
- `control_juego` — legacy table (backward compat)

Schema in `../schema.sql`, auto-loaded by Docker on first run.

## Game Engine

Games are defined as JSON configs stored in `games.config` (JSONB). The `game-loader.js` interprets these configs and creates Phaser 3 games at runtime.

Supported game types: `platformer`, `catch`, `topdown`, `target`

Use `/create-game` skill to generate games via AI.

## Game Controls

Hand tracking via WebSocket: client captures webcam → sends frames → server processes with MediaPipe → returns finger states + annotated frame. Keyboard fallback available.

Sensitivity is configurable per-finger (0-100), per-patient, with presets and change history.
