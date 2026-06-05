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
    },
    "zones": [
      {
        "id": "string — unique zone id",
        "x": 100, "y": 200,
        "w": 40, "h": 40,
        "states": {
          "state_name": {
            "color": "#hex",
            "label": "Text shown when nearby",
            "onInteract": { "type": "interact_type", "...fields" },
            "autoNext": "seconds to auto-advance (optional)"
          }
        },
        "initialState": "state_name"
      }
    ]
  },
  "controls": {
    "fingerMap": {
      "0": "jump | right | left | up | down | interact | none",
      "1": "jump | right | left | up | down | interact | none",
      "2": "jump | right | left | up | down | interact | none",
      "3": "jump | right | left | up | down | interact | none",
      "4": "jump | right | left | up | down | interact | none"
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
  },
  "events": [
    {
      "trigger": { "type": "trigger_type", ...trigger_fields },
      "actions": [
        { "type": "action_type", ...action_fields }
      ]
    }
  ],
  "countdown": 3,
  "levelDefaults": { "countdown": 3 },
  "levels": [
    {
      "name": "string — level name",
      "countdown": 3,
      "intro": { "title": "NIVEL 1", "subtitle": "El comienzo", "prompt": "SPACE / Toca para empezar" },
      "rules": { "winCondition": { "type": "score", "target": 300 } },
      "entities": { "enemies": { "count": 2, "speed": 60 } },
      "world": { "backgroundColor": "#0a2e1a" },
      "physics": { "gravity": { "y": 500 } },
      "events": [ ]
    }
  ]
}
```

## Levels System (multi-level games)

A game becomes multi-level just by adding a `levels` array to the config — **no DB
migration needed** (the whole config is stored as JSONB). Everything is optional and
backward compatible: a config **without** `levels` behaves exactly as a single-level game.

### How it flows
1. Player starts the game (StartScene) → **Level 1** begins (with its countdown).
2. When a level's `winCondition` is met → a **"NIVEL X"** announcement screen appears.
3. On SPACE / tap / finger → the next level begins, after its start-of-round countdown.
4. After the **last** level's win → the normal win/GameOver screen (total score across levels).
5. Losing retries the **current** level (its countdown runs again).

### Level object fields (all optional)
| Field | Description |
|-------|-------------|
| `name` | Shown as the subtitle on the "NIVEL X" screen and the "completed" banner |
| `countdown` | Seconds of `3·2·1·¡YA!` before this round starts (overrides `levelDefaults`/`countdown`) |
| `intro` | `{ title, subtitle, prompt, titleColor, subtitleColor, ... }` to style the announcement |
| `rules` | Per-level overrides — most importantly `winCondition` (deep-merged onto base `rules`) |
| `entities` | Per-level overrides for player/platforms/collectibles/enemies/zones (deep-merged) |
| `world` | Per-level overrides, e.g. `backgroundColor` (deep-merged) |
| `physics` | Per-level overrides, e.g. `gravity.y` (deep-merged) |
| `events` | Per-level events — **replaces** the base `events` array for that level |

**Merge semantics:** objects deep-merge onto the base config; **arrays replace** (so
`entities.platforms.positions` or `events` fully replace, they don't append). Sprites are
shared across all levels — define them once at the top-level `sprites`.

### Countdown ("timer al inicio de cada partida")
- Per level: `level.countdown`. Default for all levels: `levelDefaults.countdown`.
- Single-level games (no `levels`): top-level `countdown`.
- `0` (or omitted) disables it. Style via `screens.countdown` = `{ color, goColor, goText, size }`.

### Announcement screen styling
`screens.levelIntro` = `{ titleColor, subtitleColor, prompt, promptColor, backgroundColor, ... }`
sets defaults for all "NIVEL X" screens; each `level.intro` can override per level.

### Win conditions usable per level
`score` (≥ `target`), `collect_count` (≥ `target`), `collect_all` (all collectibles gone),
`time` (elapsed ≥ `seconds`), and `survive` (last until the `rules.timer` reaches 0 → win
instead of lose). Give each level its own `winCondition` so levels have distinct goals.

### Example: 3-level platformer
```json
"countdown": 3,
"levelDefaults": { "countdown": 3 },
"levels": [
  {
    "name": "Calentamiento",
    "rules": { "winCondition": { "type": "score", "target": 200 } },
    "entities": { "enemies": { "count": 0 } },
    "world": { "backgroundColor": "#12203a" }
  },
  {
    "name": "Se complica",
    "rules": { "winCondition": { "type": "score", "target": 400 } },
    "entities": { "enemies": { "count": 2, "speed": 60 }, "platforms": { "procedural": { "maxGap": 95 } } },
    "world": { "backgroundColor": "#1a0a2e" }
  },
  {
    "name": "Final",
    "countdown": 5,
    "intro": { "subtitle": "¡Último nivel! Aguanta 30s", "titleColor": "#ff5c8a" },
    "rules": { "winCondition": { "type": "survive" }, "timer": 30 },
    "entities": { "enemies": { "count": 4, "speed": 80, "ai": "chase" } },
    "world": { "backgroundColor": "#2e0a14" }
  }
]
```

## Events System

Events add dynamic behaviors to games. Each event has a **trigger** and one or more **actions**.

### Triggers
| Type | Fields | Description |
|------|--------|-------------|
| `timer` | `delay` (seconds), `repeat` (bool), `startAfter` (seconds, optional) | Fires every N seconds |
| `score` | `value` | Fires once when score >= value |
| `time` | `seconds` | Fires once when elapsed time >= seconds |
| `lives` | `value` | Fires once when lives <= value |
| `enemy_count` | `value` | Fires once when active enemies <= value |
| `collect_count` | `value` | Fires once when total collected >= value |

### Actions
| Type | Fields | Description |
|------|--------|-------------|
| `spawn` | `entity` (enemies/collectibles), `count`, `speed`, `ai`, `color`, `x`, `y` | Spawn entities at random or fixed positions |
| `set_property` | `target` (player/enemies), `property` (speed/ai/scale/jumpForce), `value` | Change a property on target |
| `flash_text` | `text`, `color`, `size`, `duration` (ms) | Show floating text that fades out |
| `shake_camera` | `duration` (ms), `intensity` (0.001-0.05) | Shake the camera |
| `tint` | `target` (player/enemies/collectibles), `color`, `duration` (ms) | Temporarily tint entities |
| `add_score` | `value` | Add to score (can be negative) |
| `add_lives` | `value` | Add lives (can be negative) |
| `set_timer` | `value` | Add seconds to game timer |
| `change_background` | `color` (#hex) | Change background color |

### Example events for a Pumpkin Panic style game:
```json
"events": [
  {
    "trigger": { "type": "timer", "delay": 20, "repeat": true },
    "actions": [
      { "type": "spawn", "entity": "enemies", "count": 2, "speed": 65, "ai": "chase" },
      { "type": "flash_text", "text": "MAS FANTASMAS!", "color": "#c8c8dc", "duration": 1500 }
    ]
  },
  {
    "trigger": { "type": "score", "value": 500 },
    "actions": [
      { "type": "flash_text", "text": "PELIGRO!", "color": "#ff0000", "size": "14px" },
      { "type": "shake_camera", "duration": 400, "intensity": 0.015 },
      { "type": "set_property", "target": "enemies", "property": "speed", "value": 100 }
    ]
  },
  {
    "trigger": { "type": "lives", "value": 1 },
    "actions": [
      { "type": "flash_text", "text": "ULTIMA VIDA!", "color": "#ff5c8a" },
      { "type": "tint", "target": "player", "color": "#ff0000", "duration": 3000 }
    ]
  }
]
```

## Zones System (Interactable Areas)

Zones are areas the player can interact with by pressing E (keyboard) or the `interact` finger action. Each zone has **states** with visual changes, labels, and interaction behaviors.

### Zone interact types
| Type | Fields | Description |
|------|--------|-------------|
| `give_item` | `item` (string) | Give an item to player inventory |
| `need_item` | `item`, `consume` (bool) | Require player to have item; advance state |
| `next_state` | — | Simply advance to next state |
| `harvest` | `score`, `resetTo` (state name) | Give score and reset zone to a state |
| `unlock` | `cost` (score points) | Spend score to unlock (advance state) |

### State properties
- `color` — hex color for the zone rectangle
- `label` — text shown when player is nearby
- `onInteract` — what happens when player presses interact
- `autoNext` — seconds to automatically advance to next state (for growing plants, charging, etc.)

### Example: farming game zone
```json
{
  "id": "plot1",
  "x": 80, "y": 200, "w": 48, "h": 48,
  "states": {
    "empty":   { "color": "#5b3a29", "label": "Sembrar [E]", "onInteract": { "type": "next_state" } },
    "planted": { "color": "#6b8c3f", "label": "Regar [E]", "onInteract": { "type": "need_item", "item": "water", "consume": true } },
    "watered": { "color": "#2d5a1e", "label": "Creciendo...", "autoNext": 12 },
    "grown":   { "color": "#ff6b1a", "label": "Cosechar! [E]", "onInteract": { "type": "harvest", "score": 100, "resetTo": "empty" } }
  },
  "initialState": "empty"
}
```

### Other zone ideas (generic)
- **Chest**: locked → unlocked (cost) → open (give_item)
- **Door**: closed → open (need_item: key)
- **NPC**: talk → quest_given → quest_complete (score)
- **Switch**: off → on (triggers event)
- **Crafting station**: empty → has_item (need_item) → crafted (give_item)

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

## Emulator (Retro) Games via Nostalgist.js

Besides the Phaser-rendered therapeutic games above, the platform supports **retro
emulator games** (NES, SNES, Game Boy, GBA, Genesis, …) run in the browser with
[Nostalgist.js](https://nostalgist.js.org). **Everything is config-driven** — to add a
new ROM game you do **NOT** touch code: just create a `games` row with
`metadata.type = "emulator"` plus an `emulator` block and a `controls.fingerMap`.

The generic pieces that make this work (already in place, shared by every emulator game):
- `games/emulator/template.html` — the generic play screen (camera, finger config, fullscreen).
- `static/js/emulator-loader.js` — reusable `EmulatorGame` loader (launches Nostalgist, maps fingers→buttons, resizes canvas).
- Registry key `emulator` in `games/registry.py` → renders `games/emulator/template.html`.
- ROMs are served from `games/` at `/static/games/...` (e.g. put files in `games/emulator/roms/`).

> The legacy `smb3` game keeps its own dedicated template/bridge — leave it as is.
> New emulator games should use the generic `type: "emulator"` path.

### Steps to add a new emulator game
1. **Place the ROM** somewhere served statically, e.g. `games/emulator/roms/contra.nes`
   (becomes `emulator/roms/contra.nes` for the `rom` field). A full `http(s)://` URL also works.
