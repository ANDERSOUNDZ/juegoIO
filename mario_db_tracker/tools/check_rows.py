"""Check Mario sprite row widths in DB."""
import json, urllib.request, http.cookiejar

BASE = "http://localhost:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(
    f"{BASE}/api/auth/login",
    data=json.dumps({"email": "admin@pixo.com", "password": "admin"}).encode(),
    headers={"Content-Type": "application/json"},
))

r = opener.open(f"{BASE}/api/sprites/6")
s = json.loads(r.read())
frames = s["data"]["frames"]
issues = 0
for fi, f in enumerate(frames):
    grid = f["grid"]
    for ri, row in enumerate(grid):
        if len(row) != 20:
            print(f"ISSUE: Frame {fi}, Row {ri}: len={len(row)} -> \"{row}\"")
            issues += 1
    # Show first and last few rows
    print(f"Frame {fi}: {len(grid)} rows")
    print(f"  First 3: [{grid[0][:20]}] [{grid[1][:20]}] [{grid[2][:20]}]")
    print(f"  Last 3:  [{grid[-3][:20]}] [{grid[-2][:20]}] [{grid[-1][:20]}]")

if issues == 0:
    print("ALL ROWS CORRECT (20 chars each)")
else:
    print(f"FOUND {issues} ISSUES")
