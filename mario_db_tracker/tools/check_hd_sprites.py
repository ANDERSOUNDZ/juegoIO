"""Verify HD sprites."""
import json, urllib.request, http.cookiejar

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
))

for sid in [11, 12, 13, 14, 15]:
    r = opener.open(f"{BASE}/api/sprites/{sid}")
    s = json.loads(r.read())
    url = s.get("image_url", "")
    print(f"ID {sid}: {s['name']} ({s['type']}, {s['width']}x{s['height']}, {s['frame_count']} frames)")
    print(f"  URL length: {len(url)} chars -> {'OK' if url else 'EMPTY!'}")

print()
print("Game 2 sprites:")
r = opener.open(f"{BASE}/api/games/2/config")
cfg = json.loads(r.read())
for role, ref in cfg.get("sprites", {}).items():
    print(f"  {role}: sprite_id={ref['sprite_id']}")
