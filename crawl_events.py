"""
crawl_events.py - Lay events (goals, cards) tu ESPN va luu vao matches DB
"""
import sys, os, json, time, logging
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

import requests, urllib3
urllib3.disable_warnings()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}

ESPN_LEAGUES = {
    "PL":  "eng.1",
    "UCL": "uefa.champions",
}

def norm_name(name):
    """Chuan hoa ten doi de matching chinh xac hon"""
    # Map ESPN name -> keyword de tim trong DB
    NAME_MAP = {
        "Manchester City":      "Manchester City",
        "Manchester United":    "Manchester United",
        "Tottenham Hotspur":    "Tottenham",
        "Newcastle United":     "Newcastle",
        "Nottingham Forest":    "Nottingham",
        "Brighton & Hove Albion": "Brighton",
        "Wolverhampton Wanderers": "Wolverhampton",
        "West Ham United":      "West Ham",
        "Aston Villa":          "Aston Villa",
        "AFC Bournemouth":      "Bournemouth",
        "Bayer Leverkusen":     "Leverkusen",
        "Borussia Dortmund":    "Dortmund",
        "Atletico Madrid":      "Atletico",
        "Inter Milan":          "Inter",
        "Paris Saint-Germain":  "Paris",
    }
    if name in NAME_MAP:
        return NAME_MAP[name]
    # Default: lay 2 tu dau de tranh match sai
    parts = name.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else parts[0]

def fetch_espn_events(league_slug, date_from="20250801", date_to="20260301"):
    """Lay tat ca completed matches co events tu ESPN - fetch theo tung thang"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_slug}/scoreboard"
    all_events = []

    # Chia nho thanh tung thang de tranh timeout
    from datetime import datetime, timedelta
    d_start = datetime.strptime(date_from, "%Y%m%d")
    d_end   = datetime.strptime(date_to,   "%Y%m%d")

    cur = d_start
    while cur < d_end:
        nxt = min(cur + timedelta(days=30), d_end)
        params = {"limit": 100, "dates": f"{cur.strftime("%Y%m%d")}-{nxt.strftime("%Y%m%d")}"}
        try:
            r = requests.get(url, params=params, headers=HEADERS, verify=False, timeout=30)
            if r.status_code == 200:
                evs = r.json().get("events", [])
                all_events.extend(evs)
                logging.info(f"  {params["dates"]}: {len(evs)} events")
            else:
                logging.warning(f"ESPN {league_slug} {params["dates"]}: {r.status_code}")
        except Exception as e:
            logging.error(f"ESPN fetch error {params["dates"]}: {e}")
        time.sleep(1)
        cur = nxt + timedelta(days=1)

    return all_events

def parse_events(espn_event):
    """Parse ESPN event -> list of normalized events"""
    comp = espn_event.get("competitions", [{}])[0]
    details = comp.get("details", [])
    if not details:
        return None, None, None

    # Build team id -> home/away
    team_side = {}
    for c in comp.get("competitors", []):
        tid = c.get("team", {}).get("id")
        side = c.get("homeAway", "home")
        name = c.get("team", {}).get("displayName", "")
        if tid:
            team_side[tid] = {"side": side, "name": name}

    events = []
    for d in details:
        athlete = (d.get("athletesInvolved") or [{}])[0]
        player_name = athlete.get("displayName", "")
        minute = d.get("clock", {}).get("displayValue", "")
        team_id = d.get("team", {}).get("id", "")
        side = team_side.get(team_id, {}).get("side", "home")

        if d.get("yellowCard"):
            etype = "yellow_card"
        elif d.get("redCard"):
            etype = "red_card"
        elif d.get("scoringPlay"):
            if d.get("ownGoal"):
                etype = "own_goal"
            elif d.get("penaltyKick"):
                etype = "penalty_goal"
            else:
                etype = "goal"
        elif d.get("penaltyKick") and not d.get("scoringPlay"):
            etype = "penalty_miss"
        else:
            continue  # Bo qua substitution etc

        events.append({
            "type":   etype,
            "minute": minute,
            "player": player_name,
            "side":   side,  # "home" or "away"
        })

    # ESPN match name: "Team A at Team B" hoac "Team A vs Team B"
    name = espn_event.get("name", "")
    espn_id = str(espn_event.get("id", ""))
    return espn_id, name, events

# ── MAIN ─────────────────────────────────────────────────────────────────────
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    from app.models import Match

    total_updated = 0

    for LEAGUE, slug in ESPN_LEAGUES.items():
        logging.info(f"\n=== {LEAGUE} ({slug}) ===")
        espn_events = fetch_espn_events(slug)
        logging.info(f"ESPN events: {len(espn_events)}")

        matched = 0
        for ev in espn_events:
            espn_id, name, events = parse_events(ev)
            if not events:
                continue

            comp = ev.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            home_name, away_name = "", ""
            for c in competitors:
                if c.get("homeAway") == "home":
                    home_name = c.get("team", {}).get("displayName", "")
                else:
                    away_name = c.get("team", {}).get("displayName", "")

            # Tim match trong DB theo ten doi + league
            db_match = Match.query.filter(
                Match.league == LEAGUE,
                Match.status == "FT",
                Match.home_team_name.ilike(f"%{norm_name(home_name)}%"),
                Match.away_team_name.ilike(f"%{norm_name(away_name)}%"),
            ).first()

            if not db_match:
                # Thu tim nguoc home/away doi cho
                db_match = Match.query.filter(
                    Match.league == LEAGUE,
                    Match.status == "FT",
                    Match.home_team_name.ilike(f"%{norm_name(home_name)}%"),
                    Match.away_team_name.ilike(f"%{norm_name(away_name)}%"),
                ).first()

            if db_match:
                db_match.events_json = json.dumps(events, ensure_ascii=False)
                matched += 1

        db.session.commit()
        logging.info(f"{LEAGUE}: matched & updated {matched} matches with events")
        total_updated += matched

    logging.info(f"\nTotal updated: {total_updated}")

    # Verify
    from sqlalchemy import text
    n = db.session.execute(text(
        "SELECT COUNT(*) FROM matches WHERE events_json IS NOT NULL AND events_json != '[]'"
    )).scalar()
    logging.info(f"Matches with events in DB: {n}")

    # Sample
    m = Match.query.filter(
        Match.events_json != None,
        Match.events_json != "[]"
    ).first()
    if m:
        evs = json.loads(m.events_json)
        print(f"\nSample: {m.home_team_name} vs {m.away_team_name}")
        for e in evs:
            print(f"  {e}")