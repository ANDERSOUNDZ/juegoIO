# PIXO Therapy — Rehabilitación Motriz a Través del Juego

## ¿Qué es?

**PIXO Therapy** es una plataforma web de rehabilitación motriz que convierte los gestos de la mano del paciente —capturados por una cámara web común— en control directo de videojuegos terapéuticos. Sin controles físicos, sin sensores costosos, sin equipo especializado: solo una cámara y un navegador.

## El Problema

La rehabilitación de la motricidad fina de la mano y los dedos (tras un ACV, parálisis braquial, lesión nerviosa, esclerosis múltiple, etc.) enfrenta tres grandes dificultades:

1. **Falta de adherencia** — Los ejercicios repetitivos son tediosos. Los pacientes se desmotivan y abandonan.
2. **Medición subjetiva** — Los terapeutas carecen de datos cuantitativos objetivos para evaluar la evolución.
3. **Barrera económica** — Los sistemas de realidad virtual o sensores especializados son prohibitivos para la mayoría de clínicas y hogares.

## La Solución

PIXO Therapy transforma la rehabilitación en una experiencia lúdica y medible:

| Necesidad | Cómo lo cubre PIXO |
|-----------|-------------------|
| **Motivación del paciente** | Juegos tipo plataformas, runner, catch, top-down y target — divertidos, progresivos y adaptados a cada paciente. Incluye además Prince of Persia (SDLPoP) como juego clásico controlable por gestos. |
| **Seguimiento objetivo** | Métricas clínicas automatizadas: ROM (rango articular), tiempo de reacción, fatiga muscular, temblor, independencia digital y un Score Funcional Compuesto (0-100). |
| **Accesibilidad** | Solo requiere un navegador moderno y una cámara web. Sin instalación, sin hardware extra. |
| **Personalización** | El terapeuta ajusta la sensibilidad de cada dedo individualmente, configura qué dedo controla qué acción, y adapta la dificultad al progreso del paciente. |
| **Reportes clínicos** | Genera PDFs con formato médico profesional que incluyen métricas por dedo, interpretación clínica en lenguaje natural, y comparación con sesiones anteriores. |

## ¿Para quién?

### Terapeutas Ocupacionales / Fisioterapeutas
- Dashboard con gestión de pacientes
- Ajuste de sensibilidad por dedo con sliders en tiempo real
- Catálogo de juegos asignables a cada paciente
- Reportes con métricas de rehabilitación y PDF descargable

### Pacientes
- Juegos controlados con la mano real vía cámara web (MediaPipe WASM corriendo 100% en el navegador — sin enviar video al servidor)
- Dificultad adaptada a su condición
- Experiencia divertida que fomenta la práctica repetitiva sin aburrimiento

### Médicos / Directores Clínicos
- Reportes PDF con interpretación clínica automática
- Score funcional compuesto para seguimiento longitudinal
- Detección de fatiga, temblor, sinergias anormales entre dedos

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+, Flask 3.x (Clean Architecture) |
| Base de datos | PostgreSQL 16 |
| Hand Tracking | MediaPipe Hands WASM (en el navegador) |
| Motor de juegos | Phaser 3.80.1 (HTML5 Canvas) |
| Tiempo real | WebSocket (Flask-Sock) |
| Reportes PDF | WeasyPrint |
| Contenedores | Docker Compose (web + postgres + pgadmin) |
| Frontend | Jinja2, CSS retro pixel-art, Chart.js |

## Arquitectura en 30 segundos

```
Cámara Web → MediaPipe WASM (navegador) → WebSocket → Flask (Python)
                                                          ↓
                                                     PostgreSQL
                                                          ↓
                                              Reportes PDF / Dashboard
```

Toda la detección de mano ocurre **localmente en el navegador** del paciente. Al servidor solo llegan datos estructurados (qué dedos se movieron y cuándo), garantizando privacidad total.

## Funcionalidades Principales

### Gestión de Pacientes
- CRUD completo con diagnóstico, notas y edad
- Historial de cambios de sensibilidad con trazabilidad
- Configuración de controles por paciente y por juego

### 5 Tipos de Juego Terapéutico
- **Platformer** — Saltar entre plataformas (Doodle Jump-style)
- **Runner** — Auto-scroll vertical descendente
- **Catch** — Atrapar objetos que caen
- **Top-down** — Movimiento libre en 4 direcciones
- **Target** — Puntería y precisión

### Analítica Clínica
- **ROM** (Rango Articular) por dedo
- **Tiempo de Reacción** desde que se solicita el movimiento
- **Fatiga** porcentual (comparación inicio vs final de sesión)
- **Temblor** (desviación estándar del landmark)
- **Independencia Digital** (detección de sinergias anormales)
- **Score Funcional Compuesto** (0-100) con pesos clínicos
- **Comparación automática** con la sesión anterior

### Prince of Persia Integrado
El port open-source SDLPoP (Prince of Persia original) está compilado a WASM y se controla con gestos de la mano desde el navegador, como juego adicional para pacientes más avanzados.

## Inicio Rápido

### Con Docker (recomendado)

```powershell
docker compose up -d
# Abrir http://localhost:5000
# pgAdmin: http://localhost:5050 (admin@admin.com / admin)
```

### Sin Docker (desarrollo local)

```powershell
pip install -r requirements.txt
python server.py
# Abrir http://localhost:5000
```

Requiere PostgreSQL 16 instalado y corriendo localmente.

## Flujo de Trabajo Típico

1. **Terapeuta** se registra en la plataforma
2. **Crea pacientes** con su información clínica
3. **Ajusta la sensibilidad** de cada dedo para cada paciente
4. **Asigna juegos** y configura qué dedo controla qué acción
5. **El paciente juega** usando solo los gestos de su mano frente a la cámara
6. **Sistema genera métricas** automáticamente durante la sesión
7. **Terapeuta revisa** el reporte con gráficos y scores
8. **Descarga PDF** para compartir con el médico o la historia clínica

## Créditos

- **SDLPoP**: Port open-source de Prince of Persia por SDLPoP contributors (GPL v3)
- **MediaPipe**: Hand tracking de Google
- **Phaser 3**: Framework de juegos HTML5
- **Prince of Persia** es copyright de Jordan Mechner — incluido como referencia educativa
