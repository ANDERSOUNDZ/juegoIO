-- ═══════════════════════════════════════════════════════════════
-- Schema: Plataforma de Juegos Terapéuticos
-- ═══════════════════════════════════════════════════════════════

-- Legacy: tabla original de control de dedos
CREATE TABLE IF NOT EXISTS control_juego (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    nivel INT NOT NULL CHECK (nivel BETWEEN 1 AND 5),
    pulgar INT NOT NULL CHECK (pulgar IN (0, 1)),
    indice INT NOT NULL CHECK (indice IN (0, 1)),
    medio INT NOT NULL CHECK (medio IN (0, 1)),
    anular INT NOT NULL CHECK (anular IN (0, 1)),
    menique INT NOT NULL CHECK (menique IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_control_juego_timestamp ON control_juego(timestamp DESC);

-- ─── USUARIOS (genérica con roles) ─────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'therapist',  -- therapist, admin, viewer
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── PACIENTES ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    age INT,
    diagnosis TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── JUEGOS (config JSON) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    game_type VARCHAR(50) NOT NULL,
    thumbnail_url TEXT,
    config JSONB NOT NULL,
    created_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── SESIONES DE JUEGO ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id) ON DELETE CASCADE,
    game_id INT REFERENCES games(id) ON DELETE SET NULL,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    score INT DEFAULT 0,
    metadata JSONB
);

-- ─── EVENTOS DE DEDOS (con landmarks) ─────────────────────────
CREATE TABLE IF NOT EXISTS finger_events (
    id BIGSERIAL PRIMARY KEY,
    session_id INT REFERENCES game_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    finger_index INT NOT NULL CHECK (finger_index BETWEEN 0 AND 4),
    state INT NOT NULL CHECK (state IN (0, 1)),
    landmark_x FLOAT,
    landmark_y FLOAT,
    landmark_z FLOAT,
    confidence FLOAT
);
CREATE INDEX IF NOT EXISTS idx_finger_events_session ON finger_events(session_id, timestamp);

-- ─── PRESETS DE SENSIBILIDAD ──────────────────────────────────
CREATE TABLE IF NOT EXISTS sensitivity_presets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    difficulty_level VARCHAR(50),
    sensitivities JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── SENSIBILIDAD POR PACIENTE ────────────────────────────────
CREATE TABLE IF NOT EXISTS patient_sensitivity (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id) ON DELETE CASCADE UNIQUE,
    sensitivities JSONB NOT NULL,
    based_on_preset INT REFERENCES sensitivity_presets(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by INT REFERENCES users(id) ON DELETE SET NULL
);

-- ─── HISTORIAL DE CAMBIOS DE SENSIBILIDAD ─────────────────────
CREATE TABLE IF NOT EXISTS sensitivity_history (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id) ON DELETE CASCADE,
    old_sensitivities JSONB,
    new_sensitivities JSONB NOT NULL,
    reason TEXT,
    changed_by INT REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── PRESETS POR DEFECTO DEL SISTEMA ──────────────────────────
INSERT INTO sensitivity_presets (name, description, difficulty_level, sensitivities, is_default)
SELECT * FROM (VALUES
    ('Principiante', 'Movilidad muy limitada - alta sensibilidad, detecta movimientos mínimos', 'beginner', '[85, 85, 85, 85, 85]'::jsonb, true),
    ('Intermedio', 'Movilidad moderada - sensibilidad balanceada', 'intermediate', '[50, 50, 50, 50, 50]'::jsonb, true),
    ('Avanzado', 'Buena movilidad - requiere movimientos claros', 'advanced', '[25, 25, 25, 25, 25]'::jsonb, true),
    ('Pulgar enfocado', 'Alta sensibilidad en pulgar, normal en el resto', 'custom', '[90, 50, 50, 50, 50]'::jsonb, true),
    ('Índice-Medio', 'Enfoque en índice y medio (los más usados en juegos)', 'custom', '[50, 80, 80, 50, 50]'::jsonb, true)
) AS v(name, description, difficulty_level, sensitivities, is_default)
WHERE NOT EXISTS (SELECT 1 FROM sensitivity_presets WHERE is_default = true);

-- ─── SPRITES REUTILIZABLES ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS sprites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(30) NOT NULL CHECK (category IN ('player', 'platform', 'coin', 'enemy', 'background', 'other')),
    type VARCHAR(20) NOT NULL CHECK (type IN ('pixelmap', 'image')),
    width INT NOT NULL,
    height INT NOT NULL,
    data JSONB,            -- pixelmap: { palette: [...], frames: [{ grid: [...] }] }
    image_url TEXT,         -- image: URL to PNG/SVG
    frame_count INT DEFAULT 1,
    created_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── SPRITES POR DEFECTO ────────────────────────────────────────
