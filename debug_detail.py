import requests, urllib3, json
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://www.fotmob.com/",
}

r = requests.get("https://www.fotmob.com/api/data/teams?id=8456", headers=HEADERS, verify=False, timeout=10)
data = r.json()
squad = data.get("squad", {})
inner = squad.get("squad", [])

# Duyet tat ca group, tim cau thu co stats
for group in inner:
    title = group.get("title", "")
    members = group.get("members", [])
    print(f"\n--- {title}: {len(members)} members ---")
    for m in members[:2]:
        print(json.dumps(m, indent=2)[:600])
        print("---")