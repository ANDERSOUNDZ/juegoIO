"""Fix all Mario sprite rows to be exactly 20 chars wide."""
import json, urllib.request, http.cookiejar

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
))

# Fetch current sprite data
r = opener.open(f"{BASE}/api/sprites/6")
s = json.loads(r.read())
data = s["data"]
W = s["width"]  # 20

# Fix each frame: pad rows to W chars
for fi, frame in enumerate(data["frames"]):
    for ri, row in enumerate(frame["grid"]):
        if len(row) < W:
            # Pad with dots on right
            frame["grid"][ri] = row + "." * (W - len(row))
        elif len(row) > W:
            frame["grid"][ri] = row[:W]

# Also fix coin sprite
r2 = opener.open(f"{BASE}/api/sprites/8")
s2 = json.loads(r2.read())
data2 = s2["data"]
W2 = s2["width"]  # 12
for fi, frame in enumerate(data2["frames"]):
    for ri, row in enumerate(frame["grid"]):
        if len(row) < W2:
            frame["grid"][ri] = row + "." * (W2 - len(row))
        elif len(row) > W2:
            frame["grid"][ri] = row[:W2]

# Update Mario sprite
upd = {"data": data}
r = opener.open(urllib.request.Request(
    f"{BASE}/api/sprites/6",
    data=json.dumps(upd).encode(),
    headers={"Content-Type": "application/json"},
    method="PUT",
))
print(f"Mario sprite updated: {r.status}")

# Update coin sprite
upd2 = {"data": data2}
r = opener.open(urllib.request.Request(
    f"{BASE}/api/sprites/8",
    data=json.dumps(upd2).encode(),
    headers={"Content-Type": "application/json"},
    method="PUT",
))
print(f"Coin sprite updated: {r.status}")

# Verify
r = opener.open(f"{BASE}/api/sprites/6")
s = json.loads(r.read())
issues = []
for fi, frame in enumerate(s["data"]["frames"]):
    for ri, row in enumerate(frame["grid"]):
        if len(row) != 20:
            issues.append(f"F{fi}R{ri}: len={len(row)}")
print(f"Mario issues after fix: {len(issues)}")
if issues:
    for i in issues[:5]:
        print(f"  {i}")

r = opener.open(f"{BASE}/api/sprites/8")
s = json.loads(r.read())
issues2 = []
for fi, frame in enumerate(s["data"]["frames"]):
    for ri, row in enumerate(frame["grid"]):
        if len(row) != 12:
            issues2.append(f"F{fi}R{ri}: len={len(row)}")
print(f"Coin issues after fix: {len(issues2)}")
