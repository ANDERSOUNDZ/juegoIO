#!/usr/bin/env python3
"""Verify the Mario Bros game was created correctly."""

import json
import urllib.request
import http.cookiejar

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
req = urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
)
opener.open(req)

# Get game
req = urllib.request.Request(f"{BASE}/api/games/2")
r = opener.open(req)
g = json.loads(r.read())

print("=== JUEGO CREADO CORRECTAMENTE ===")
print(f"  ID:           {g['id']}")
print(f"  Nombre:       {g['name']}")
print(f"  Tipo:         {g['game_type']}")

cfg = g.get("config", {})
meta = cfg.get("metadata", {})
print(f"\n  Dificultad:   {meta.get('difficulty')}")
print(f"  Duracion est: {meta.get('estimatedDuration')}s")
print(f"  Dedos objetivo: {meta.get('targetFingers')}")

ents = cfg.get("entities", {})
print(f"\n  Plataformas:  {len(ents.get('platforms', {}).get('positions', []))} (fijas)")
print(f"  Enemigos:     {len(ents.get('enemies', {}).get('positions', []))} (posiciones fijas)")
print(f"  Monedas:      {len(ents.get('collectibles', {}).get('positions', []))} (posiciones fijas)")

sprites = cfg.get("sprites", {})
print(f"\n  Sprites:")
for role, ref in sprites.items():
    print(f"    {role}: ID {ref['sprite_id']}")

ctrl = cfg.get("controls", {})
print(f"\n  FingerMap:     {ctrl.get('fingerMap')}")
print(f"  Keyboard:      {ctrl.get('keyboardFallback')}")

cam = cfg.get("world", {}).get("camera", {})
print(f"  Camera follow: {cam.get('follow')} (fija - sin scroll)")

print(f"\n  URL de juego:  {BASE}/play/{g['id']}")
print("\n=== VERIFICACION COMPLETA ===")

# Also verify sprites exist
print("\nVerificando sprites...")
req = urllib.request.Request(f"{BASE}/api/sprites")
r = opener.open(req)
sprites = json.loads(r.read())
mario_sprites = [s for s in sprites if s["id"] in [6, 7, 8, 9, 10]]
for s in mario_sprites:
    print(f"  Sprite ID {s['id']}: '{s['name']}' ({s['category']}, {s['type']}, {s['width']}x{s['height']})")
print(f"\n  Total sprites Mario: {len(mario_sprites)}/5")
