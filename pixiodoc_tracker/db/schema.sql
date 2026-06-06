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

-- ─── ROLES ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30) UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO roles (name, description) VALUES
    ('admin', 'Acceso total al sistema'),
    ('therapist', 'Gestión de pacientes y sesiones'),
    ('patient', 'Acceso a informacion del paciente y uso de los juegos')
ON CONFLICT (name) DO NOTHING;

-- ─── USUARIOS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    role_id INT REFERENCES roles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO users (email, password_hash, name, lastname, role_id) VALUES
    ('admin@pixotherapy.com', 'scrypt:32768:8:1$xvxtnd0Xqh8nWDax$fcf56ddc6b033a7afa8f8abe28ecad9786442d5fa5371908583c2235305b6de5a75ed6e2e6c5127f20437e0867a10f0111a637af9cfb49b3f8db28875a72081b', 'Admin', 'admin', 1) -- pass: 12345678
ON CONFLICT (email) DO NOTHING;

-- ─── PACIENTES ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    therapist_id INT REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    document VARCHAR(10) NOT NULL,
    birth_date DATE,
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

-- ─── SPRITES MARIO BROS ─────────────────────────────────────────
INSERT INTO sprites (name, category, type, width, height, data, image_url, frame_count)
SELECT * FROM (VALUES
    ('Mario Bros', 'player', 'pixelmap', 20, 26,
     '{"frames":[{"grid":["....0000000000......","...000000000000.....","...000000000000.....","..00000000000000....","..22000000000022....","..22000000000022....","..22440000004422....","..22555555555522....","..22000000000022....","...000000000000.....","...000660066000.....","...000660066000.....","...000000000000.....","..00111111111100....",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...","..00111111111100....","......33..33........","......33..33........","......33..33........","......33..33........","......33..33........",".....3333..3333....."]},{"grid":["....0000000000......","...000000000000.....","...000000000000.....","..00000000000000....","..22000000000022....","..22000000000022....","..22440000004422....","..22555555555522....","..22000000000022....","...000000000000.....","...000660066000.....","...000660066000.....","...000000000000.....","..00111111111100....",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...","..00111111111100....",".....33..33.........",".....33..33.........",".....33..33.........",".....33..33.........","....3333..33........","....33....3333......"]},{"grid":["....0000000000......","...000000000000.....","...000000000000.....","..00000000000000....","..22000000000022....","..22000000000022....","..22440000004422....","..22555555555522....","..22000000000022....","...000000000000.....","...000660066000.....","...000660066000.....","...000000000000.....","..00111111111100....",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...","..00111111111100....","........33..33......","........33..33......","........33..33......","........33..33......",".......3333..33.....",".....3333....33....."]},{"grid":["....0000000000......","...000000000000.....","...000000000000.....","..00000000000000....","..22000000000022....","..22000000000022....","..22440000004422....","..22555555555522....","..22000000000022....","...000000000000.....","...000660066000.....","...000660066000.....","...000000000000.....","..00111111111100....",".0011111111111100...",".0011111111111100...",".0011111111111100...",".0011111111111100...","..00111111111100....",".....33......33.....",".....33......33.....","....3333....3333....","....33........33....","....33........33....","....................","...................."]}],"palette":["#dc2020","#2020f8","#f8d8a0","#684020","#f8f8f8","#000000","#f8b800"]}'::jsonb,
     NULL::text, 4),
    ('Plataforma Mario', 'platform', 'pixelmap', 16, 16,
     '{"frames":[{"grid":["0111111111111110","0111111111111110","0000000000000000","0111110111111110","0111110111111110","0000000000000000","0111111110111110","0111111110111110","0000000000000000","0111110111111110","0111110111111110","0000000000000000","0111111111111110","0111111111111110","0000000000000000","0111111111111110"]}],"palette":["#c84b31","#7a2e1d","#e87a5a","#2e1a0a"]}'::jsonb,
     NULL::text, 1),
    ('Moneda Mario', 'coin', 'pixelmap', 12, 12,
     '{"frames":[{"grid":[".....00.....","....0000....","...000000...","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","..00000000..","...000000...","....0000....",".....00....."]},{"grid":[".....11.....","....1111....","...000000...","..00000000..",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.","...000000...","....2222....",".....22....."]},{"grid":["....1111....","...111111...","..00000000..",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.","..00000000..","...222222...","....2222...."]},{"grid":["...111111...","..11111111..",".0000000000.","000000000000","000000000000","000000000000","000000000000","000000000000","000000000000",".0000000000.","..22222222..","...222222..."]},{"grid":["....1111....","...111111...","..00000000..",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.","..00000000..","...222222...","....2222...."]},{"grid":[".....11.....","....1111....","...000000...","..00000000..",".0000000000.",".0000000000.",".0000000000.",".0000000000.",".0000000000.","...000000...","....2222....",".....22....."]}],"palette":["#ffd23f","#fff3a0","#b8830a","#ffffff"]}'::jsonb,
     NULL::text, 6),
    ('Shellcreeper', 'enemy', 'pixelmap', 16, 16,
     '{"frames":[{"grid":["................","....022220....","...02222220...","...02222220...","..0222002220..","..0220002220..","..0222222220..","..0022222200..","...04444440...","...04555540...","...04444440...","....033330....","....600006....","...60000006...","...60000006...","....66..66...."]},{"grid":["................","....022220....","...02222220...","...02222220...","..0222002220..","..0220002220..","..0222222220..","..0022222200..","...04444440...","...04555540...","...04444440...","....033330....","....600006....","...60000006...","...60000006...","....66..66...."]}],"palette":["#30b030","#188018","#58d858","#f8d8a0","#f8f8f8","#000000","#d8d800"]}'::jsonb,
     NULL::text, 2),
    ('Fondo Mario', 'background', 'pixelmap', 16, 16,
     '{"frames":[{"grid":["0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000111111000000","0000111111000000","0000222222000000","0000222222000000","0000111111000000"]}],"palette":["#1a0a2e","#30b030","#188018","#58d858"]}'::jsonb,
     NULL::text, 1)
) AS v(name, category, type, width, height, data, image_url, frame_count)
WHERE NOT EXISTS (SELECT 1 FROM sprites WHERE name = 'Mario Bros');

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
           "loseCondition": { "type": "fall_off" },
           "lives": 3,
           "timer": null
         },
         "screens": {
           "start": { "title": "PLATAFORMAS TERAPÉUTICAS", "subtitle": "Elige un nivel en el menú" }
         },
         "levelDefaults": { "countdown": 3 },
         "levels": [
           {
             "name": "Menú de niveles",
             "countdown": 0,
             "intro": { "title": "NIVELES", "subtitle": "Toca un nivel para jugar", "prompt": "Toca / cierra un dedo sobre un nivel" },
             "physics": { "gravity": { "x": 0, "y": 0 } },
             "world": { "backgroundColor": "#14122a", "camera": { "follow": "none", "scrollY": false } },
             "rules": { "loseCondition": { "type": "none" } },
             "entities": {
               "player": { "spawn": { "x": 200, "y": 560 } },
               "platforms": { "layout": "fixed", "positions": [] },
               "collectibles": { "spawnRate": 0 },
               "enemies": { "count": 0 },
               "zones": [
                 {
                   "id": "n1", "x": 120, "y": 220, "w": 130, "h": 130,
                   "clickable": true, "alwaysLabel": true, "icon": { "label": "1" },
                   "states": { "idle": { "color": "#1c3a2a", "label": "Calentamiento", "onInteract": { "type": "goto_level", "index": 1, "intro": true } } },
                   "initialState": "idle"
                 },
                 {
                   "id": "n2", "x": 280, "y": 220, "w": 130, "h": 130,
                   "clickable": true, "alwaysLabel": true, "icon": { "label": "2" },
                   "states": { "idle": { "color": "#23314a", "label": "Más alto", "onInteract": { "type": "goto_level", "index": 2, "intro": true } } },
                   "initialState": "idle"
                 },
                 {
                   "id": "n3", "x": 120, "y": 400, "w": 130, "h": 130,
                   "clickable": true, "alwaysLabel": true, "icon": { "label": "3" },
                   "states": { "idle": { "color": "#3a1a2e", "label": "Cuidado", "onInteract": { "type": "goto_level", "index": 3, "intro": true } } },
                   "initialState": "idle"
                 },
                 {
                   "id": "n4", "x": 280, "y": 400, "w": 130, "h": 130,
                   "clickable": true, "alwaysLabel": true, "icon": { "label": "4" },
                   "states": { "idle": { "color": "#3a2e10", "label": "Maestría", "onInteract": { "type": "goto_level", "index": 4, "intro": true } } },
                   "initialState": "idle"
                 }
               ]
             }
           },
           {
             "name": "Calentamiento",
             "intro": { "subtitle": "Gana 200 puntos. Sin enemigos." },
             "world": { "backgroundColor": "#12203a" },
             "entities": {
               "platforms": { "procedural": { "count": 12, "minGap": 35, "maxGap": 70, "minWidth": 80, "maxWidth": 160 } },
               "enemies": { "count": 0 }
             },
             "events": [
               { "trigger": { "type": "score", "value": 200 },
                 "actions": [
                   { "type": "flash_text", "text": "¡NIVEL COMPLETADO!", "color": "#3ddc97", "size": "12px", "duration": 1400 },
                   { "type": "goto_level", "index": 0, "delay": 1200 }
                 ] }
             ]
           },
           {
             "name": "Más alto",
             "intro": { "subtitle": "Gana 350 puntos. Plataformas más separadas." },
             "world": { "backgroundColor": "#1a1a3e" },
             "entities": {
               "platforms": { "procedural": { "count": 16, "minGap": 45, "maxGap": 85, "minWidth": 60, "maxWidth": 130 } },
               "enemies": { "count": 0 }
             },
             "events": [
               { "trigger": { "type": "score", "value": 350 },
                 "actions": [
                   { "type": "flash_text", "text": "¡NIVEL COMPLETADO!", "color": "#3ddc97", "size": "12px", "duration": 1400 },
                   { "type": "goto_level", "index": 0, "delay": 1200 }
                 ] }
             ]
           },
           {
             "name": "Cuidado",
             "intro": { "subtitle": "Gana 450 puntos. ¡Aparecen enemigos!", "titleColor": "#ff9c5c" },
             "world": { "backgroundColor": "#2a1030" },
             "entities": {
               "platforms": { "procedural": { "count": 18, "minGap": 45, "maxGap": 90, "minWidth": 55, "maxWidth": 120 } },
               "enemies": { "count": 2, "speed": 50, "ai": "patrol" }
             },
             "events": [
               { "trigger": { "type": "score", "value": 450 },
                 "actions": [
                   { "type": "flash_text", "text": "¡NIVEL COMPLETADO!", "color": "#3ddc97", "size": "12px", "duration": 1400 },
                   { "type": "goto_level", "index": 0, "delay": 1200 }
                 ] }
             ]
           },
           {
             "name": "Maestría",
             "countdown": 5,
             "intro": { "subtitle": "¡Último reto! 600 puntos.", "titleColor": "#ff5c8a" },
             "world": { "backgroundColor": "#2e0a14" },
             "entities": {
               "platforms": { "procedural": { "count": 22, "minGap": 50, "maxGap": 100, "minWidth": 45, "maxWidth": 100 } },
               "enemies": { "count": 3, "speed": 70, "ai": "patrol" }
             },
             "events": [
               { "trigger": { "type": "score", "value": 600 },
                 "actions": [
                   { "type": "flash_text", "text": "¡JUEGO COMPLETADO!", "color": "#ffd23f", "size": "13px", "duration": 1800 },
                   { "type": "goto_level", "index": 0, "delay": 1200 }
                 ] }
             ]
           }
         ]
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