2. **Pick the libretro core** for the console (see table below).
3. **POST the game config** with `metadata.type = "emulator"`, the `emulator` block, and `controls.fingerMap`.

### Emulator game config schema
```json
{
  "version": "1.0",
  "metadata": {
    "name": "Contra (NES)",
    "type": "emulator",
    "targetFingers": [0, 1, 2, 3, 4],
    "difficulty": "medium",
    "description": "string",
    "estimatedDuration": 1800
  },
  "emulator": {
    "core": "fceumm",                 
    "rom": "emulator/roms/contra.nes",
    "aspectRatio": "256/240",         
    "tapButtons": ["start", "select"],
    "options": {}                     
  },
  "controls": {
    "fingerMap": {
      "0": "left", "1": "a", "2": "right", "3": "b", "4": "start"
    },
    "keyboardFallback": true
  }
}
```

- **`core`** — libretro core name (Nostalgist downloads it automatically).
- **`rom`** — path under `/static/games/` (e.g. `emulator/roms/x.nes`) or a full URL.
- **`aspectRatio`** — `"w/h"` string, `[w, h]` array, or a number. Defaults to `4/3`.
- **`tapButtons`** — buttons pressed once on finger-close instead of held (good for `start`/`select`). Default `["start","select"]`.
- **`options`** — extra options forwarded verbatim to `Nostalgist.launch()` (advanced).

