#!/usr/bin/env python3
"""Check the full config JSON for validity."""
import json, urllib.request, http.cookiejar, sys

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
))

r = opener.open(f"{BASE}/api/games/2/config")
cfg = json.loads(r.read())
issues = []

def ok(msg): print(f"  [OK] {msg}")
def warn(msg): print(f"  [!] {msg}")
def fail(msg): issues.append(msg); print(f"  [FAIL] {msg}")

# Camera
cam = cfg.get("world", {}).get("camera", {})
follow = cam.get("follow")
if follow is None:
    ok("Camera fixed (no follow)")
else:
    warn(f"Camera follow = {follow}")

# Gravity
print(f"  gravity = {cfg.get('physics',{}).get('gravity')}")

# Player
p = cfg.get("entities",{}).get("player",{})
print(f"  player speed={p.get('speed')} jumpForce={p.get('jumpForce')} spawn={p.get('spawn')}")

# Platforms
plats = cfg.get("entities",{}).get("platforms",{})
print(f"  platform layout={plats.get('layout')} count={len(plats.get('positions',[]))}")
for i, pos in enumerate(plats.get("positions",[])):
    if not all(k in pos for k in ("x","y","w","h")):
        fail(f"Platform {i}: missing keys")

# Enemies
enemies = cfg.get("entities",{}).get("enemies",{})
print(f"  enemies ai={enemies.get('ai')} speed={enemies.get('speed')} count={len(enemies.get('positions',[]))}")

# Controls
fm = cfg.get("controls",{}).get("fingerMap",{})
for i in range(5):
    si = str(i)
    if si not in fm:
        fail(f"Finger {i} not mapped")
    else:
        print(f"  finger {i} -> {fm[si]}")

# Rules
rules = cfg.get("rules",{})
print(f"  win={rules.get('winCondition')} lose={rules.get('loseCondition')} lives={rules.get('lives')}")

# Sprites
sprites = cfg.get("sprites",{})
expected = {"player","platform","coin","enemy","background"}
missing_roles = expected - set(sprites.keys())
if missing_roles: fail(f"Missing sprites: {missing_roles}")
for role, ref in sprites.items():
    if "sprite_id" not in ref: fail(f"Sprite {role}: no sprite_id")
    else: print(f"  sprite {role}: ID {ref['sprite_id']}")

world = cfg.get("world",{})
print(f"  world {world.get('width')}x{world.get('height')} bg={world.get('backgroundColor')}")

if issues:
    print(f"\nFAILED: {len(issues)} issues found")
    sys.exit(1)
else:
    print("\n[OK] All checks passed - config valida!")