-- ─── JUEGO MARIO BROS ───────────────────────────────────────────
INSERT INTO games (name, description, game_type, config)
SELECT 'Mario Bros Terapeutico',
       'Juego terapeutico inspirado en Mario Bros. Salta entre plataformas, evita enemigos y colecciona monedas. Ejercita los 5 dedos: pulgar(salto), indice(derecha), medio(izquierda), anular(arriba), menique(abajo).',
       'platformer',
       '{"controls":{"fingerMap":{"0":"jump","1":"right","2":"left","3":"up","4":"down"},"fingerMaps":[{"0":"jump","1":"right","2":"left","3":"up","4":"down"},{"0":"jump","1":"right","2":"left","3":"up","4":"down"}],"hands":2,"keyboardFallback":true},"entities":{"collectibles":{"color":"#ffd23f","positions":[{"x":55,"y":82},{"x":345,"y":82},{"x":40,"y":262},{"x":200,"y":262},{"x":360,"y":262},{"x":70,"y":422},{"x":330,"y":422}],"scoreValue":100,"spawnRate":0},"enemies":{"ai":"patrol","color":"#30b030","count":0,"height":16,"positions":[{"x":55,"y":88},{"x":345,"y":88},{"x":40,"y":268},{"x":360,"y":268},{"x":70,"y":428},{"x":330,"y":428}],"speed":40,"width":16},"platforms":{"color":"#c84b31","height":14,"layout":"positions","oneWay":true,"positions":[{"h":14,"w":110,"x":55,"y":100},{"h":14,"w":110,"x":345,"y":100},{"h":14,"w":100,"x":40,"y":280},{"h":14,"w":100,"x":200,"y":280},{"h":14,"w":100,"x":360,"y":280},{"h":14,"w":140,"x":70,"y":440},{"h":14,"w":140,"x":330,"y":440},{"h":14,"w":400,"x":200,"y":570}],"static":true,"width":80},"player":{"color":"#dc2020","height":26,"jumpForce":-380,"physics":{"bounce":0,"collideWorldBounds":true},"spawn":{"x":200,"y":520},"speed":160,"width":20}},"events":[{"actions":[{"ai":"patrol","color":"#30b030","count":1,"entity":"enemies","speed":50,"type":"spawn"},{"color":"#ff5c8a","duration":1500,"size":"12px","text":"CUIDADO!","type":"flash_text"}],"trigger":{"delay":25,"repeat":true,"type":"timer"}},{"actions":[{"color":"#ffd23f","duration":2000,"size":"10px","text":"MITAD DEL NIVEL!","type":"flash_text"}],"trigger":{"type":"score","value":500}},{"actions":[{"color":"#ff5c8a","duration":2000,"size":"12px","text":"ULTIMA VIDA!","type":"flash_text"},{"color":"#ff0000","duration":3000,"target":"player","type":"tint"}],"trigger":{"type":"lives","value":1}}],"metadata":{"description":"Juego terapeutico inspirado en Mario Bros. Salta entre plataformas, evita enemigos y colecciona monedas. Ejercita los 5 dedos: pulgar(salto), indice(derecha), medio(izquierda), anular(arriba), menique(abajo).","difficulty":"easy","estimatedDuration":300,"name":"Mario Bros Terapeutico","targetFingers":[0,1,2,3,4],"type":"platformer"},"physics":{"debug":false,"gravity":{"x":0,"y":400},"type":"arcade"},"rules":{"lives":3,"loseCondition":{"type":"fall_off"},"timer":null,"winCondition":{"target":1000,"type":"score"}},"screens":{"gameOver":{"backgroundColor":"#1a0a2e","losePrompt":"SPACE / Cierra un dedo para reintentar","loseTitle":"GAME OVER","loseTitleColor":"#ff5c8a","subtitleColor":"#ffd23f","winPrompt":"SPACE / Cierra un dedo para continuar","winTitle":"NIVEL COMPLETADO!","winTitleColor":"#3ddc97"},"start":{"backgroundColor":"#1a0a2e","delay":400,"prompt":"Salta! [SPACE / dedo pulgar]","promptColor":"#ffffff","promptSize":"7px","subtitle":"Terapeutico","subtitleColor":"#ffd23f","subtitleSize":"10px","title":"MARIO BROS","titleColor":"#dc2020","titleSize":"18px"}},"sprites":{"background":{"sprite_id":10},"coin":{"sprite_id":8},"enemy":{"sprite_id":9},"platform":{"sprite_id":7},"player":{"sprite_id":6}},"version":"1.0","world":{"backgroundColor":"#1a0a2e","camera":{"follow":null,"scrollX":false,"scrollY":false},"height":600,"width":400}}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Mario Bros Terapeutico');

