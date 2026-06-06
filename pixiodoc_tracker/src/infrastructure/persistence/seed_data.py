"""Default game and sprite seed data (SQL statements, executed on startup if games table is empty)."""

SEED_SQL = """
-- ─── SPRITES POR DEFECTO ────────────────────────────────────────
INSERT INTO sprites (name, category, type, width, height, data, image_url, frame_count)
SELECT * FROM (VALUES
    ('Pixo Hero', 'player', 'pixelmap', 20, 26,
     '{"palette":["#3ddc97","#1f7a4f","#ffd23f","#5a2a8a","#f4c896","#c89868","#1a0a2e","#ff8a8a","#ffd23f","#b8830a","#7a3ac8","#4a1a8a","#2a1a0a","#fff3a0"],"frames":[{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa......","..888aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa888.","..999aaaaaaaaaaa999.","..444aaaaaaaaaaa444.","..444bbbbbbbbbbb444.",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....","....ccccc..ccccc...."]},{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa......","..888aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa888.","..999aaaaaaaaaaa999.","..444aaaaaaaaaaa444.","..444bbbbbbbbbbb444.",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..ccccc....","....ccccc..ccccc...."]},{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa..888.",".....aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa999.","..888aaaaaaaaaaa444.","..999aaaaaaaaaaa444.","..444bbbbbbbbbbb....","..444aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....ccccc.aaaa.....",".....ccccc.ccccc...."]},{"grid":["...00000000000000...","...00000222000000...","...00002222200000...","...00000000000000...",".10000000000000001..",".10000000000000001..",".10000000011111111..","...334444444444411..",".....44444444444....",".....44466444664....",".....44466444664....",".....47744444774....",".....55555555555....",".......aa555aa......","..888aaaa888aaaa888.","..888aaaa888aaaa888.","..888aada888adaa888.","..888aaaa888aaaa888.","..999aaaaaaaaaaa999.","..444aaaaaaaaaaa444.","..444bbbbbbbbbbb444.",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....",".....aaaa..aaaa.....","....ccccc..ccccc...."]}]}'::jsonb,
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

-- ─── JUEGO: Plataformas Terap\u00e9uticas ──────────────────────────
INSERT INTO games (name, description, game_type, config)
SELECT 'Plataformas Terap\u00e9uticas',
       'Platformer b\u00e1sico para ejercitar pulgar, \u00edndice y medio. Salta entre plataformas y recoge monedas.',
       'platformer',
       '{"version":"1.0","metadata":{"name":"Plataformas Terap\u00e9uticas","type":"platformer","targetFingers":[0,1,2],"difficulty":"easy","description":"Platformer b\u00e1sico para rehabilitaci\u00f3n de motricidad fina","estimatedDuration":300},"physics":{"type":"arcade","gravity":{"x":0,"y":400},"debug":false},"world":{"width":400,"height":600,"backgroundColor":"#1a1a2e","camera":{"follow":"none","scrollY":false,"scrollX":false}},"entities":{"player":{"spawn":{"x":200,"y":500},"width":20,"height":26,"color":"#3ddc97","speed":160,"jumpForce":-350,"physics":{"bounce":0.2,"collideWorldBounds":true}},"platforms":{"static":true,"color":"#4a90d9","width":80,"height":14,"layout":"fixed","positions":[]},"collectibles":{"color":"#ffd23f","spawnRate":0,"scoreValue":50},"enemies":{"count":0,"color":"#ff6b6b","width":16,"height":16,"ai":"patrol","speed":55}},"controls":{"fingerMap":{"0":"jump","1":"right","2":"left","3":"none","4":"none"},"keyboardFallback":true},"rules":{"loseCondition":{"type":"fall_off"},"lives":3,"timer":null},"screens":{"start":{"title":"PLATAFORMAS TERAP\u00c9UTICAS","subtitle":"Elige un nivel en el men\u00fa"}},"levelDefaults":{"countdown":3},"levels":[{"name":"Men\u00fa de niveles","countdown":0,"intro":{"title":"NIVELES","subtitle":"Toca un nivel para jugar","prompt":"Toca / cierra un dedo sobre un nivel"},"physics":{"gravity":{"x":0,"y":0}},"world":{"backgroundColor":"#14122a"},"rules":{"loseCondition":{"type":"none"}},"entities":{"player":{"spawn":{"x":200,"y":560}},"platforms":{"layout":"fixed","positions":[]},"collectibles":{"spawnRate":0},"enemies":{"count":0},"zones":[{"id":"n1","x":120,"y":220,"w":130,"h":130,"clickable":true,"alwaysLabel":true,"icon":{"label":"1"},"states":{"idle":{"color":"#1c3a2a","label":"Calentamiento","onInteract":{"type":"goto_level","index":1,"intro":true}}},"initialState":"idle"},{"id":"n2","x":280,"y":220,"w":130,"h":130,"clickable":true,"alwaysLabel":true,"icon":{"label":"2"},"states":{"idle":{"color":"#23314a","label":"M\u00e1s alto","onInteract":{"type":"goto_level","index":2,"intro":true}}},"initialState":"idle"},{"id":"n3","x":120,"y":400,"w":130,"h":130,"clickable":true,"alwaysLabel":true,"icon":{"label":"3"},"states":{"idle":{"color":"#3a1a2e","label":"Cuidado","onInteract":{"type":"goto_level","index":3,"intro":true}}},"initialState":"idle"},{"id":"n4","x":280,"y":400,"w":130,"h":130,"clickable":true,"alwaysLabel":true,"icon":{"label":"4"},"states":{"idle":{"color":"#3a2e10","label":"Maestr\u00eda","onInteract":{"type":"goto_level","index":4,"intro":true}}},"initialState":"idle"}]}},{"name":"Calentamiento","intro":{"subtitle":"Sube y recoge todas las monedas."},"world":{"width":400,"height":1150,"backgroundColor":"#12203a","camera":{"follow":"player","scrollY":true,"scrollX":false}},"entities":{"player":{"spawn":{"x":200,"y":1105}},"platforms":{"layout":"fixed","positions":[{"x":200,"y":1135,"w":400,"h":20},{"x":91,"y":1065,"w":170,"h":14},{"x":194,"y":946,"w":170,"h":14},{"x":104,"y":826,"w":150,"h":14},{"x":216,"y":707,"w":170,"h":14},{"x":131,"y":587,"w":150,"h":14},{"x":218,"y":468,"w":160,"h":14},{"x":108,"y":348,"w":140,"h":14}]},"collectibles":{"scoreValue":50,"positions":[{"x":108,"y":324},{"x":131,"y":563},{"x":91,"y":1041},{"x":104,"y":802},{"x":194,"y":922}]},"enemies":{"count":0}},"events":[{"trigger":{"type":"collect_count","value":5},"actions":[{"type":"flash_text","text":"\u00a1NIVEL COMPLETADO!","color":"#3ddc97","size":"13px","duration":1600},{"type":"goto_level","index":0,"delay":1200}]}]},{"name":"M\u00e1s alto","intro":{"subtitle":"Trepa m\u00e1s alto. Cuidado con el enemigo."},"world":{"width":400,"height":1500,"backgroundColor":"#1a1a3e","camera":{"follow":"player","scrollY":true,"scrollX":false}},"entities":{"player":{"spawn":{"x":200,"y":1455}},"platforms":{"layout":"fixed","positions":[{"x":200,"y":1485,"w":400,"h":20},{"x":108,"y":1415,"w":150,"h":14},{"x":197,"y":1296,"w":170,"h":14},{"x":80,"y":1176,"w":140,"h":14},{"x":200,"y":1057,"w":160,"h":14},{"x":108,"y":937,"w":140,"h":14},{"x":204,"y":818,"w":140,"h":14},{"x":81,"y":698,"w":150,"h":14},{"x":196,"y":579,"w":170,"h":14},{"x":88,"y":460,"w":140,"h":14}]},"collectibles":{"scoreValue":50,"positions":[{"x":88,"y":436},{"x":197,"y":1272},{"x":81,"y":674},{"x":196,"y":555},{"x":200,"y":1033},{"x":204,"y":794}]},"enemies":{"ai":"patrol","speed":55,"positions":[{"x":200,"y":1460,"range":170}]}},"events":[{"trigger":{"type":"collect_count","value":6},"actions":[{"type":"flash_text","text":"\u00a1NIVEL COMPLETADO!","color":"#3ddc97","size":"13px","duration":1600},{"type":"goto_level","index":0,"delay":1200}]}]},{"name":"Cuidado","intro":{"subtitle":"Subida larga con enemigos patrullando."},"world":{"width":400,"height":1850,"backgroundColor":"#2a1030","camera":{"follow":"player","scrollY":true,"scrollX":false}},"entities":{"player":{"spawn":{"x":200,"y":1805}},"platforms":{"layout":"fixed","positions":[{"x":200,"y":1835,"w":400,"h":20},{"x":88,"y":1765,"w":150,"h":14},{"x":192,"y":1646,"w":160,"h":14},{"x":81,"y":1526,"w":150,"h":14},{"x":209,"y":1407,"w":160,"h":14},{"x":107,"y":1287,"w":170,"h":14},{"x":202,"y":1168,"w":140,"h":14},{"x":96,"y":1048,"w":160,"h":14},{"x":213,"y":929,"w":140,"h":14},{"x":93,"y":810,"w":170,"h":14},{"x":219,"y":690,"w":160,"h":14},{"x":133,"y":571,"w":150,"h":14}]},"collectibles":{"scoreValue":50,"positions":[{"x":133,"y":547},{"x":209,"y":1383},{"x":96,"y":1024},{"x":213,"y":905},{"x":93,"y":786},{"x":81,"y":1502},{"x":219,"y":666}]},"enemies":{"ai":"patrol","speed":55,"positions":[{"x":200,"y":1810,"range":170},{"x":192,"y":1630,"range":66}]}},"events":[{"trigger":{"type":"collect_count","value":7},"actions":[{"type":"flash_text","text":"\u00a1NIVEL COMPLETADO!","color":"#3ddc97","size":"13px","duration":1600},{"type":"goto_level","index":0,"delay":1200}]}]},{"name":"Maestr\u00eda","intro":{"subtitle":"El ascenso final. Conc\u00e9ntrate."},"world":{"width":400,"height":2200,"backgroundColor":"#2e0a14","camera":{"follow":"player","scrollY":true,"scrollX":false}},"entities":{"player":{"spawn":{"x":200,"y":2155}},"platforms":{"layout":"fixed","positions":[{"x":200,"y":2185,"w":400,"h":20},{"x":94,"y":2115,"w":170,"h":14},{"x":183,"y":1996,"w":140,"h":14},{"x":88,"y":1876,"w":150,"h":14},{"x":174,"y":1757,"w":150,"h":14},{"x":89,"y":1637,"w":140,"h":14},{"x":204,"y":1518,"w":160,"h":14},{"x":94,"y":1398,"w":170,"h":14},{"x":192,"y":1279,"w":160,"h":14},{"x":86,"y":1160,"w":160,"h":14},{"x":172,"y":1040,"w":150,"h":14},{"x":76,"y":921,"w":140,"h":14},{"x":204,"y":801,"w":160,"h":14},{"x":77,"y":682,"w":140,"h":14}]},"collectibles":{"scoreValue":50,"positions":[{"x":77,"y":658},{"x":88,"y":1852},{"x":172,"y":1016},{"x":76,"y":897},{"x":204,"y":777},{"x":192,"y":1255},{"x":86,"y":1136},{"x":174,"y":1733}]},"enemies":{"ai":"patrol","speed":55,"positions":[{"x":200,"y":2160,"range":170},{"x":76,"y":905,"range":56},{"x":183,"y":1980,"range":56}]}},"events":[{"trigger":{"type":"collect_count","value":8},"actions":[{"type":"flash_text","text":"\u00a1NIVEL COMPLETADO!","color":"#3ddc97","size":"13px","duration":1600},{"type":"goto_level","index":0,"delay":1200}]}],"countdown":5}]}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Plataformas Terap\u00e9uticas');

-- Link sprites: Plataformas Terap\u00e9uticas
UPDATE games SET config = (config::jsonb || jsonb_build_object('sprites', jsonb_build_object(
    'player', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'player' LIMIT 1)),
    'platform', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'platform' LIMIT 1)),
    'coin', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'coin' LIMIT 1)),
    'enemy', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE category = 'enemy' LIMIT 1))
)))::json
WHERE name = 'Plataformas Terap\u00e9uticas' AND config->>'sprites' IS NULL;

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

-- ─── JUEGO: Pumpkin Panic ─────────────────────────────────────
INSERT INTO games (name, description, game_type, config)
SELECT 'Pumpkin Panic - Granja Embrujada',
       'Recoge calabazas en una granja embrujada mientras esquivas fantasmas.',
       'platformer',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Pumpkin Panic - Granja Embrujada", "type": "platformer",
           "targetFingers": [0, 1, 2, 3, 4], "difficulty": "medium",
           "description": "Recoge calabazas esquivando fantasmas.",
           "estimatedDuration": 300, "theme": "halloween"
         },
         "physics": { "type": "arcade", "gravity": { "x": 0, "y": 500 }, "debug": false },
         "world": {
           "width": 600, "height": 400, "backgroundColor": "#0a0a2e",
           "camera": { "follow": "player", "scrollY": false, "scrollX": true }
         },
         "entities": {
           "player": {
             "spawn": { "x": 50, "y": 300 }, "width": 16, "height": 20,
             "color": "#deb887", "speed": 140, "jumpForce": -380,
             "physics": { "bounce": 0.1, "collideWorldBounds": true }
           },
           "platforms": {
             "static": true, "color": "#8b4513", "width": 80, "height": 16,
             "layout": "procedural",
             "procedural": { "count": 20, "minGap": 30, "maxGap": 70, "minWidth": 50, "maxWidth": 140 }
           },
           "collectibles": { "color": "#ff8c00", "spawnRate": 0.6, "scoreValue": 100, "name": "calabaza" },
           "enemies": { "count": 5, "color": "#e8e8ff", "width": 16, "height": 18, "ai": "float", "speed": 50, "name": "fantasma" }
         },
         "controls": {
           "fingerMap": { "0": "jump", "1": "right", "2": "left", "3": "duck", "4": "action" },
           "keyboardFallback": true
         },
         "rules": {
           "winCondition": { "type": "score", "target": 1000 },
           "loseCondition": { "type": "enemy_touch" },
           "lives": 3, "timer": 180
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Pumpkin Panic - Granja Embrujada');

-- Link sprites: Pumpkin Panic
UPDATE games SET config = (config::jsonb || jsonb_build_object('sprites', jsonb_build_object(
    'player', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Granjero Asustado' LIMIT 1)),
    'platform', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Tierra Granja' LIMIT 1)),
    'coin', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Calabaza' LIMIT 1)),
    'enemy', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Fantasma' LIMIT 1)),
    'background', jsonb_build_object('sprite_id', (SELECT id FROM sprites WHERE name = 'Fondo Granja Noche' LIMIT 1))
)))::json
WHERE name = 'Pumpkin Panic - Granja Embrujada' AND config->>'sprites' IS NULL;

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
       'Flappy Bird de NES corriendo con Nostalgist.js y controlado por gestos. Solo el índice tiene asignación (START); el resto de dedos sin asignar.',
       'emulator',
       '{
         "version": "1.0",
         "metadata": {
           "name": "Flappy Bird",
           "type": "emulator",
           "targetFingers": [1],
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
           "fingerMap": { "0": "none", "1": "start", "2": "none", "3": "none", "4": "none" },
           "keyboardFallback": true
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Flappy Bird');

-- ─── JUEGO: D-Pad Hero 2 (NES, emulador genérico) ──────────────
-- Requiere la ROM en static/roms/dpadhero2.nes (servida en /static/roms/dpadhero2.nes).
-- Juego de ritmo (tipo Guitar Hero): las notas caen en 4 carriles = cruceta.
-- Default a 2 manos: Mano 1 = config de referencia del paciente
-- (pulgar=izq, índice=der, medio=select, anular=B, meñique=A); Mano 2 = índice=START.
INSERT INTO games (name, description, game_type, config)
SELECT 'D-Pad Hero 2',
       'D-Pad Hero 2 de NES corriendo con Nostalgist.js y controlado por gestos. Configurado a 2 manos: Mano 1 = pulgar=izquierda, índice=derecha, medio=select, anular=B, meñique=A; Mano 2 = índice=START.',
       'emulator',
       '{
         "version": "1.0",
         "metadata": {
           "name": "D-Pad Hero 2",
           "type": "emulator",
           "targetFingers": [0, 1, 2, 3, 4],
           "difficulty": "medium",
           "description": "D-Pad Hero 2 (NES) en emulador, juego de ritmo por gestos.",
           "estimatedDuration": 1200
         },
         "emulator": {
           "core": "fceumm",
           "rom": "static/roms/dpadhero2.nes",
           "aspectRatio": "256/240",
           "tapButtons": ["start", "select"]
         },
         "controls": {
           "hands": 2,
           "fingerMap": { "0": "left", "1": "right", "2": "select", "3": "b", "4": "a" },
           "fingerMaps": [
             { "0": "left", "1": "right", "2": "select", "3": "b", "4": "a" },
             { "0": "none", "1": "start", "2": "none", "3": "none", "4": "none" }
           ],
           "keyboardFallback": true
         }
       }'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'D-Pad Hero 2');

"""
