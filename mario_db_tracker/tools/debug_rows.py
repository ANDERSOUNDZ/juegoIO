"""Check raw sprite data from DB."""
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

# Print first row of frame 0 WITH character codes
row = s["data"]["frames"][0]["grid"][0]
print(f"Row 0: repr = {repr(row)}")
print(f"Length: {len(row)}")
print(f"Chars: ", [ord(c) for c in row])

# Check if the issue is during PUT
print("\nFull frame 0 rows:")
for i, r in enumerate(s["data"]["frames"][0]["grid"]):
    print(f"  {i}: len={len(r)} val={repr(r)}")
