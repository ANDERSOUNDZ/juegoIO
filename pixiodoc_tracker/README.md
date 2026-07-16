# PIXO Therapy — Plataforma de Juegos Terapéuticos

Plataforma de rehabilitación motriz basada en juegos controlados por gestos de la mano. Utiliza **MediaPipe Hand Tracking** para detectar la posición de los 5 dedos en tiempo real, permitiendo a terapeutas gestionar pacientes, configurar sensibilidad, ejecutar sesiones de juego y monitorear la evolución mediante **métricas de rehabilitación** con reportes PDF descargables.

---

## ¿Qué necesitas instalar?

**Solo una cosa:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

No necesitas Python, Node.js, PostgreSQL, ni descargar nada a mano.

### Cómo empezar (2 comandos)

```powershell
git clone -b completo https://github.com/ANDERSOUNDZ/juegoIO.git
cd juegoIO/pixiodoc_tracker
docker compose up -d
```

Ese único comando (`docker compose up -d`) descarga e instala **todo** automáticamente:

| Docker descarga | Propósito |
|----------------|-----------|
| Python 3.11 + pip | Lenguaje del servidor |
| Flask, SQLAlchemy, WeasyPrint… | Librerías del backend |
| PostgreSQL 16 | Base de datos (pacientes, sesiones, eventos) |
| Phaser 3 + MediaPipe + Fomantic UI + Chart.js + Nostalgist.js | Librerías del frontend (~22 MB, incluidas en el repo) |
| Hand Landmarker model | Modelo de IA para detectar dedos (~7.5 MB, incluido en el repo) |

**Todo queda dentro de Docker.** No instalas nada en tu PC. Solo abres http://localhost:5001 y usas la web.

> **Nota:** Los archivos vendor (Phaser, MediaPipe, etc.) ya vienen incluidos en el repositorio. No se necesita `--build` para descargarlos. El build solo se necesita si modificas el código fuente. Para uso normal basta `docker compose up -d`.

---

## Índice

