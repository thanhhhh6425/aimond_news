import requests, urllib3
urllib3.disable_warnings()

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

r = requests.get(
    "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard",
    params={"limit": 50, "dates": "20260407-20260415"},
    headers=HEADERS, verify=False, timeout=15
)
events = r.json().get("events", [])
print(f"Events: {len(events)}")
for e in events[:5]:
    season = e.get("season", {})
    print(f"  {e.get('name')} | slug={season.get('slug')} | week={e.get('week')}")