-- Migración idempotente: habilita 2 manos en el Mario terapéutico (juego Phaser).
-- Sólo aplica si aún no tiene multi-mano configurado. Para BDs ya inicializadas.
UPDATE games
SET config = jsonb_set(
    jsonb_set(config, '{controls,hands}', '2'::jsonb, true),
    '{controls,fingerMaps}',
    '[{"0":"jump","1":"right","2":"left","3":"up","4":"down"},{"0":"jump","1":"right","2":"left","3":"up","4":"down"}]'::jsonb,
    true)
WHERE name = 'Mario Bros Terapeutico'
  AND COALESCE((config->'controls'->>'hands')::int, 1) < 2;

-- ─── SPRITES: Pumpkin Panic ────────────────────────────────────
INSERT INTO sprites (name, category, type, width, height, data, image_url, frame_count)
SELECT * FROM (VALUES
    ('Granjero Asustado', 'player', 'pixelmap', 16, 20,
     '{"palette":["#8b4513","#deb887","#f4c896","#2e8b57","#1a5c2e","#4169e1","#2a3d8f","#000000","#ffffff","#ff6347","#c84b31"],"frames":[{"grid":["....00000000....","....00000000....","....08880888....","....08880888....","..22222222222222","..22222222222222","..33333333333333","..33333333333333","..44444444444444","..33333333333333","..33333333333333","..33333333333333","..55555555555555","..55555555555555","..66666666666666","..66666666666666","....5555..5555..","....5555..5555..","....aaaa..aaaa..","....aaaa..aaaa.."]},{"grid":["....00000000....","....00000000....","....08880888....","....08880888....","..22222222222222","..22222222222222","..33333333333333","..33333333333333","..44444444444444","..33333333333333","..33333333333333","..33333333333333","..55555555555555","..55555555555555","..66666666666666","..66666666666666","....5555..5555..","....aaaa..5555..","....aaaa..aaaa..","..........aaaa.."]},{"grid":["....00000000....","....00000000....","....08980898....","....08880888....","..22222222222222","..22222222222222","..33333333333333","..33333333333333","..44444444444444","..33333333333333","..33333333333333","..33333333333333","..55555555555555","..55555555555555","..66666666666666","..66666666666666","....5555..5555..","....5555..5555..","....aaaa..aaaa..","....aaaa..aaaa.."]}]}'::jsonb,
     NULL::text, 3),
    ('Calabaza', 'coin', 'pixelmap', 14, 14,
     '{"palette":["#ff8c00","#ff6600","#2e8b57","#1a5c2e","#000000","#ffa500"],"frames":[{"grid":["......2222......","....22332222....","..000000000000..","..000000000000..","..005500055000..","..005500055000..","..000000000000..","..000000000000..","..000044000000..","..000044000000..","..000000000000..","..111111111111..","....11111111....","......1111......"]},{"grid":["......3322......","....22332222....","..555000005500..","..000000000000..","..005500055000..","..005500055000..","..000000000000..","..000000000000..","..000044000000..","..000044000000..","..000000000000..","..111111111111..","....11111111....","......1111......"]},{"grid":["......2222......","....33332222....","..000000000000..","..550000000055..","..005500055000..","..005500055000..","..000000000000..","..000000000000..","..000044000000..","..000044000000..","..000000000000..","..111111111111..","....11111111....","......1111......"]}]}'::jsonb,
     NULL::text, 3),
    ('Fantasma', 'enemy', 'pixelmap', 16, 18,
     '{"palette":["#e8e8ff","#c8c8e8","#6a0dad","#4b0082","#ff0000","#000000"],"frames":[{"grid":["....00000000....","..000000000000..","..000000000000..","0000000000000000","0000550000550000","0000550000550000","0004440004440000","0000000000000000","0000000000000000","0000033333300000","0000033333300000","0000000000000000","0000000000000000","0000000000000000","0011000000001100","0011000000001100","0011001100110011","0011001100110011"]},{"grid":["....00000000....","..000000000000..","..000000000000..","0000000000000000","0000055000055000","0000055000055000","0000044400044000","0000000000000000","0000000000000000","0000033333300000","0000033333300000","0000000000000000","0000000000000000","0000000000000000","0000110000110000","0000110000110000","0011001100110011","0011001100110011"]}]}'::jsonb,
     NULL::text, 2),
    ('Tierra Granja', 'platform', 'pixelmap', 16, 16,
     '{"palette":["#8b4513","#654321","#2e8b57","#a0522d","#556b2f"],"frames":[{"grid":["2222222222222222","2244224422442244","0000000000000000","0033003300330033","0000000000000000","0000000000000000","1111111111111111","1100110011001100","1111111111111111","1100110011001100","1111111111111111","1111111111111111","1100110011001100","1111111111111111","1100110011001100","1111111111111111"]}]}'::jsonb,
     NULL::text, 1),
    ('Cerca Madera', 'other', 'pixelmap', 16, 16,
     '{"palette":["#8b4513","#a0522d","#654321","#deb887"],"frames":[{"grid":["..00....00....00","..00....00....00","..00....00....00","1111111111111111","1111111111111111","..00....00....00","..00....00....00","..00....00....00","2222222222222222","2222222222222222","..00....00....00","..00....00....00","..00....00....00","..00....00....00","..00....00....00","..00....00....00"]}]}'::jsonb,
     NULL::text, 1),
    ('Fondo Granja Noche', 'background', 'pixelmap', 20, 20,
     '{"palette":["#0a0a2e","#1a1a3e","#2a1a4e","#ffd700","#c0c0c0","#1a3a1a"],"frames":[{"grid":["00000000000000000000","00000000030000000000","00000000000000000000","00100000000000000040","00000000000000000000","00000000000000001000","00000300000000000000","00000000000000000000","11111111111111111111","11111111111111111111","22222222222222222222","22222222222222222222","55555555555555555555","55555555555555555555","55555555555555555555","55555555555555555555","55555555555555555555","55555555555555555555","55555555555555555555","55555555555555555555"]}]}'::jsonb,
     NULL::text, 1)
) AS v(name, category, type, width, height, data, image_url, frame_count)
WHERE NOT EXISTS (SELECT 1 FROM sprites WHERE name = 'Granjero Asustado');