- [Stack Tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Modelos de Datos](#modelos-de-datos)
- [API REST](#api-rest)
- [WebSocket — Hand Tracking](#websocket--hand-tracking)
- [Motor de Juego (Phaser 3)](#motor-de-juego-phaser-3)
- [Analytics de Rehabilitación](#analytics-de-rehabilitación)
- [Reporte PDF](#reporte-pdf)
- [Frontend](#frontend)
- [Docker](#docker)
- [Inicio Rápido](#inicio-rápido)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Comandos Útiles](#comandos-útiles)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.11+, Flask 3.x |
| **ORM** | SQLAlchemy 2.x + Flask-SQLAlchemy |
| **DB directa** | psycopg2-binary (inserciones de alta frecuencia) |
| **Base de datos** | PostgreSQL 16 (Docker) |
| **Autenticación** | Flask-Login (sesiones) |
| **WebSocket** | Flask-Sock |
| **Hand Tracking** | MediaPipe Hands WASM (@mediapipe/hands CDN) en el navegador |
| **Frontend** | Jinja2, Phaser 3.80.1 (CDN), Chart.js 4 |
| **CSS** | Framework propio retro pixel art (Press Start 2P) |
| **PDF** | WeasyPrint (HTML → PDF, en Docker) |
| **Contenedores** | Docker Compose (3 servicios: web + postgres + pgadmin) |

---

## Arquitectura

El proyecto sigue **Clean Architecture** (Arquitectura Hexagonal) con 3 capas principals:

```
┌──────────────────────────────────────────────────────────────┐
│                     Navegador (Cliente)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Cámara + │  │ HandInput│  │ Phaser 3 │  │ Templates  │  │
│  │ MediaPipe│──│ (WS)     │──│ Juego    │  │ (Jinja2)   │  │
│  └──────────┘  └────┬─────┘  └──────────┘  └──────┬─────┘  │
│                     │                              │         │
└─────────────────────┼──────────────────────────────┼─────────┘
                      │ WebSocket                    │ HTTP
┌─────────────────────┼──────────────────────────────┼─────────┐
│             Aplicación Flask                        │         │
│  ┌──────────────────┴──────────────────────────────┴──────┐  │
│  │           INFRASTRUCTURE (Controladores)                 │  │
│  │  auth │ patients │ games │ sessions │ sensitivity       │  │
│  │  sprites │ analytics │ ws (WS) │ pages (HTML)           │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │           APPLICATION (Servicios)                        │  │
│  │  PatientService │ GameService │ SessionService           │  │
│  │  SensitivityService │ SpriteService │ AnalyticsService   │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │           DOMAIN (Entidades + Interfaces)                │  │
│  │  User │ Patient │ Game │ GameSession │ FingerEvent       │  │
│  │  SensitivityPreset │ Sprite │ Repository interfaces     │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │     INFRASTRUCTURE (Persistencia + Web)                  │  │
│  │  SQLAlchemy Models → Repository Impl → PostgreSQL        │  │
│  │  DBWorker (hilo async para inserts de alta frecuencia)   │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Capa de Dominio (`src/domain/`)

Entidades puras (dataclasses) sin dependencias externas, value objects inmutables, e interfaces abstractas para repositorios.

| Archivo | Contenido |
|---------|-----------|
| `entities.py` | 10 entidades: User, Patient, Game, GameSession, FingerEvent, SensitivityPreset, PatientSensitivity, SensitivityHistory, PlayerGameConfig, Sprite |
| `value_objects.py` | FingerState (5 tupla 0/1), Sensitivity (5 tupla 0-100), HandLandmark, HandLandmarks |
| `exceptions.py` | DomainError, NotFoundError, ValidationError |
| `interfaces/repositories.py` | 9 interfaces abstractas (ABC) para repositorios |
| `interfaces/hand_tracker.py` | Interfaz IHandTracker |

### Capa de Aplicación (`src/application/`)

Servicios que orquestan la lógica de negocio, dependen de interfaces del dominio.

| Servicio | Responsabilidad |
|----------|----------------|
| `patient_service.py` | CRUD pacientes + gestión de sensibilidad + historial |
| `game_service.py` | CRUD juegos + configuración por paciente |
| `session_service.py` | CRUD sesiones + finger events + reportes |
| `sensitivity_service.py` | Presets de sensibilidad |
| `sprite_service.py` | CRUD sprites + batch lookup |
| `analytics_service.py` | Métricas de rehabilitación, interpretación clínica, datos para PDF |

### Capa de Infraestructura (`src/infrastructure/`)

Implementaciones concretas de interfaces, adaptadores de frameworks.

| Subcarpeta | Contenido |
|------------|-----------|
| `persistence/models.py` | 9 modelos SQLAlchemy + instancia `db` |
| `persistence/repositories.py` | Implementaciones concretas de repositorios |
| `persistence/db_worker.py` | Worker async para inserts de finger_events |
| `web/controllers/` | 8 controladores Flask (auth, patients, games, sessions, sensitivity, sprites, analytics, pages) |
| `web/controllers/ws.py` | Manejador WebSocket `/ws` |
| `web/app.py` | Fábrica Flask `create_app()` |
| `web/middleware.py` | Manejadores de error 404, 500, DomainError |

---

## Modelos de Datos

### Tabla: `users`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `email` | VARCHAR(255) UNIQUE | |
| `password_hash` | VARCHAR(255) | |
| `name` | VARCHAR(100) | |
| `role` | VARCHAR(30) | `therapist` \| `admin` \| `viewer` |
| `created_at` | TIMESTAMPTZ | |

### Tabla: `patients`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `user_id` | INT FK → users | Terapeuta responsable |
| `name` | VARCHAR(100) | |
| `age` | INT | |
| `diagnosis` | TEXT | Diagnóstico médico |
| `notes` | TEXT | Notas del terapeuta |
| `created_at` | TIMESTAMPTZ | |

### Tabla: `games`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `name` | VARCHAR(100) | |
| `description` | TEXT | |
| `game_type` | VARCHAR(50) | `platformer` \| `catch` \| `topdown` \| `target` |
| `thumbnail_url` | TEXT | |
| `config` | JSONB | Definición completa del juego (entidades, física, reglas, sprites) |
| `created_by` | INT FK → users | |
| `created_at` | TIMESTAMPTZ | |

### Tabla: `game_sessions`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `patient_id` | INT FK → patients CASCADE | |
| `game_id` | INT FK → games | |
| `user_id` | INT FK → users | Terapeuta que supervisó |
| `started_at` | TIMESTAMPTZ | |
| `ended_at` | TIMESTAMPTZ | |
| `score` | INT | Puntaje obtenido |
| `metadata` | JSONB | Metadatos adicionales |

### Tabla: `finger_events`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL PK | |
| `session_id` | INT FK → game_sessions CASCADE | |
| `timestamp` | TIMESTAMPTZ | |
| `finger_index` | INT 0-4 | 0=Pulgar, 1=Índice, 2=Medio, 3=Anular, 4=Meñique |
| `state` | INT 0/1 | 0=abajo, 1=arriba |
| `landmark_x` | FLOAT | Coordenada X normalizada del landmark |
| `landmark_y` | FLOAT | Coordenada Y normalizada |
| `landmark_z` | FLOAT | Coordenada Z normalizada |
| `confidence` | FLOAT | Confianza de detección |

### Tabla: `sensitivity_presets`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `name` | VARCHAR(100) | Ej: "Principiante", "Intermedio", "Avanzado" |
| `description` | TEXT | |
| `difficulty_level` | VARCHAR(50) | |
| `sensitivities` | JSONB | Array [5] de 0-100 |
| `is_default` | BOOLEAN | |
| `created_by` | INT FK → users | |
| `created_at` | TIMESTAMPTZ | |

### Tabla: `patient_sensitivity`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `patient_id` | INT FK → patients UNIQUE CASCADE | |
| `sensitivities` | JSONB | Array [5] de 0-100 |
| `based_on_preset` | INT FK → sensitivity_presets | |
| `updated_at` | TIMESTAMPTZ | |
| `updated_by` | INT FK → users | |

### Tabla: `sensitivity_history`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `patient_id` | INT FK → patients CASCADE | |
| `old_sensitivities` | JSONB | Valores anteriores |
| `new_sensitivities` | JSONB | Valores nuevos |
| `reason` | TEXT | Motivo del cambio |
| `changed_by` | INT FK → users | |
| `changed_at` | TIMESTAMPTZ | |

### Tabla: `player_game_config`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `patient_id` | INT FK → patients CASCADE | |
| `game_id` | INT FK → games CASCADE | |
| `sensitivities` | JSONB | Array [5] de 0-100 |
| `finger_map` | JSONB | Mapa dedo→acción: `{"0":"jump","1":"right","2":"left","3":"none","4":"none"}` |
| `updated_at` | TIMESTAMPTZ | |
| UNIQUE | `(patient_id, game_id)` | |

### Tabla: `sprites`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL PK | |
| `name` | VARCHAR(100) | |
| `category` | VARCHAR(30) | `player` \| `platform` \| `coin` \| `enemy` \| `background` \| `other` |
| `type` | VARCHAR(20) | `pixelmap` \| `image` |
| `width` | INT | |
| `height` | INT | |
| `data` | JSONB | Frames pixelmap: `{palette: [...], frames: [{grid: [...]}]}` |
| `image_url` | TEXT | URL para tipo `image` |
| `frame_count` | INT | |
| `created_by` | INT FK → users | |
| `created_at` | TIMESTAMPTZ | |

---

## API REST

### Autenticación (Blueprint: `auth`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET/POST | `/login` | Login HTML | No |
| GET/POST | `/register` | Registro HTML | No |
| GET | `/logout` | Logout | Sí |
| POST | `/api/auth/login` | Login JSON → `{id, name, email, role}` | No |
| POST | `/api/auth/register` | Registro JSON → `{id, name, email, role}` | No |
| POST | `/api/auth/logout` | Logout JSON | Sí |

### Pacientes (Blueprint: `patients_api`, prefijo: `/api/patients`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/patients` | Listar pacientes del terapeuta actual |
| POST | `/api/patients` | Crear paciente |
| GET | `/api/patients/<id>` | Obtener paciente |
| PUT | `/api/patients/<id>` | Actualizar paciente |
| DELETE | `/api/patients/<id>` | Eliminar paciente |
| GET | `/api/patients/<id>/sensitivity` | Obtener sensibilidad del paciente |
| PUT | `/api/patients/<id>/sensitivity` | Actualizar sensibilidad (guarda historial) |
| GET | `/api/patients/<id>/sensitivity/history` | Historial de cambios de sensibilidad |

### Juegos (Blueprint: `games_api`, prefijo: `/api/games`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/games` | Listar todos los juegos |
| POST | `/api/games` | Crear juego |
| GET | `/api/games/<id>` | Obtener juego con config |
| PUT | `/api/games/<id>` | Actualizar juego |
| DELETE | `/api/games/<id>` | Eliminar juego |
| GET | `/api/games/<id>/config` | Obtener config JSON del juego |
| GET | `/api/games/<id>/player-config/<pid>` | Config de controles para paciente+juego |
| PUT | `/api/games/<id>/player-config/<pid>` | Guardar config de controles |

### Sesiones (Blueprint: `sessions_api`, prefijo: `/api/sessions`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/sessions` | Listar sesiones (filtro por patient_id, game_id) |
| POST | `/api/sessions` | Crear sesión |
| GET | `/api/sessions/<id>` | Obtener sesión |
| PUT | `/api/sessions/<id>/end` | Finalizar sesión con score |
| GET | `/api/sessions/<id>/events` | Obtener finger events de la sesión |
| GET | `/api/sessions/<id>/report` | Reporte con stats |

### Sensibilidad (Blueprint: `sensitivity_api`, prefijo: `/api/sensitivity`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/sensitivity/presets` | Listar presets |
| POST | `/api/sensitivity/presets` | Crear preset |

### Sprites (Blueprint: `sprites_api`, prefijo: `/api/sprites`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/sprites` | Listar sprites (filtro por category) |
| POST | `/api/sprites` | Crear sprite |
| GET | `/api/sprites/<id>` | Obtener sprite |
| PUT | `/api/sprites/<id>` | Actualizar sprite |
| DELETE | `/api/sprites/<id>` | Eliminar sprite |
| POST | `/api/sprites/batch` | Obtener múltiples sprites por IDs |

### Analytics (Blueprint: `analytics_api`, prefijo: `/api/sessions`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/sessions/<id>/analytics` | Métricas de rehabilitación (compara con sesión anterior) |
| GET | `/api/sessions/<id>/report/pdf` | Descargar PDF del reporte clínico |

### Páginas HTML (Blueprint: `pages`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Redirige a dashboard o login |
| GET | `/dashboard` | Panel del terapeuta |
| GET | `/patients` | Lista de pacientes |
| GET | `/patients/<id>` | Detalle del paciente |
| GET | `/games` | Catálogo de juegos |
| GET | `/play/<id>` | Ejecutar juego |
| GET | `/sessions/<id>/report` | Reporte de sesión |

---

## WebSocket — Hand Tracking

### Ruta: `/ws`

Conexión bidireccional para datos de hand tracking. El cliente ejecuta MediaPipe WASM localmente y envía solo datos JSON (sin frames de video).

### Mensajes Cliente → Servidor

```json
// Configurar sensibilidad
{ "type": "config", "sensitivity": [50, 80, 80, 50, 50] }

// Iniciar sesión
{ "type": "start_session", "session_id": 1 }

// Terminar sesión
{ "type": "end_session" }

// Actualización de dedos (solo en cambio de estado)
{
  "type": "finger_update",
  "session_id": 1,
  "fingers": [1, 0, 1, 0, 0],
  "landmarks": [[0.5, 0.3, 0.1], ...]   // 21 landmarks x 3 coordenadas
}
```

### Flujo

```
Cliente                          Servidor
  │                                │
  │──── config ──────────────────► │
  │──── start_session ───────────► │
  │                                │
  │  ┌─ MediaPipe WASM local ──┐   │
  │  │  detectFingers() cada   │   │
  │  │  frame (60fps)          │   │
  │  └─────────────────────────┘   │
  │                                │
  │──── finger_update (estado) ──► │  ← solo cuando cambia
  │──── finger_update (estado) ──► │
  │──── finger_update (estado) ──► │
  │                                │
  │──── end_session ──────────────►│
  │                                │
```

---

## Motor de Juego (Phaser 3)

### game-loader.js

Interpreta una configuración JSON de la base de datos y crea un juego Phaser 3 en tiempo real.

**Escenas:**

1. **BootScene**: Precarga sprites tipo `image`, genera texturas para sprites tipo `pixelmap`, luego inicia PlayScene.

2. **PlayScene**: Escena principal con:
   - **Jugador**: Sprite con físicas (gravedad, velocidad, salto, bounce). Animaciones idle/run/jump desde spritesheet.
   - **Plataformas**: Estáticas, generación procedural (infinita hacia arriba o abajo), culling híbrido.
   - **Coleccionables**: Monedas con animación de giro, spawn aleatorio sobre plataformas.
   - **Enemigos**: IA de patrulla o persecución.
   - **Controles**: Finger mapping configurable + teclado (flechas + espacio).
   - **Cámara**: Sigue al jugador, auto-scroll opcional.
   - **Parallax**: Fondo con scroll factor.
   - **Reglas**: Victoria por score, derrota por caída o tiempo.

3. **GameOverScene**: Muestra "GANASTE!" o "GAME OVER", score final, click para reiniciar.

**Tipos de juego soportados:**
- `platformer` — plataformas hacia arriba (Doodle Jump-style)
- `runner` — plataformas hacia abajo (coinciden con gravedad normal)
- `catch` — atrapar objetos
- `topdown` — vista superior
- `target` — puntería

### sprite-generator.js

Convierte datos de sprites en texturas de Phaser 3.

- **pixelmap**: Dibuja pixel por pixel desde una paleta de colores + grid de caracteres hex. Soporta múltiples frames para animación.
- **image**: Carga desde URL. Soporta spritesheets con frame_count.

### Config JSON de Juego

Los juegos se definen como JSON almacenado en `games.config`. Ejemplo estructurado:

```json
{
  "version": "1.0",
  "metadata": {
    "name": "Plataformas Terapéuticas",
    "type": "platformer",
    "targetFingers": [0, 1, 2],
    "difficulty": "easy",
    "estimatedDuration": 300
  },
  "physics": {
    "type": "arcade",
    "gravity": { "x": 0, "y": 400 },
    "debug": false
  },
  "world": {
    "width": 400,
    "height": 600,
    "backgroundColor": "#1a1a2e",
    "camera": { "follow": "player", "scrollY": true }
  },
  "entities": {
    "player": { "spawn": {"x": 200, "y": 500}, "speed": 160, "jumpForce": -350 },
    "platforms": { "layout": "procedural", "color": "#4a90d9" },
    "collectibles": { "color": "#ffd23f", "scoreValue": 50 },
    "enemies": { "count": 0, "color": "#ff6b6b" }
  },
  "controls": {
    "fingerMap": {
      "0": "jump", "1": "right", "2": "left",
      "3": "none", "4": "none"
    }
  },
  "rules": {
    "winCondition": { "type": "score", "target": 500 },
    "loseCondition": { "type": "fall_off" },
    "lives": 3
  },
  "sprites": {
    "player": { "sprite_id": 1 },
    "platform": { "sprite_id": 2 }
  }
}
```

---

## Analytics de Rehabilitación

El sistema calcula métricas clínicas a partir de los datos crudos de `finger_events`. Estas métricas se muestran en la interfaz de reporte y se incluyen en el PDF descargable.

### Métricas por Dedo

| Métrica | Cálculo | Rango Saludable | Interpretación Clínica |
|---------|---------|-----------------|----------------------|
| **ROM** (Rango Articular) | `(max(X)-min(X) + max(Y)-min(Y)) / 2` | > 0.10 | Amplitud de movimiento del dedo. Valores bajos indican rigidez o limitación articular. |
| **Tiempo de Reacción** | Segundos hasta primera activación (0→1) | < 2s | Reflejos motrices. Valores altos pueden indicar deterioro neuromuscular. |
| **Fatiga** | `(1 - ROM_último_tercio / ROM_primer_tercio) × 100` | < 25% | Resistencia muscular. Fatiga elevada = posible debilidad patológica. |
| **Temblor** | `(stdev(X) + stdev(Y)) / 2` durante estado=1 | < 0.015 | Control motor fino. Valores altos = temblor significativo. |
| **Activaciones** | Conteo de eventos estado=1 | — | Frecuencia de uso del dedo. Valores bajos pueden indicar evasión por dolor o debilidad. |

### Independencia Digital

Analiza si los dedos se mueven de forma independiente o si hay **sinergias anormales** (ej. el paciente mueve el índice pero el medio se activa involuntariamente).

- **Score 0-100**: ≥ 70 Normal, 40-69 Leve sinergia, < 40 Sinergia significativa
- Por cada par de dedos que se activan juntos >50% del tiempo, se penaliza el score.

### Score Funcional Compuesto (0-100)

Ponderación de todas las métricas para un número único de seguimiento semanal:

| Componente | Peso | Fórmula |
|------------|------|---------|
| ROM | 35% | `min(100, ROM / 0.003)` |
| Fatiga | 25% | `max(0, 100 - fatiga × 3.3)` |
| Temblor | 20% | `max(0, 100 - temblor × 5000)` |
| Activaciones | 20% | `min(100, activaciones × 5)` |
| Independencia | 30% del final | `base × 0.7 + independencia × 0.3` |

### Interpretación Clínica Automática

El sistema genera texto en lenguaje natural basado en:
- Nivel de score funcional (≥80 bueno, 50-79 moderado, <50 reducido)
- Comparación con sesión anterior (mejora/empeoramiento porcentual)
- Alertas por dedo (temblor, fatiga, ROM reducido)
- Problemas de independencia digital

### Comparación con Sesión Anterior

Automáticamente busca la sesión previa del mismo paciente y compara scores, mostrando:
- Diferencia absoluta y porcentual
- Indicador visual de mejora (▲) o empeoramiento (▼)
- Tendencia en el tiempo

---

## Reporte PDF

Endpoint: `GET /api/sessions/<id>/report/pdf`

Genera un PDF con formato médico profesional usando WeasyPrint.

### Contenido del PDF

```
┌─────────────────────────────────────────────┐
│  PIXO Therapy — Reporte Clínico              │
│  Paciente: Juan Pérez   Edad: 34            │
│  Diagnóstico: Parálisis braquial             │
│  Juego: Plataformas Fecha: 30/05/2026       │
│  Duración: 5m 23s                            │
├─────────────────────────────────────────────┤
│              Score Funcional                 │
│                   72                         │
│         ▲ +12% vs sesión anterior            │
├──────────┬──────┬──────┬──────┬──────┬──────┤
│ Dedo     │ ROM  │ Reac │ Fat  │ Trem │ Act │
│──────────┼──────┼──────┼──────┼──────┼──────┤
│ Pulgar   │ 0.28 │ 0.8s │ 12%  │ 0.008│  45  │
│ Índice   │ 0.15⚠│ 1.4s │ 25%⚠│ 0.012│  22  │ ← alerta
│ Medio    │ 0.31 │ 0.6s │  8%  │ 0.005│  38  │
│ Anular   │ 0.22 │ 1.1s │ 18%  │ 0.009│  31  │
│ Meñique  │ 0.18 │ 1.3s │ 22%  │ 0.011│  28  │
├──────────┴──────┴──────┴──────┴──────┴──────┤
│ Independencia Digital: Normal (85/100)       │
│                                               │
│ Interpretación Clínica:                       │
│ El paciente presenta funcionalidad motriz     │
│ moderada. Comparado con la sesión anterior,   │
│ hay una mejora del 12%. Se detecta fatiga     │
│ elevada en índice (25%). Se recomienda        │
│ ejercicios de aislamiento digital.            │
└─────────────────────────────────────────────┘
```

- **Disponible**: En Docker (Linux) con WeasyPrint + GTK
- **Fallback**: En Windows devuelve error 501 (PDF no disponible)
- **Descarga**: Botón "Descargar PDF" en la página de reporte

---

## Frontend

### Templates Jinja2 (10 archivos)

| Template | Extiende | Propósito |
|----------|----------|-----------|
| `base.html` | — | Layout principal: navbar retro pixel-art, flash messages, bloques content/scripts |
| `login.html` | standalone | Formulario de inicio de sesión |
| `register.html` | standalone | Formulario de registro de terapeuta |
| `dashboard.html` | base.html | Panel con stats (pacientes/sesiones/juegos), accesos rápidos |
| `patients.html` | base.html | Tabla de pacientes + modal para crear nuevo |
| `patient_detail.html` | base.html | Info paciente, sliders de sensibilidad, presets, historial, sesiones |
| `games.html` | base.html | Grid de juegos + modal selección paciente |
| `play.html` | base.html | Área de juego Phaser 3 + cámara + indicadores + overlay configuración |
| `report.html` | base.html | Gráficos Chart.js + tabla analytics + interpretación clínica |
| `report_pdf.html` | standalone | Template limpio para PDF médico |

### JavaScript (3 archivos)

| Archivo | Clases/Funciones | Propósito |
|---------|-----------------|-----------|
| `hand-input.js` | `class HandInput` | Captura cámara, MediaPipe WASM local, WebSocket, detección de dedos con histéresis |
| `sprite-generator.js` | `SpriteRenderer` | Renderiza sprites pixelmap/image como texturas Phaser 3 |
| `game-loader.js` | `GameLoader`, BootScene, PlayScene, GameOverScene | Motor de juego Phaser 3 completo |
| play.html (inline) | `drawLandmarks()`, `toggleCamera()`, `toggleFullscreen()`, `buildConfigUI()`, `initGame()`, `endGame()`, etc. | Lógica de la página de juego |

### CSS (1 archivo)

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `platform.css` | 422 | Tema retro pixel-art: paleta oscura (púrpura/neón), fuente Press Start 2P, cards, tablas, modales, sliders, responsive |

---

## Requisitos

Solo necesitas una cosa instalada en tu computadora:

| Software | Versión | Descarga |
|----------|---------|----------|
| **Docker Desktop** | Cualquier versión reciente | https://www.docker.com/products/docker-desktop/ |

No necesitas instalar Python, PostgreSQL, Node.js, ni ninguna otra cosa.

---

## Instalación paso a paso

### Paso 1: Instalar Docker Desktop

1. Ve a https://www.docker.com/products/docker-desktop/
2. Descarga Docker Desktop para tu sistema operativo (Windows/Mac/Linux)
3. Instálalo (en Windows: acepta todos los defaults, **no** necesitas WSL 2 si no quieres, pero es recomendado)
4. Abre Docker Desktop y espera a que aparezca "Engine running" en la esquina inferior izquierda

### Paso 2: Descargar el proyecto

```powershell
# Opción A: Con Git (recomendado)
git clone -b completo https://github.com/ANDERSOUNDZ/juegoIO.git
cd juegoIO/pixiodoc_tracker

# Opción B: Sin Git (descarga el ZIP)
# 1. Ve a https://github.com/ANDERSOUNDZ/juegoIO
# 2. Botón verde "Code" → "Download ZIP"
# 3. Extrae el ZIP y abre la carpeta pixiodoc_tracker
```

### Paso 3: Crear archivo .env (opcional, ya viene incluido)

Si no ves el archivo `.env` en la carpeta, crea uno copiando:

```powershell
Copy-Item .env.example .env
```

Los valores por defecto ya funcionan, no necesitas cambiarlos.

### Paso 4: Construir y levantar los servicios

```powershell
# Primera vez (solo descarga imágenes Docker)
docker compose up -d
```
Esta es la parte más lenta. Docker va a:
1. Descargar Python 3.11, PostgreSQL 16 y pgAdmin
2. Instalar las librerías Python (Flask, SQLAlchemy, etc.)
3. Iniciar los 3 servicios

> Las librerías frontend (Phaser, MediaPipe, Chart.js, Google Fonts, ~22 MB) ya vienen incluidas en el repositorio. No necesitan descargarse.

**Tiempo estimado:** 3-5 minutos (depende de tu internet).

### Paso 5: Verificar que todo funciona

```powershell
docker compose ps
```

Debes ver 3 contenedores con estado "Up" y "healthy":
```
NAME             SERVICE    STATUS                    PORTS
mario-web        web        Up 30 seconds (healthy)   0.0.0.0:5001->5000/tcp
mario-postgres   postgres   Up 30 seconds (healthy)   0.0.0.0:5432->5432/tcp
mario-pgadmin    pgadmin    Up 30 seconds             0.0.0.0:5050->80/tcp
```

Si ves "healthy" en web y postgres, todo está bien.

### Paso 6: Abrir la aplicación

| Servicio | URL | Usuario/Contraseña |
|----------|-----|-------------------|
| **PIXO Therapy** (app principal) | http://localhost:5001 | Regístrate libre |
| **pgAdmin** (gestor BD) | http://localhost:5050 | admin@admin.com / admin |

### Paso 7: Primer uso

1. Abre http://localhost:5001
2. Haz clic en **"Crear cuenta"**
3. Regístrate como terapeuta (nombre, email, contraseña)
4. ¡Ya estás dentro! Crea pacientes, juega, genera reportes

---

## Cómo usar después de la primera vez

```powershell
# Iniciar servicios (si están detenidos)
docker compose start

# Ver logs en vivo
docker compose logs -f

# Detener (conserva datos de la BD)
docker compose down

# Detener y borrar TODO (BD incluida)
docker compose down -v

# Reconstruir después de cambios en Python/Dockerfile
docker compose up --build -d
```

---

## Solución de problemas

| Problema | Causa posible | Solución |
|----------|--------------|----------|
| `docker: command not found` | Docker no instalado | Descarga e instala Docker Desktop |
| Puerto 5001 en uso | Otro programa usa ese puerto | Cambia el puerto en docker-compose.yml línea 6 (`5001:5000` → `5002:5000`) |
| Puerto 5432 en uso | Otro PostgreSQL local | Detén tu PostgreSQL local antes de iniciar Docker |
| Contenedor `mario-web` se reinicia | DB no lista aún | Espera 30 segundos, el healthcheck lo intenta automáticamente |
| La cámara no funciona | Permisos del navegador | Acepta permisos de cámara cuando el navegador lo pida |
| Los juegos no cargan | Faltan vendor files | Asegúrate de estar en la rama `completo`: `git checkout completo` |
| pgAdmin no conecta | Credenciales incorrectas | Usa: Host=postgres, User=postgres, Password=admin, DB=mario_db |

---

## ¿Qué hace cada servicio?

| Servicio | Contenedor | Puerto local | Qué es | Para qué sirve |
|----------|------------|-------------|--------|---------------|
| **web** | `mario-web` | `http://localhost:5001` | Flask + Phaser + MediaPipe | La app principal donde juegas |
| **postgres** | `mario-postgres` | `5432` | Base de datos PostgreSQL | Guarda pacientes, sesiones, config |
| **pgadmin** | `mario-pgadmin` | `http://localhost:5050` | Gestor web de PostgreSQL | Para ver/editar la BD directamente |

---

## Estructura de carpetas importante

```
pixiodoc_tracker/
├── server.py                ← Entry point (no tocar)
├── Dockerfile               ← Cómo se construye el contenedor
├── docker-compose.yml       ← Configuración de los 3 servicios
├── .env / .env.example      ← Variables de entorno
├── tools/download-vendor.sh ← Script que descarga librerías frontend
├── src/                     ← Código Python (backend)
├── static/                  ← JS, CSS, imágenes (frontend)
├── templates/               ← Plantillas HTML
├── games/                   ← Juegos específicos (Prince, SMB3, emuladores)
└── db/schema.sql            ← Estructura de la base de datos
```

---

## Flujo de Trabajo

### Para el Terapeuta

```
1. Registrar cuenta → /register
2. Crear paciente → /patients → "Nuevo paciente"
3. Ajustar sensibilidad → /patients/<id> → sliders por dedo
4. Elegir juego → /games → seleccionar juego
5. Seleccionar paciente → modal → elegir preset de sensibilidad
6. Jugar → /play/<id> → activar cámara → gestos controlan el juego
7. Ver resultado → al terminar → redirect a reporte
8. Descargar PDF → botón "Descargar PDF" en reporte
```

### Para el Doctor (interpretación de reportes)

```
1. El terapeuta comparte el PDF del reporte
2. El PDF incluye:
   - Score funcional (0-100) con tendencia
   - Métricas por dedo (ROM, fatiga, temblor)
   - Independencia digital (sinergias anormales)
   - Interpretación clínica en lenguaje natural
3. Evaluar evolución comparando reportes de sesiones sucesivas
```

---

## Comandos Útiles

```powershell
# Docker
docker compose up -d                    # Iniciar servicios
docker compose down                     # Detener (conserva datos)
docker compose down -v                  # Detener y borrar datos DB
docker compose logs -f                  # Ver logs en vivo
docker compose logs web                 # Logs solo del servidor web
docker compose build web                # Reconstruir imagen web
docker compose exec postgres psql -U postgres -d mario_db  # Acceder a DB

# Servidor (local)
python server.py                        # Iniciar (Ctrl+C para detener)
pip install -r requirements.txt         # Instalar dependencias

# Git
git pull                                # Actualizar
git add -A && git commit -m "mensaje"  # Commit
git push                                # Subir cambios
```

---

## Estructura del Proyecto

```
pixiodoc_tracker/
├── server.py                        # Entry point Flask
├── Dockerfile                       # Python 3.11-slim + WeasyPrint + curl
├── docker-compose.yml               # 3 servicios (web, postgres, pgadmin)
├── requirements.txt                 # Dependencias Python
├── .env / .env.example              # Variables de entorno
├── .dockerignore                    # Exclusiones Docker
├── .gitignore                       # Exclusiones Git
├── README.md                        # Esta documentación
│
├── tools/
│   └── download-vendor.sh           # Descarga Phaser, MediaPipe, etc. (se ejecuta en docker build)
│
├── src/                             # Código fuente Python
│   ├── config/settings.py           # Config desde variables de entorno
│   ├── domain/                      # Entidades, value objects, interfaces
│   ├── application/                 # Servicios (pacientes, juegos, sesiones, analytics)
│   └── infrastructure/              # Persistencia, controladores Flask, WebSocket
│
├── static/                          # Frontend
│   ├── css/pixo.css                # Estilos
│   ├── js/                         # hand-input.js, game-loader.js, etc.
│   └── vendor/                     # ⚡ Generado por Docker (NO editar aquí)
│       ├── phaser/
│       ├── fomantic/
│       ├── jquery/
│       ├── chart.js/
│       ├── nostalgist/
│       ├── mediapipe/              # HandLandmarker model + WASM + vision bundle
│       └── fonts/                  # Google Fonts Plus Jakarta Sans
│
├── templates/                       # Plantillas HTML (Jinja2)
├── games/                           # Juegos (Prince of Persia, SMB3, emulador)
└── db/schema.sql                    # Esquema de base de datos + seed data
```

---

## Cómo conectar pgAdmin

1. Abre http://localhost:5050
2. Login: admin@admin.com / admin
3. Clic derecho en "Servers" → "Register" → "Server"
4. Pestaña **General**: Name = `PIXO Local`
5. Pestaña **Connection**:
   - Host: `postgres`
   - Port: `5432`
   - Username: `postgres`
   - Password: `admin`
6. Guardar

---

## Comandos rápidos

```powershell
# Iniciar todo
docker compose up -d

# Ver estado
docker compose ps

# Ver logs del servidor web
docker compose logs -f web

# Detener (sin borrar datos)
docker compose down

# Detener y borrar BD
docker compose down -v

# Reconstruir después de cambiar Python/Dockerfile
docker compose up --build -d

# Solo iniciar/detener (sin build, los vendor ya están en el repo)
docker compose start
docker compose stop

# Acceder a la base de datos
docker compose exec postgres psql -U postgres -d mario_db
```