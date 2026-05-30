# PIXO Therapy — Plataforma de Juegos Terapéuticos

Plataforma de rehabilitación motriz basada en juegos controlados por gestos de la mano. Utiliza **MediaPipe Hand Tracking** para detectar la posición de los 5 dedos en tiempo real, permitiendo a terapeutas gestionar pacientes, configurar sensibilidad, ejecutar sesiones de juego y monitorear la evolución mediante **métricas de rehabilitación** con reportes PDF descargables.

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

## Docker

### Servicios

```
docker compose up -d
```

| Servicio | Contenedor | Puerto | Imagen | Propósito |
|----------|------------|--------|--------|-----------|
| **web** | `mario-web` | `5000` | Build local | Servidor Flask |
| **postgres** | `mario-postgres` | `5432` | `postgres:16` | Base de datos |
| **pgadmin** | `mario-pgadmin` | `5050:80` | `dpage/pgadmin4` | Gestor DB web |

### Volúmenes

| Volumen | Montaje | Propósito |
|---------|---------|-----------|
| `pgdata` | `/var/lib/postgresql/data` | Persistencia de DB |
| `pgadmin-data` | `/var/lib/pgadmin` | Config de pgAdmin |
| Bind mount | `./src:/app/src` | Hot reload (desarrollo) |
| Bind mount | `./templates:/app/templates` | Hot reload (desarrollo) |
| Bind mount | `./static:/app/static` | Hot reload (desarrollo) |
| Bind mount | `./server.py:/app/server.py` | Hot reload (desarrollo) |
| Bind mount | `./hand_landmarker.task` | Modelo MediaPipe |

### Hot Reload

En modo desarrollo, los cambios en el código se reflejan automáticamente:

| Cambio | ¿Requiere rebuild? | Tiempo de recarga |
|--------|-------------------|-------------------|
| Python `.py` | No | ~1s (Flask recarga automática) |
| Jinja2 `.html` | No | Instantáneo (refrescar navegador) |
| JS / CSS | No | Instantáneo (refrescar navegador) |
| `requirements.txt` | Sí (`docker compose build web`) | ~10s |
| `Dockerfile` | Sí (`docker compose build web`) | ~10s |

---

## Inicio Rápido

### Con Docker (recomendado)

```powershell
cd mario_db_tracker
docker compose up -d
# Abrir http://localhost:5000
# pgAdmin: http://localhost:5050 (admin@admin.com / admin)
```

### Sin Docker (desarrollo local)

Requiere PostgreSQL 16 instalado y corriendo.

```powershell
cd mario_db_tracker
pip install -r requirements.txt
python server.py
# Abrir http://localhost:5000
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
mario_db_tracker/
├── server.py                        # Entry point Flask (delgado)
├── Dockerfile                       # Python 3.11-slim + WeasyPrint
├── docker-compose.yml               # 3 servicios (web, postgres, pgadmin)
├── requirements.txt                 # 7 dependencias Python
├── .dockerignore                    # Exclusiones Docker
├── .gitignore                       # Exclusiones Git
├── hand_landmarker.task             # Modelo MediaPipe (~15MB)
├── README.md                        # Esta documentación
│
├── src/                             # 📦 CÓDIGO FUENTE
│   ├── domain/                      # ⚪ Capa de dominio
│   │   ├── entities.py              #   10 entidades puras (dataclasses)
│   │   ├── value_objects.py         #   FingerState, Sensitivity, HandLandmarks
│   │   ├── exceptions.py           #   DomainError, NotFoundError, ValidationError
│   │   └── interfaces/             #   Puertos abstractos
│   │       ├── repositories.py     #   9 interfaces de repositorios
│   │       └── hand_tracker.py     #   IHandTracker
│   │
│   ├── application/                 # 🟢 Capa de aplicación
│   │   ├── patient_service.py      #   Pacientes + sensibilidad + historial
│   │   ├── game_service.py         #   Juegos + config por jugador
│   │   ├── session_service.py      #   Sesiones + eventos + reportes
│   │   ├── sensitivity_service.py  #   Presets
│   │   ├── sprite_service.py       #   Sprites CRUD + batch
│   │   └── analytics_service.py   #   Métricas de rehabilitación + PDF
│   │
│   └── infrastructure/             # 🔵 Capa de infraestructura
│       ├── di.py                   #   Inyección de dependencias
│       ├── persistence/
│       │   ├── models.py           #   9 modelos SQLAlchemy
│       │   ├── repositories.py     #   Implementaciones de repositorios
│       │   └── db_worker.py        #   Worker async para inserts
│       └── web/
│           ├── app.py              #   Flask create_app()
│           ├── config.py           #   Config Flask
│           ├── middleware.py       #   Error handlers
│           └── controllers/
│               ├── auth.py         #   Login/register + API
│               ├── patients.py     #   Pacientes API
│               ├── games.py        #   Juegos API
│               ├── sessions.py     #   Sesiones API
│               ├── sensitivity.py  #   Presets API
│               ├── sprites.py      #   Sprites API
│               ├── analytics.py    #   Analytics API + PDF
│               ├── pages.py        #   Rutas de páginas HTML
│               └── ws.py           #   WebSocket handler
│
├── static/                          # 📦 FRONTEND
│   ├── css/platform.css            #   Tema retro pixel-art (422 líneas)
│   └── js/
│       ├── hand-input.js           #   MediaPipe WASM + WebSocket + detección
│       ├── game-loader.js          #   Motor Phaser 3 (709 líneas)
│       └── sprite-generator.js     #   Renderizador de sprites
│
└── templates/                       # 📦 PLANTILLAS
    ├── base.html                   #   Layout principal
    ├── login.html                  #   Login
    ├── register.html               #   Registro
    ├── dashboard.html              #   Dashboard terapeuta
    ├── patients.html               #   Lista pacientes
    ├── patient_detail.html         #   Detalle + sensibilidad
    ├── games.html                  #   Catálogo juegos
    ├── play.html                   #   Ejecutor Phaser 3 (705 líneas)
    ├── report.html                 #   Reporte con analytics
    └── report_pdf.html             #   Template PDF médico
```