-- ─── JUEGO POR DEFECTO: Pumpkin Panic ─────────────────────────
INSERT INTO games (name, description, game_type, config)
SELECT 'Pumpkin Panic - Granja Embrujada',
       'Recoge calabazas en una granja embrujada mientras esquivas fantasmas. Usa todos los dedos para moverte, saltar y agacharte.',
       'platformer',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Pumpkin Panic - Granja Embrujada",
           "type": "platformer",
           "targetFingers": [0, 1, 2, 3, 4],
           "difficulty": "medium",
           "description": "Recoge calabazas en la granja embrujada esquivando fantasmas. Ejercita todos los dedos.",
           "estimatedDuration": 300,
           "theme": "halloween"
         },
         "physics": {
           "type": "arcade",
           "gravity": { "x": 0, "y": 500 },
           "debug": false
         },
         "world": {
           "width": 600,
           "height": 400,
           "backgroundColor": "#0a0a2e",
           "camera": {
             "follow": "player",
             "scrollY": false,
             "scrollX": true
           }
         },
         "entities": {
           "player": {
             "spawn": { "x": 50, "y": 300 },
             "width": 16,
             "height": 20,
             "color": "#deb887",
             "speed": 140,
             "jumpForce": -380,
             "physics": {
               "bounce": 0.1,
               "collideWorldBounds": true
             }
           },
           "platforms": {
             "static": true,
             "color": "#8b4513",
             "width": 80,
             "height": 16,
             "layout": "procedural",
             "procedural": {
               "count": 20,
               "minGap": 30,
               "maxGap": 70,
               "minWidth": 50,
               "maxWidth": 140
             }
           },
           "collectibles": {
             "color": "#ff8c00",
             "spawnRate": 0.6,
             "scoreValue": 100,
             "name": "calabaza"
           },
           "enemies": {
             "count": 5,
             "color": "#e8e8ff",
             "width": 16,
             "height": 18,
             "ai": "float",
             "speed": 50,
             "name": "fantasma"
           }
         },
         "controls": {
           "fingerMap": {
             "0": "jump",
             "1": "right",
             "2": "left",
             "3": "duck",
             "4": "action"
           },
           "keyboardFallback": true
         },
         "rules": {
           "winCondition": {
             "type": "score",
             "target": 1000
           },
           "loseCondition": {
             "type": "enemy_touch"
           },
           "lives": 3,
           "timer": 180
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Pumpkin Panic - Granja Embrujada');

-- Link sprites to Pumpkin Panic game config
UPDATE games SET config = config || jsonb_build_object('sprites', jsonb_build_object(
    'player', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Granjero Asustado' LIMIT 1)),
    'platform', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Tierra Granja' LIMIT 1)),
    'coin', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Calabaza' LIMIT 1)),
    'enemy', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Fantasma' LIMIT 1)),
    'background', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Fondo Granja Noche' LIMIT 1))
))
WHERE name = 'Pumpkin Panic - Granja Embrujada' AND NOT (config ? 'sprites');

-- ─── JUEGO: Prince of Persia (NES, emulador genérico) ──────────
-- Requiere la ROM en static/roms/prince.nes (servida en /static/roms/prince.nes).
INSERT INTO games (name, description, game_type, config)
SELECT 'Prince of Persia',
       'El clásico Prince of Persia de NES corriendo con Nostalgist.js y controlado por gestos. Configurado a 2 manos: Mano 1 = dpad + start, Mano 2 = A(salto)/B(espada).',
       'emulator',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Prince of Persia",
           "type": "emulator",
           "targetFingers": [0, 1, 2, 3, 4],
           "difficulty": "medium",
           "description": "Prince of Persia (NES) en emulador, control por gestos.",
           "estimatedDuration": 3600
         },
         "emulator": {
           "core": "fceumm",
           "rom": "static/roms/prince.nes",
           "aspectRatio": "256/240",
           "tapButtons": ["start", "select"]
         },
         "controls": {
           "hands": 2,
           "fingerMap": { "0": "left", "1": "right", "2": "up", "3": "down", "4": "start" },
           "fingerMaps": [
             { "0": "left", "1": "right", "2": "up", "3": "down", "4": "start" },
             { "0": "a", "1": "b", "2": "none", "3": "none", "4": "none" }
           ],
           "keyboardFallback": true
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Prince of Persia');

-- ─── JUEGO: Super Mario Bros. 3 (NES, emulador genérico) ───────
-- Requiere la ROM en static/roms/smb3.nes (servida en /static/roms/smb3.nes).
INSERT INTO games (name, description, game_type, config)
SELECT 'Super Mario Bros. 3',
       'El clásico Super Mario Bros. 3 de NES corriendo con Nostalgist.js y controlado por gestos. Pulgar=izquierda, índice=A(salto), medio=derecha, anular=B(correr), meñique=START.',
       'emulator',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Super Mario Bros. 3",
           "type": "emulator",
           "targetFingers": [0, 1, 2, 3, 4],
           "difficulty": "medium",
           "description": "Super Mario Bros. 3 (NES) en emulador, control por gestos.",
           "estimatedDuration": 3600
         },
         "emulator": {
           "core": "fceumm",
           "rom": "static/roms/smb3.nes",
           "aspectRatio": "256/240",
           "tapButtons": ["start", "select"]
         },
         "controls": {
           "hands": 2,
           "fingerMap": { "0": "left", "1": "right", "2": "up", "3": "down", "4": "start" },
           "fingerMaps": [
             { "0": "left", "1": "right", "2": "up", "3": "down", "4": "select" },
             { "0": "a", "1": "b", "2": "start", "3": "none", "4": "none" }
           ],
           "keyboardFallback": true
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Super Mario Bros. 3');

-- ─── JUEGO: Flappy Bird (NES, emulador genérico) ───────────────
-- Requiere la ROM en static/roms/flappy.nes (servida en /static/roms/flappy.nes).
-- Juego de UN solo botón: aletear = A. Ideal para terapia de un dedo.
INSERT INTO games (name, description, game_type, config)
SELECT 'Flappy Bird',
       'Flappy Bird de NES corriendo con Nostalgist.js y controlado por gestos. Un solo botón: cierra el índice para aletear (A); meñique = START.',
       'emulator',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Flappy Bird",
           "type": "emulator",
           "targetFingers": [1, 4],
           "difficulty": "easy",
           "description": "Flappy Bird (NES) en emulador, control por gestos.",
           "estimatedDuration": 600
         },
         "emulator": {
           "core": "fceumm",
           "rom": "static/roms/flappy.nes",
           "aspectRatio": "256/240",
           "tapButtons": ["start", "select"]
         },
         "controls": {
           "fingerMap": { "0": "a", "1": "a", "2": "a", "3": "a", "4": "start" },
           "keyboardFallback": true
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Flappy Bird');

-- ─── CONFIG DE CONTROLES POR PACIENTE+JUEGO ───────────────────
-- sensitivities / finger_map soportan dos formas (multi-mano disponible en todo juego):
--   1 mano  → sensitivities: [50,50,50,50,50]        finger_map: {"0":"jump",...}
--   N manos → sensitivities: [[..5..],[..5..]]        finger_map: [{"0":..},{"0":..}]
-- JSONB acepta ambas; el frontend normaliza según controls.hands del juego.
CREATE TABLE IF NOT EXISTS player_game_config (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id) ON DELETE CASCADE,
    game_id INT REFERENCES games(id) ON DELETE CASCADE,
    sensitivities JSONB NOT NULL DEFAULT '[50,50,50,50,50]',
    finger_map JSONB NOT NULL DEFAULT '{"0":"jump","1":"right","2":"left","3":"none","4":"none"}',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(patient_id, game_id)
);

-- ─── MIGRACIONES IDEMPOTENTES (se ejecutan siempre) ──────────
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'role_id'
    ) THEN
        ALTER TABLE users ADD COLUMN role_id INT REFERENCES roles(id);
    END IF;
END $$;
