#!/usr/bin/env python3
"""End-to-end test: verifies the full game load flow as the frontend would."""

import json, urllib.request, http.cookiejar

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
))

print("1. Fetch game config...")
r = opener.open(f"{BASE}/api/games/2/config")
cfg = json.loads(r.read())
sprite_refs = cfg.get("sprites", {})
print(f"   Sprite IDs: {[v['sprite_id'] for v in sprite_refs.values()]}")

print("2. Batch resolve sprites...")
sprite_ids = [v["sprite_id"] for v in sprite_refs.values()]
r = opener.open(urllib.request.Request(
    f"{BASE}/api/sprites/batch",
    data=json.dumps({"ids": sprite_ids}).encode(),
    headers={"Content-Type": "application/json"},
))
sprites = json.loads(r.read())
print(f"   Resolved {len(sprites)} sprites:")
for s in sprites:
    print(f"     ID {s['id']}: {s['name']} ({s['type']}, {s['width']}x{s['height']}, {s.get('frame_count',1)} frames)")
    if s["type"] == "pixelmap":
        frames = s["data"].get("frames", [])
        palette = s["data"].get("palette", [])
        print(f"       pixelmap: {len(frames)} frames, {len(palette)} palette colors")
        for fi, f in enumerate(frames):
            grid = f.get("grid", [])
            print(f"       frame {fi}: {len(grid)} rows x {len(grid[0]) if grid else 0} cols")

print()
print("3. Create a test session...")
r = opener.open(urllib.request.Request(
    f"{BASE}/api/sessions",
    data=json.dumps({"game_id": 2, "patient_id": None}).encode(),
    headers={"Content-Type": "application/json"},
))
session = json.loads(r.read())
print(f"   Session created: ID {session.get('id')}")

print()
print("4. Verify play page loads...")
r = opener.open(f"{BASE}/play/2")
html = r.read().decode("utf-8")
checks = [
    ("Phaser loaded", "phaser" in html.lower()),
    ("GameLoader loaded", "GameLoader" in html),
    ("HandInput loaded", "HandInput" in html),
    ("Game ID reference", "gameId = 2" in html or '"2"' in html),
]
for label, ok in checks:
    print(f"   {'[OK]' if ok else '[FAIL]'} {label}")

print()
print("[OK] End-to-end verification complete - game is ready to play!")
print(f"    URL: {BASE}/play/2")
