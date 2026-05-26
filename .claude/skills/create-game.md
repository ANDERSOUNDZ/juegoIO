---
name: create-game
description: Generate a therapeutic game config from a natural language description and save it to the database
user_invocable: true
---

# /create-game

Generate a therapeutic game for the PIXO Therapy platform from a natural language description.

## Instructions

The user will describe a game they want. You must:

1. **Parse the description** for:
   - Game type: `platformer` (gravity, climb up), `runner` (auto-scroll down, survive), `catch` (falling objects), `topdown` (no gravity, free movement), `target` (click/tap targets)
   - Target fingers (which fingers the game exercises)
   - Difficulty level
   - Theme/visual style
   - Special mechanics (enemies, timers, obstacles)

2. **Generate a valid game config JSON** following the schema below.

3. **Save it to the database** by running:
   ```bash
   curl -s -X POST http://localhost:5000/api/games \
     -H "Content-Type: application/json" \
     -b "session=<cookie>" \
     -d '<json_payload>'
   ```

   If auth is needed, first register/login:
   ```bash
   curl -s -c /tmp/pixo-cookie -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@pixo.com","password":"admin"}'
   ```

4. **Report the result** with game ID and summary.

## Game Config JSON Schema

```json
{
  "version": "1.0",
  "metadata": {
    "name": "string — game name",
    "type": "platformer | catch | topdown | target",
    "targetFingers": [0, 1, 2],
    "difficulty": "easy | medium | hard",
    "description": "string",
    "estimatedDuration": 300
  },
  "physics": {
    "type": "arcade",
    "gravity": { "x": 0, "y": 0-800 },
    "debug": false
  },
  "world": {
    "width": 400,
    "height": 600,
    "backgroundColor": "#hex",
    "camera": {
      "follow": "player",
      "scrollY": true,
      "scrollX": false
    }
  },
  "entities": {
    "player": {
      "spawn": { "x": 200, "y": 500 },
      "width": 20,
      "height": 26,
      "color": "#hex",
      "speed": 50-400,
      "jumpForce": -200 to -600,
      "physics": {
        "bounce": 0-1,
        "collideWorldBounds": true
      }
    },
    "platforms": {
      "static": true,
      "color": "#hex",
      "width": 80,
      "height": 14,
      "layout": "procedural | fixed",
      "procedural": {
        "count": 5-30,
        "minGap": 30-60,
        "maxGap": 50-120,
        "minWidth": 40-80,
        "maxWidth": 80-200
      },
      "positions": [
        { "x": 200, "y": 500, "w": 100, "h": 14 }
      ]
    },
    "collectibles": {
      "color": "#hex",
      "spawnRate": 0.1-0.8,
      "scoreValue": 10-500
    },
    "enemies": {
      "count": 0-20,
      "color": "#hex",
      "width": 16,
      "height": 16,
      "ai": "patrol | chase",
      "speed": 20-200
    }
  },
  "controls": {
    "fingerMap": {
      "0": "jump | right | left | none",
      "1": "jump | right | left | none",
      "2": "jump | right | left | none",
      "3": "jump | right | left | none",
      "4": "jump | right | left | none"
    },
    "keyboardFallback": true
  },
  "sprites": {
    "player":     { "sprite_id": 1 },
    "platform":   { "sprite_id": 2 },
    "coin":       { "sprite_id": 3 },
    "enemy":      { "sprite_id": 4 },
    "background": { "sprite_id": 5 }
  },
  "rules": {
    "winCondition": {
      "type": "score | survive | collect_all",
      "target": 1000
    },
    "loseCondition": {
      "type": "fall_off | off_screen | timer | lives"
    },
    "lives": 1-5,
    "timer": null or seconds
  }
}
```

## Sprites System

Games reference reusable sprites from the `sprites` table via `sprite_id`. The `sprites` field is **optional** — if omitted, the game renders with colored rectangles (fallback).

### Sprite types:
- **pixelmap**: Pixel art defined as palette + grid arrays, rendered via canvas at runtime
- **image**: URL to PNG/SVG image file

### Creating sprites:
Before creating a game with sprites, first create the sprites via the API:
```bash
curl -s -X POST http://localhost:5000/api/sprites \
  -H "Content-Type: application/json" \
  -b /tmp/pixo-cookie \
  -d '{
    "name": "Pixo Hero",
    "category": "player",
    "type": "pixelmap",
    "width": 20,
    "height": 26,
    "frame_count": 4,
    "data": {
      "palette": ["#3ddc97", "#1f7a4f", "#f4c896", "#ffd23f", "#7a3ac8", "#2a1a0a"],
      "frames": [
        { "grid": ["..........row of hex indices...", "..."] },
        { "grid": ["...frame 2..."] }
      ]
    }
  }'
```

### Pixelmap grid format:
- Each row is a string, each character is a hex index (0-f) into the palette
- `.` = transparent pixel
- Example: `"..00110011.."` with palette `["#ff0000", "#00ff00"]` → red and green pixels

### Listing available sprites:
```bash
curl -s http://localhost:5000/api/sprites?category=player -b /tmp/pixo-cookie
```

### Sprite roles in config:
- `player` — the character (supports frame_count for animation: idle, run frames, jump)
- `platform` — tiled horizontally across platform width
- `coin` — animated spin (frame_count frames)
- `enemy` — enemy character
- `background` — tiled as parallax scrolling background

If the user doesn't mention sprites, omit the `sprites` field entirely. If they want visual themes, create appropriate sprites first, then reference them in the game config.

## Design Guidelines for Therapeutic Games

- **Principiante**: Large platforms, slow speed, few/no enemies, generous gaps, high sensitivity fingers
- **Intermedio**: Medium platforms, moderate speed, some enemies, standard gaps
- **Avanzado**: Small platforms, fast speed, many enemies, tight gaps, low sensitivity

### Finger-specific exercises:
- **Pulgar (0)**: Map to jump — exercises thumb extension
- **Índice (1)**: Map to right movement — exercises index finger extension
- **Medio (2)**: Map to left movement — exercises middle finger extension
- **Anular (3)**: Map to an action — exercises ring finger (hardest for most patients)
- **Meñique (4)**: Map to an action — exercises pinky extension

### Game type recommendations:
- **platformer**: Best for thumb + index/middle. Jump + lateral movement.
- **catch**: Best for index + middle. Move left/right to catch falling items.
- **topdown**: Best for all fingers. 4-directional movement.
- **runner**: Best for thumb + index/middle. Auto-scroll down, jump between platforms to survive. Uses `camera.autoScroll`, `loseCondition: "off_screen"`.
- **target**: Best for individual finger isolation. Each finger triggers an action on a specific zone.

## Examples

### Input: "Un juego para ejercitar índice y medio, fácil, sin enemigos"
→ Type: `catch`, fingerMap: index=right, middle=left, no enemies, slow speed, big player

### Input: "Platformer difícil con enemigos para todos los dedos"
→ Type: `platformer`, all fingers mapped, many enemies, fast speed, small platforms

### Input: "Juego relajado top-down para practicar el anular"
→ Type: `topdown`, ring finger mapped to a key action, no enemies, slow, big world
