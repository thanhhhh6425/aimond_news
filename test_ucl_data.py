import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(".")))

import requests, urllib3
urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.fotmob.com/",
}

# UCL
resp = requests.get("https://www.fotmob.com/api/leagues?id=42", headers=headers, verify=False, timeout=30)
data = resp.json()

print("=== UCL TOP KEYS ===", list(data.keys()))

# Table
table = data.get("table", [])
print("=== UCL TABLE sections count ===", len(table))
if table:
    for i, section in enumerate(table):
        sd = section.get("data", {})
        to = sd.get("table", {})
        print(f"  section[{i}] keys:", list(to.keys()))
        for k in ["all", "home", "away"]:
            rows = to.get(k, [])
            if rows:
                print(f"    [{k}] first row:", json.dumps(rows[0], indent=2))
                break

# Fixtures / matches
fixtures = data.get("fixtures", {})
print("\n=== FIXTURES keys ===", list(fixtures.keys()) if isinstance(fixtures, dict) else type(fixtures))
if isinstance(fixtures, dict):
    all_matches = fixtures.get("allMatches", [])
    if all_matches:
        print("  First match:", json.dumps(all_matches[0], indent=2))

# Form va qualColor example
matches = data.get("matches", {})
print("\n=== MATCHES keys ===", list(matches.keys()) if isinstance(matches, dict) else type(matches))