INSERT INTO sprites (name, category, type, width, height, data, image_url, frame_count)
SELECT * FROM (VALUES
    ('Pixo Hero', 'player', 'pixelmap', 20, 26,
     '{"palette":["#3ddc97","#1f7a4f","#ffd23f","#5a2a8a","#f4c896","#c89868","#1a0a2e","#ff8a8a","#ffd23f","#b8830a","#7a3ac8","#4a1a8a","#2a1a0a","#fff3a0"],"frames":[{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa......","..888aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa888.","..999aaaaaaaaaaa999.","..444aaaaaaaaaaa444.","..444bbbbbbbbbbb444.",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....","....ccccc..ccccc...."]},{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa......","..888aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa888.","..999aaaaaaaaaaa999.","..444aaaaaaaaaaa444.","..444bbbbbbbbbbb444.",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..ccccc....","....ccccc..ccccc...."]},{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa..888.",".....aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa999.","..888aaaaaaaaaaa444.","..999aaaaaaaaaaa444.","..444bbbbbbbbbbb....","..444aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....ccccc.aaaa.....",".....ccccc.ccccc...."]},{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa......","..888aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa888.","..999aaaaaaaaaaa999.","..444aaaaaaaaaaa444.","..444bbbbbbbbbbb444.",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....cccc..cccc.....",".....cccc..cccc....."]}]}'::jsonb,
     NULL::text, 4),
    ('Ladrillo Retro', 'platform', 'pixelmap', 16, 16,
     '{"palette":["#c84b31","#7a2e1d","#e87a5a"],"frames":[{"grid":["1222222212222222","1222222212222222","1000000010000000","1000000010000000","1000000010000000","1000000010000000","1000000010000000","1000000010000000","1111111111111111","1000000010000000","1000000010000000","1000000010000000","1000000010000000","1111111111111111","1111111111111111","1111111111111111"]}]}'::jsonb,
     NULL::text, 1),
    ('Bloque ?', 'other', 'pixelmap', 16, 16,
     '{"palette":["#ffd23f","#b8830a","#fff3a0"],"frames":[{"grid":["2222222222222211","2222222222222211","2200000000000011","2200011111100011","2200011111100011","2200000001100011","2200000001100011","2200000110000011","2200000110000011","2200000000000011","2200000110000011","2200000110000011","2200000000000011","2211111111111111","2211111111111111","2211111111111111"]}]}'::jsonb,
     NULL::text, 1),
    ('Moneda Dorada', 'coin', 'pixelmap', 12, 12,
     '{"palette":["#ffd23f","#fff3a0","#b8830a","#ffffff"],"frames":[{"grid":[".....11.....",".....11.....",".....00.....",".....00.....",".....00.....",".....00.....",".....00.....",".....00.....",".....00.....",".....00.....",".....22.....",".....22....."]},{"grid":["....1111....","....1111....","....0000....","....0000....","....0000....","....0000....","....0000....","....0000....","....0000....","....0000....","....2222....","....2222...."]},{"grid":["..11331111..","..11111111..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..22222222..","..22222222.."]},{"grid":[".1133111111.",".1111111111.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".2222222222.",".2222222222."]},{"grid":["..11331111..","..11111111..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..22222222..","..22222222.."]},{"grid":["....1111....","....1111....","....0000....","....0000....","....0000....","....0000....","....0000....","....0000....","....0000....","....0000....","....2222....","....2222...."]}]}'::jsonb,
     NULL::text, 6),
    ('Enemigo Basico', 'enemy', 'pixelmap', 16, 16,
     '{"palette":["#ff5c8a","#ffffff","#1a0a2e","#cc3366"],"frames":[{"grid":["................","................","....00000000....","....00000000....","..000000000000..","..000000000000..","..001110011100..","..001220012200..","..001220012200..","..000000000000..","..000000000000..","..000000000000..","..000000000000..",".33333000033333.",".33333....33333.",".33333....33333."]}]}'::jsonb,
     NULL::text, 1)
) AS v(name, category, type, width, height, data, image_url, frame_count)
WHERE NOT EXISTS (SELECT 1 FROM sprites LIMIT 1);

-- ─── JUEGO POR DEFECTO ──────────────────────────────────────────
INSERT INTO games (name, description, game_type, config)
SELECT 'Plataformas Terapéuticas',
       'Platformer básico para ejercitar pulgar, índice y medio. Salta entre plataformas y recoge monedas.',
       'platformer',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Plataformas Terapéuticas",
           "type": "platformer",
           "targetFingers": [0, 1, 2],
           "difficulty": "easy",
           "description": "Platformer básico para rehabilitación de motricidad fina",
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
             "color": "#3ddc97",
             "speed": 160,
             "jumpForce": -350,
             "physics": {
               "bounce": 0.2,
               "collideWorldBounds": true
             }
           },
           "platforms": {
             "static": true,
             "color": "#4a90d9",
             "width": 80,
             "height": 14,
             "layout": "procedural",
             "procedural": {
               "count": 15,
               "minGap": 40,
               "maxGap": 80,
               "minWidth": 60,
               "maxWidth": 150
             }
           },
           "collectibles": {
             "color": "#ffd23f",
             "spawnRate": 0.5,
             "scoreValue": 50
           },
           "enemies": {
             "count": 0,
             "color": "#ff6b6b",
             "width": 16,
             "height": 16,
             "ai": "patrol",
             "speed": 40
           }
         },
         "controls": {
           "fingerMap": {
             "0": "jump",
             "1": "right",
             "2": "left",
             "3": "none",
             "4": "none"
           },
           "keyboardFallback": true
         },
         "rules": {
           "winCondition": {
             "type": "score",
             "target": 500
           },
           "loseCondition": {
             "type": "fall_off"
           },
           "lives": 3,
           "timer": null
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Plataformas Terapéuticas');

-- Link sprites to game config
UPDATE games SET config = config || jsonb_build_object('sprites', jsonb_build_object(
    'player', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'player' LIMIT 1)),
    'platform', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'platform' LIMIT 1)),
    'coin', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'coin' LIMIT 1)),
    'enemy', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'enemy' LIMIT 1))
))
WHERE name = 'Plataformas Terapéuticas' AND NOT (config ? 'sprites');

-- ─── CONFIG DE CONTROLES POR PACIENTE+JUEGO ───────────────────
CREATE TABLE IF NOT EXISTS player_game_config (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id) ON DELETE CASCADE,
    game_id INT REFERENCES games(id) ON DELETE CASCADE,
    sensitivities JSONB NOT NULL DEFAULT '[50,50,50,50,50]',
    finger_map JSONB NOT NULL DEFAULT '{"0":"jump","1":"right","2":"left","3":"none","4":"none"}',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(patient_id, game_id)
);
