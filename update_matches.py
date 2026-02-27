"""
update_matches.py
1. Cap nhat status tran dau tu FotMob (FT/LIVE/SCHEDULED)
2. Cap nhat aggregate score cho UCL playoff tu playoff.rounds
"""
import sys, os, logging
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

import requests, urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.fotmob.com/",
}

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logging.warning(f"fetch error: {e}")
    return None

from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    from app.models import Match

    # ── 1. Cap nhat PL + UCL matches tu leagues API ──────────────────
    for LEAGUE, lid in [("PL", 47), ("UCL", 42)]:
        data = fetch(f"https://www.fotmob.com/api/leagues?id={lid}")
        if not data:
            logging.error(f"No data for {LEAGUE}")
            continue

        all_m = data.get("fixtures",{}).get("allMatches",[])
        logging.info(f"{LEAGUE}: {len(all_m)} matches from API")

        updated = 0
        for m in all_m:
            sid = str(m.get("id",""))
            if not sid: continue

            st = m.get("status",{})
            finished = st.get("finished", False)
            started  = st.get("started", False)
            reason_short = (st.get("reason",{}).get("short","") or "").upper()

            if finished:
                status = "FT"
            elif started:
                status = "HT" if reason_short == "HT" else "LIVE"
            else:
                status = "SCHEDULED"

            score_str = st.get("scoreStr","")
            hs = as_ = None
            if score_str:
                norm = score_str.replace(" ","").replace("-",":")
                if ":" in norm:
                    parts = norm.split(":")
                    try: hs, as_ = int(parts[0]), int(parts[1])
                    except: pass

            match = Match.query.filter_by(source_id=sid).first()
            if match:
                match.status = status
                if hs is not None:
                    match.home_score = hs
                    match.away_score = as_
                updated += 1

        db.session.commit()
        logging.info(f"{LEAGUE}: updated {updated} matches")

    # ── 2. Cap nhat UCL playoff aggregate + leg tu playoff.rounds ────
    data = fetch("https://www.fotmob.com/api/leagues?id=42")
    if data:
        playoff = data.get("playoff", {})
        agg_updated = 0
        for rnd in playoff.get("rounds", []):
            for mu in rnd.get("matchups", []):
                agg = mu.get("aggregatedResult") or {}
                agg_h = agg.get("homeScore")
                agg_a = agg.get("awayScore")
                matches_in_mu = mu.get("matches", [])

                for i, m in enumerate(matches_in_mu):
                    sid = str(m.get("matchId",""))
                    if not sid: continue
                    match = Match.query.filter_by(source_id=sid).first()
                    if not match: continue

                    match.leg = i + 1
                    match.is_knockout = True
                    if agg_h is not None:
                        match.agg_home = agg_h
                        match.agg_away = agg_a

                    # Update status va score tu playoff data (chinh xac hon)
                    st = m.get("status", {})
                    if st.get("finished"):
                        match.status = "FT"
                    elif st.get("started"):
                        match.status = "LIVE"
                    else:
                        match.status = "SCHEDULED"

                    score_str = st.get("scoreStr","")
                    if score_str:
                        norm = score_str.replace(" ","").replace("-",":")
                        if ":" in norm:
                            parts = norm.split(":")
                            try:
                                match.home_score = int(parts[0])
                                match.away_score = int(parts[1])
                            except: pass
                    agg_updated += 1

        db.session.commit()
        logging.info(f"UCL playoff: updated {agg_updated} match legs with aggregate")

    # ── Verify ────────────────────────────────────────────────────────
    for lg in ["PL","UCL"]:
        ft  = db.session.execute(db.text(f"SELECT COUNT(*) FROM matches WHERE league='{lg}' AND status='FT'")).scalar()
        liv = db.session.execute(db.text(f"SELECT COUNT(*) FROM matches WHERE league='{lg}' AND status='LIVE'")).scalar()
        sch = db.session.execute(db.text(f"SELECT COUNT(*) FROM matches WHERE league='{lg}' AND status='SCHEDULED'")).scalar()
        logging.info(f"{lg}: FT={ft}, LIVE={liv}, SCHEDULED={sch}")

    # Show UCL playoff aggregate
    rows = db.session.execute(db.text("""
        SELECT home_team_name, away_team_name, home_score, away_score,
               agg_home, agg_away, leg, status
        FROM matches WHERE league='UCL' AND matchweek=9 AND leg IS NOT NULL
        ORDER BY leg
        LIMIT 6
    """)).fetchall()
    logging.info("UCL Playoff sample:")
    for r in rows:
        print(f"  Leg{r.leg}: {r.home_team_name} {r.home_score}-{r.away_score} {r.away_team_name} | Agg: {r.agg_home}-{r.agg_away} | {r.status}")