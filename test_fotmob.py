import requests, urllib3, json
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
    "Origin": "https://www.fotmob.com",
}

urls = [
    "https://www.fotmob.com/api/leagues?id=42",
    "https://www.fotmob.com/api/leagues?id=42&ccode3=VNM",
    "https://www.fotmob.com/api/leagues?id=47",
    "https://www.fotmob.com/_next/data/en/leagues/42/overview.json",
    "https://www.fotmob.com/api/allLeagues",
]

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        print(f"{r.status_code} | {url}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Keys: {list(data.keys())[:5]}")
    except Exception as e:
        print(f"ERROR | {url} | {e}")