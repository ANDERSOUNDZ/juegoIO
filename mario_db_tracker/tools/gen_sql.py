"""Generate SQL INSERT statements for Mario Bros sprites and game."""
import json, urllib.request, http.cookiejar

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
))

def escape_sql(val):
    """Escape a Python value for SQL (single-quote doubling)."""
    if val is None:
        return "NULL"
    s = json.dumps(val, ensure_ascii=False, separators=(",", ":"))
    s = s.replace("'", "''")
    return f"'{s}'::jsonb"

def escape_str(val):
    if val is None:
        return "NULL::text"
    s = str(val).replace("'", "''")
    return f"'{s}'"

# Fetch sprites
sprites = {}
for sid in [6, 7, 8, 9, 10]:
    r = opener.open(f"{BASE}/api/sprites/{sid}")
    sprites[sid] = json.loads(r.read())

# Generate sprite INSERT
import sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', closefd=False)
print("-- --- SPRITES MARIO BROS ----------------------------------")
print("INSERT INTO sprites (name, category, type, width, height, data, image_url, frame_count)")
print("SELECT * FROM (VALUES")
vals = []
for sid in [6, 7, 8, 9, 10]:
    s = sprites[sid]
    name = escape_str(s["name"])
    cat = escape_str(s["category"])
    typ = escape_str(s["type"])
    w = s["width"]
    h = s["height"]
    data = escape_sql(s["data"])
    img = "NULL::text"
    fc = s["frame_count"]
    vals.append(f"    ({name}, {cat}, {typ}, {w}, {h}, {data}, {img}, {fc})")
print(",\n".join(vals))
print(") AS v(name, category, type, width, height, data, image_url, frame_count)")
print("WHERE NOT EXISTS (SELECT 1 FROM sprites WHERE name = 'Mario Bros');")
print()

# Fetch game config
r = opener.open(f"{BASE}/api/games/2/config")
cfg = json.loads(r.read())
cfg_json = json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
cfg_escaped = cfg_json.replace("'", "''")

print("-- --- JUEGO MARIO BROS ------------------------------------")
print("INSERT INTO games (name, description, game_type, config)")
print("SELECT 'Mario Bros Terapeutico',")
desc = "Juego terapeutico inspirado en Mario Bros. Salta entre plataformas, evita enemigos y colecciona monedas. Ejercita los 5 dedos: pulgar(salto), indice(derecha), medio(izquierda), anular(arriba), menique(abajo)."
desc_escaped = desc.replace("'", "''")
print(f"       '{desc_escaped}',")
print(f"       'platformer',")
print(f"       '{cfg_escaped}'::jsonb")
print("WHERE NOT EXISTS (SELECT 1 FROM games WHERE name = 'Mario Bros Terapeutico');")
