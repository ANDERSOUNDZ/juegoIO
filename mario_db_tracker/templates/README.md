# PIXO Therapy — Migración de UI (Fomantic + tema PIXO)

Dos sets equivalentes:

- **`pixo/templates/`** → plantillas **Flask reales** (drop-in). Reemplazan a `uploads/templates/`.
- **`pixo/*.html`** (raíz) → versiones **standalone previsualizables** con datos de ejemplo (`mock-api.js`), para revisar el diseño sin levantar el backend.

La **lógica JS** (fetch a `/api`, handlers, eventos) es idéntica al original en ambos sets.

## Integración en Flask

1. Copia las plantillas a tu carpeta de templates:
   ```
   pixo/templates/*.html  →  templates/
   ```
2. Copia los assets a tu carpeta `static`:
   ```
   pixo/static/css/pixo.css     →  static/css/pixo.css
   pixo/static/js/pixo-ui.js    →  static/js/pixo-ui.js
   ```
   (`pixo-ui.js` = sprite de iconos + toggle de tema claro/oscuro persistente.)
3. Tus JS de juego/reporte siguen igual en `static/js/`: `hand-input.js`, `sprite-generator.js`, `game-loader.js`, `hand3d-viz.js`.

## Estructura

- `base.html` — layout base: nav (estado activo por `request.endpoint`), tema, flash, `{% block content %}` y `{% block scripts %}`.
  - `{% block head %}` para libs por página (Chart.js, Phaser…).
  - `{% block main_class %}` vacío en `play.html` para ir a pantalla completa.
- `login.html`, `register.html` — autocontenidas (sin nav, usuario no autenticado).
- `dashboard / patients / patient_detail / games / report / play` — extienden `base.html`.
- `report_pdf.html` — plantilla server-rendered para el PDF (sin JS).

## Notas

- Variables Jinja conservadas: `{{ patient_id }}`, `{{ session_id }}`, `{{ game_id }}`, `current_user`, `finger_rows`, etc.
- En las versiones standalone esas variables se leen de la URL (`?id=`, `?game_id=`) y `mock-api.js` responde si no hay backend — ese script **no** se incluye en las plantillas Flask.
- Tema: `--brand` (azul) + `--teal`, tipografía Plus Jakarta Sans. Edita los tokens en `pixo.css`.
