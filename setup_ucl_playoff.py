"""
setup_ucl_playoff.py - Chi restore UCL playoff (mw=9) tu FotMob
"""
import sys, os, logging
from datetime import datetime, timezone
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

import requests, urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.fotmob.com/",
}

def parse_utc(s):
    if not s: return None
    try:
        s = s.replace("Z","").split(".")[0]
        if "T" not in s: s = s.replace(" ","T")
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except: return None

from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    from app.models import Match

    r = requests.get("https://www.fotmob.com/api/leagues?id=42",
                     headers=HEADERS, verify=False, timeout=15)
    data = r.json()
    rounds = data.get("playoff",{}).get("rounds",[])

    inserted = 0
    for rd in rounds:
        if rd.get("stage") != "playoff": continue
        for mu in rd.get("matchups",[]):
            for leg_num, m in enumerate(mu.get("matches",[]), 1):
                sid = str(m.get("matchId",""))
                if not sid: continue

                status_obj = m.get("status",{})
                finished = status_obj.get("finished", False)
                started  = status_obj.get("started", False)
                kickoff  = parse_utc(status_obj.get("utcTime",""))

                status = "FT" if finished else ("LIVE" if started else "SCHEDULED")
                h, a = m.get("home",{}), m.get("away",{})

                db_m = Match.query.filter_by(source_id=sid).first()
                if not db_m:
                    db_m = Match(source_id=sid, league="UCL", season="2025")
                    db.session.add(db_m)

                db_m.matchweek   = 9
                db_m.round       = "Playoff"
                db_m.is_knockout = True
                db_m.leg         = leg_num
                db_m.kickoff_at  = kickoff
                db_m.status      = status
                db_m.home_team_name  = h.get("name","")
                db_m.away_team_name  = a.get("name","")
                db_m.home_score  = h.get("score") if finished or started else None
                db_m.away_score  = a.get("score") if finished or started else None

                # Badge tu Club
                from app.models import Club
                for team_name, attr in [(h.get("name",""), "home"), (a.get("name",""), "away")]:
                    c = Club.query.filter(
                        Club.name.ilike(f"%{team_name.split()[0]}%"),
                        Club.league=="UCL"
                    ).first()
                    if c:
                        if attr == "home": db_m.home_team_badge = c.badge_url or ""
                        else: db_m.away_team_badge = c.badge_url or ""

                inserted += 1

    db.session.commit()
    logging.info(f"Restored {inserted} playoff matches")

    from sqlalchemy import text
    n = db.session.execute(text("SELECT COUNT(*) FROM matches WHERE league='UCL' AND matchweek=9")).scalar()
    logging.info(f"UCL mw=9 now: {n} matches")