import sys, os, json
sys.path.insert(0, ".")
import requests, urllib3
urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.fotmob.com/",
}

resp = requests.get("https://www.fotmob.com/api/leagues?id=47", headers=headers, verify=False, timeout=30)
data = resp.json()

# Kiem tra fixtures vs matches
print("=== FIXTURES keys ===")
fixtures = data.get("fixtures", {})
print(list(fixtures.keys()) if isinstance(fixtures, dict) else type(fixtures))
if isinstance(fixtures, dict):
    all_m = fixtures.get("allMatches", [])
    print(f"fixtures.allMatches count: {len(all_m)}")
    if all_m:
        print("First match:", json.dumps(all_m[0], indent=2))

print("\n=== MATCHES keys ===")
matches = data.get("matches", {})
print(list(matches.keys()) if isinstance(matches, dict) else type(matches))

# Kiem tra form trong table
print("\n=== FORM field in table row ===")
table = data.get("table", [])
if table:
    for section in table:
        sd = section.get("data", {})
        to = sd.get("table", {})
        rows = to.get("all", [])
        if rows:
            row = rows[0]
            print("form field:", json.dumps(row.get("form", "NOT FOUND"), indent=2))
            print("full row keys:", list(row.keys()))
            break