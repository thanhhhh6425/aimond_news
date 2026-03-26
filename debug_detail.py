import requests, urllib3, json
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.fotmob.com/",
}

r = requests.get("https://www.fotmob.com/api/data/leagues?id=42", headers=HEADERS, verify=False, timeout=10)
data = r.json()
print("Top keys:", list(data.keys()))
print("playoff:", data.get("playoff"))
print("tabs:", data.get("tabs", [])[:3])