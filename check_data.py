import sys, os, json
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
import requests, urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.fotmob.com/",
}

from app import create_app
app = create_app()
with app.app_context():
    from app.models import Player
    for name in ["Kalimuendo", "Masuaku"]:
        p = Player.query.filter(Player.name.ilike(f"%{name}%"), Player.league=="PL").first()
        if p:
            print(f"{p.name}: source_id={p.source_id} club_id={p.club_id} nationality={p.nationality!r}")
            # Fetch player detail tu FotMob
            r = requests.get(f"https://www.fotmob.com/api/playerData?id={p.source_id}",
                           headers=HEADERS, verify=False, timeout=10)
            if r.status_code == 200:
                d = r.json()
                meta = d.get("meta", {})
                print(f"  FotMob ccode={meta.get("ccode")!r} countryCode={meta.get("countryCode")!r}")
                # In ra cac field co the chua nationality
                for k in ["ccode","countryCode","country","nationality"]:
                    if k in d: print(f"  {k}={d[k]!r}")
                    if k in meta: print(f"  meta.{k}={meta[k]!r}")
            else:
                print(f"  FotMob status: {r.status_code}")