### fingerMap for emulator games (RetroPad buttons)
Unlike Phaser games (which map to semantic actions like `jump`/`right`), emulator games map
each finger **directly to a RetroPad button**. Valid button names:

`up`, `down`, `left`, `right`, `a`, `b`, `x`, `y`, `l`, `r`, `l2`, `r2`, `select`, `start`, `none`

### Libretro core reference
| Console | Core (`core`) | Typical aspectRatio | ROM ext |
|---------|---------------|---------------------|---------|
| NES | `fceumm` (or `nestopia`) | `256/240` | `.nes` |
| SNES | `snes9x` | `256/224` | `.sfc` / `.smc` |
| Game Boy / Color | `gambatte` | `160/144` | `.gb` / `.gbc` |
| Game Boy Advance | `mgba` | `240/160` | `.gba` |
| Sega Genesis / Mega Drive | `genesis_plus_gx` | `320/224` | `.md` / `.bin` |
| Arcade | `fbneo` (or `mame2003_plus`) | varies | `.zip` |

### Example: create an NES game
```bash
curl -s -X POST http://localhost:5000/api/games \
  -H "Content-Type: application/json" -b /tmp/pixo-cookie \
  -d '{
    "name": "Contra (NES)",
    "description": "Run & gun clásico de NES, controlado por gestos.",
    "game_type": "emulator",
    "config": {
      "version": "1.0",
      "metadata": { "name": "Contra (NES)", "type": "emulator", "targetFingers": [0,1,2,3,4], "difficulty": "hard", "estimatedDuration": 1800 },
      "emulator": { "core": "fceumm", "rom": "emulator/roms/contra.nes", "aspectRatio": "256/240", "tapButtons": ["start","select"] },
      "controls": { "fingerMap": { "0": "left", "1": "a", "2": "right", "3": "b", "4": "start" }, "keyboardFallback": true }
    }
  }'
```

> **Note (multi-hand):** the configurable multi-hand feature applies **only to Phaser
> games**. Emulator games are single-hand (one RetroPad), so use the flat `fingerMap`
> (object) and flat `sensitivities` (`[50,50,50,50,50]`) shapes.

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
