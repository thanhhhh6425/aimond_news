"""
crawl_players.py - Crawl stats + squad, luu vao DB
Position mapping chinh xac tu FotMob position IDs thuc te
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

# Position IDs chinh xac tu FotMob (verified tu debug thuc te)
GK_IDS  = {11}
DEF_IDS = {32, 33, 34, 35, 36, 37, 38, 51, 59, 62}  # CB, LB, RB, WB
MID_IDS = {64, 65, 66, 67, 72, 73, 74, 75, 76, 77, 78, 79, 82}  # DM, CM, AM
# 68=LWB/LM, 71=RWB/RM -> tuy truong hop nhung thuong la DEF/wingback
WING_IDS = {68, 71}  # wingback - xet theo context
FWD_IDS = {83, 84, 85, 86, 87, 88, 103, 104, 105, 106, 107, 115}  # W, SS, CF, ST

def map_pos_from_desc(desc_str, section_title=""):
    """Map tu positionIdsDesc + section_title sang GK/DEF/MID/FWD.
    Dung section_title lam tie-breaker khi cau thu da nhieu vi tri.
    """
    if not desc_str: return None
    GK_SET  = {"GK"}
    DEF_SET = {"CB","LB","RB","SW"}
    WING_SET= {"LWB","RWB"}   # wingback - co the DEF hoac FWD tuy nguoi
    MID_SET = {"CM","CDM","CAM","LM","RM","AM","DM"}
    FWD_SET = {"ST","CF","LW","RW","SS","WF","SS"}

    positions = [p.strip().upper() for p in desc_str.split(",")]
    first = positions[0]

    # GK luon ro rang
    if first in GK_SET: return "GK"

    # Dem so luong theo nhom
    counts = {"GK":0,"DEF":0,"MID":0,"FWD":0}
    for p in positions:
        if p in GK_SET:   counts["GK"]  += 1
        elif p in DEF_SET: counts["DEF"] += 1
        elif p in WING_SET:
            # Wingback: dung section_title quyet dinh
            sec = section_title.lower()
            if "attack" in sec or "forward" in sec: counts["FWD"] += 1
            elif "defend" in sec:                   counts["DEF"] += 1
            else:                                   counts["DEF"] += 1  # mac dinh DEF
        elif p in MID_SET: counts["MID"] += 1
        elif p in FWD_SET: counts["FWD"] += 1

    # Neu first la wingback, dung section + other positions de quyet dinh
    if first in WING_SET:
        sec = section_title.lower()
        # Neu section la attackers/midfielders VA co FWD position khac -> FWD
        has_fwd = any(p in FWD_SET for p in positions[1:])
        has_mid = any(p in MID_SET for p in positions[1:])
        if "attack" in sec or "forward" in sec: return "FWD"
        if ("mid" in sec) and has_fwd: return "FWD"
        # Neu majority la DEF/WING (>= 60%) -> DEF du co MID
        n_def = sum(1 for p in positions if p in DEF_SET or p in WING_SET)
        if n_def / len(positions) >= 0.5: return "DEF"
        if ("mid" in sec) and has_mid: return "MID"
        return "DEF"

    # Neu first ro rang
    if first in DEF_SET: return "DEF"
    if first in MID_SET: return "MID"
    if first in FWD_SET: return "FWD"

    # Fallback: nhom nhieu nhat (bo qua GK)
    best = max(["DEF","MID","FWD"], key=lambda k: counts[k])
    return best

def map_pos(pos_ids):
    if not pos_ids: return "FWD"
    p = pos_ids[0]
    if p in GK_IDS:   return "GK"
    if p in DEF_IDS:  return "DEF"
    if p in MID_IDS:  return "MID"
    if p in WING_IDS: return "MID"
    if p in FWD_IDS:  return "FWD"
    if p == 11:       return "GK"
    if p <= 62:       return "DEF"
    if p <= 82:       return "MID"
    return "FWD"

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logging.warning(f"fetch error {url}: {e}")
    return None

def badge(tid): return f"https://images.fotmob.com/image_resources/logo/teamlogo/{tid}_small.png"
def photo(pid): return f"https://images.fotmob.com/image_resources/playerimages/{pid}.png"

def crawl_stats(league_id, season_id):
    STAT_URLS = [
        ("goals",        f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/goals.json"),
        ("assists",      f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/goal_assist.json"),
        ("yellow_cards", f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/yellow_card.json"),
        ("red_cards",    f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/red_card.json"),
        ("saves",        f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/saves.json"),
        ("clean_sheets", f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/clean_sheet.json"),
        ("rating",       f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/rating.json"),
        ("xg",           f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/expected_goals.json"),
        ("mins",         f"https://data.fotmob.com/stats/{league_id}/season/{season_id}/mins_played.json"),
    ]

    players = {}

    for stat_key, url in STAT_URLS:
        data = fetch(url)
        if not data:
            logging.warning(f"  {stat_key}: no data")
            continue
        count = 0
        for tl in data.get("TopLists", []):
            for e in tl.get("StatList", []):
                pid = str(e.get("ParticiantId") or e.get("ParticipantId") or "")
                if not pid: continue

                if pid not in players:
                    pos_ids = e.get("Positions", [])
                    players[pid] = {
                        "pid": pid,
                        "name": e.get("ParticipantName",""),
                        "team_id": str(e.get("TeamId","")),
                        "team_name": e.get("TeamName",""),
                        "position": map_pos(pos_ids),
                        "_pos_ids": pos_ids,
                        "goals": 0, "assists": 0, "saves": None, "clean_sheets": None,
                        "yellow_cards": 0, "red_cards": 0, "xg": None, "rating": None,
                        "appearances": 0, "minutes": 0,
                    }
                else:
                    # Update position neu chua set hoac chua chinh xac
                    pos_ids = e.get("Positions", [])
                    if pos_ids and not players[pid].get("_pos_ids"):
                        players[pid]["_pos_ids"] = pos_ids
                        players[pid]["position"] = map_pos(pos_ids)

                val = float(e.get("StatValue") or 0)
                mp  = int(e.get("MatchesPlayed") or 0)
                min_= int(e.get("MinutesPlayed") or 0)

                if stat_key == "goals":
                    players[pid]["goals"]       = int(val)
                    players[pid]["appearances"]  = mp
                    players[pid]["minutes"]      = min_
                elif stat_key == "assists":
                    players[pid]["assists"]      = int(val)
                elif stat_key == "yellow_cards":
                    players[pid]["yellow_cards"] = int(val)
                elif stat_key == "red_cards":
                    players[pid]["red_cards"]    = int(val)
                elif stat_key == "saves":
                    players[pid]["saves"]        = int(val)
                    players[pid]["position"]     = "GK"
                elif stat_key == "clean_sheets":
                    players[pid]["clean_sheets"] = int(val)
                    players[pid]["position"]     = "GK"
                elif stat_key == "rating":
                    players[pid]["rating"]       = float(val)
                    if not players[pid]["appearances"]: players[pid]["appearances"] = mp
                    if not players[pid]["minutes"]:     players[pid]["minutes"]     = min_
                elif stat_key == "xg":
                    players[pid]["xg"]           = float(val)
                elif stat_key == "mins":
                    if not players[pid]["appearances"]: players[pid]["appearances"] = mp
                    if not players[pid]["minutes"]:     players[pid]["minutes"]     = min_
                count += 1
        logging.info(f"  {stat_key}: {count} entries")

    return players

def crawl_squad(league_id):
    """Lay squad info: shirt, dob, height, nationality. Return dict pid -> info"""
    data = fetch(f"https://www.fotmob.com/api/leagues?id={league_id}")
    if not data: return {}

    # Lay club IDs tu FIXTURES (chac chan co du tat ca clubs ke ca UCL)
    club_ids = set()
    for m in data.get("fixtures",{}).get("allMatches",[]):
        for key in ["home","away"]:
            cid = m.get(key,{}).get("id")
            if cid: club_ids.add(str(cid))
    # Fallback: table
    if not club_ids:
        for section in data.get("table", []):
            for row in section.get("data",{}).get("table",{}).get("all",[]):
                cid = row.get("id")
                if cid: club_ids.add(str(cid))

    squad_info = {}
    logging.info(f"  Fetching squad for {len(club_ids)} clubs...")

    for cid in sorted(club_ids):
        team = fetch(f"https://www.fotmob.com/api/teams?id={cid}")
        if not team: continue
        squad_data = (team.get("squad") or {}).get("squad") or []
        for section in squad_data:
            title = (section.get("title","") or "").lower()
            if "coach" in title: continue
            for m in (section.get("members") or []):
                pid = str(m.get("id",""))
                if not pid: continue
                # Skip coach by role
                role_key = (m.get("role") or {}).get("key","")
                if "coach" in role_key.lower(): continue
                dob = m.get("dateOfBirth","")
                if isinstance(dob, dict):
                    dob = dob.get("utcTime","")[:10]
                else:
                    dob = str(dob or "")[:10]
                squad_info[pid] = {
                    "shirt_number": m.get("shirtNumber") or m.get("shirt"),
                    "date_of_birth": dob,
                    "height_cm": m.get("height"),
                    "nationality": m.get("ccode") or m.get("countryCode",""),
                    "position_desc": m.get("positionIdsDesc",""),
                    "section_title": title,
                }
    logging.info(f"  Squad info: {len(squad_info)} players")
    return squad_info

# ─── MAIN ───────────────────────────────────────────────────────────────────
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    from app.models import Player, Club, Statistic
    from datetime import date

    for LEAGUE, league_id, season_id in [("PL", 47, 27110), ("UCL", 42, 28184)]:
        logging.info(f"\n=== {LEAGUE} ===")

        # Xoa cu
        db.session.execute(db.text(f"DELETE FROM statistics WHERE league='{LEAGUE}'"))
        db.session.execute(db.text(f"DELETE FROM players WHERE league='{LEAGUE}'"))
        db.session.commit()

        stats  = crawl_stats(league_id, season_id)
        squad  = crawl_squad(league_id)
        clubs  = {c.source_id: c for c in Club.query.filter_by(league=LEAGUE).all()}
        logging.info(f"  Stats: {len(stats)}, Squad: {len(squad)}, Clubs: {len(clubs)}")

        # Supplement: them GK tu squad section "keepers" neu chua co trong stats
        data_lg = fetch(f"https://www.fotmob.com/api/leagues?id={league_id}")
        club_ids_for_gk = set()
        if data_lg:
            for m in data_lg.get("fixtures",{}).get("allMatches",[]):
                for key in ["home","away"]:
                    cid = m.get(key,{}).get("id")
                    if cid: club_ids_for_gk.add(str(cid))
        for cid in sorted(club_ids_for_gk):
            team = fetch(f"https://www.fotmob.com/api/teams?id={cid}")
            if not team: continue
            club = clubs.get(cid)
            for section in ((team.get("squad") or {}).get("squad") or []):
                title = (section.get("title","") or "").lower()
                if "keeper" not in title: continue
                for m in (section.get("members") or []):
                    pid = str(m.get("id",""))
                    if not pid or pid in stats: continue
                    # Them GK moi chua co trong stats
                    team_id = cid
                    team_name = (team.get("details") or {}).get("name","")
                    stats[pid] = {
                        "pid": pid,
                        "name": m.get("name",""),
                        "team_id": team_id,
                        "team_name": team_name,
                        "position": "GK",
                        "goals":0,"assists":0,"saves":None,"clean_sheets":None,
                        "yellow_cards":0,"red_cards":0,"xg":None,"rating":None,
                        "appearances":0,"minutes":0,
                    }
                    if pid not in squad:
                        dob = m.get("dateOfBirth","")
                        if isinstance(dob, dict): dob = dob.get("utcTime","")[:10]
                        squad[pid] = {
                            "shirt_number": m.get("shirtNumber"),
                            "date_of_birth": str(dob or "")[:10],
                            "height_cm": m.get("height"),
                            "nationality": m.get("ccode",""),
                        }
        logging.info(f"  After GK supplement: {len(stats)} total")

        count = 0
        for pid, s in stats.items():
            try:
                club = clubs.get(s["team_id"])
                sq   = squad.get(pid, {})

                player = Player(source_id=pid, league=LEAGUE, season="2025")
                db.session.add(player)
                player.name         = s["name"]
                player.club_id      = club.id if club else None
                # Uu tien position tu squad (chinh xac hon stats)
                sq_pos = map_pos_from_desc(sq.get("position_desc",""), sq.get("section_title",""))
                if sq_pos:
                    player.position = sq_pos
                elif s["position"]:
                    player.position = s["position"]
                else:
                    # Fallback theo section title
                    sec = sq.get("section_title","").lower()
                    player.position = "GK" if "keeper" in sec else "DEF" if "defend" in sec else "FWD" if "attack" in sec else "MID"
                player.photo_url    = photo(pid)
                player.nationality  = sq.get("nationality","")
                player.shirt_number = sq.get("shirt_number") or None
                player.height_cm    = sq.get("height_cm") or None
                dob = sq.get("date_of_birth","")
                if dob and len(dob) >= 10:
                    try: player.date_of_birth = date.fromisoformat(dob[:10])
                    except: pass
                db.session.flush()

                stat = Statistic(player_id=player.id, league=LEAGUE, season="2025",
                                 club_id=club.id if club else None)
                db.session.add(stat)
                stat.goals          = s["goals"]
                stat.assists        = s["assists"]
                stat.yellow_cards   = s["yellow_cards"]
                stat.red_cards      = s["red_cards"]
                stat.saves          = s["saves"]
                stat.clean_sheets   = s["clean_sheets"]
                stat.average_rating = s["rating"]
                stat.expected_goals = s["xg"]
                stat.appearances    = s["appearances"]
                stat.minutes_played = s["minutes"]
                count += 1

                if count % 100 == 0:
                    db.session.commit()
                    logging.info(f"  Committed {count}...")

            except Exception as e:
                logging.error(f"  Error pid={pid} {s.get('name')}: {e}")
                db.session.rollback()

        db.session.commit()
        logging.info(f"{LEAGUE} done: {count} players")

    # Verify
    logging.info("\n=== VERIFY ===")
    for lg in ["PL","UCL"]:
        for stat, cond in [("goals","goals>0"),("assists","assists>0"),
                           ("yellow","yellow_cards>0"),("saves","saves IS NOT NULL AND saves>0"),
                           ("rating","average_rating IS NOT NULL")]:
            n = db.session.execute(db.text(
                f"SELECT COUNT(*) FROM statistics WHERE league='{lg}' AND {cond}"
            )).scalar()
            logging.info(f"  {lg} {stat}: {n}")

        # Position breakdown
        for pos in ["GK","DEF","MID","FWD"]:
            n = db.session.execute(db.text(
                f"SELECT COUNT(*) FROM players WHERE league='{lg}' AND position='{pos}'"
            )).scalar()
            logging.info(f"  {lg} {pos}: {n}")