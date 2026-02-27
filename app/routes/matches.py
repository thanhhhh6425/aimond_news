"""
app/routes/matches.py - API trận đấu
"""
from flask import Blueprint, request, jsonify
from app.models import Match
from app.extensions import cache

matches_bp = Blueprint("matches", __name__)

@matches_bp.route("/", methods=["GET"])
def get_matches():
    league    = request.args.get("league", "PL").upper()
    season    = request.args.get("season", "2025")
    status    = request.args.get("status", "").upper()
    matchweek = request.args.get("matchweek", type=int)
    page      = max(1, int(request.args.get("page", 1)))
    per_page  = min(int(request.args.get("per_page", 20)), 100)

    q = Match.query.filter_by(league=league, season=season)
    if status:    q = q.filter(Match.status == status)
    if matchweek: q = q.filter(Match.matchweek == matchweek)
    q = q.order_by(Match.kickoff_at.asc())
    p = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [m.to_dict() for m in p.items],
        "total": p.total, "page": p.page, "pages": p.pages
    })

@matches_bp.route("/live", methods=["GET"])
@cache.cached(timeout=15, query_string=True)
def get_live():
    league = request.args.get("league", "").upper()
    q = Match.query.filter_by(status="LIVE")
    if league: q = q.filter_by(league=league)
    items = q.order_by(Match.kickoff_at.asc()).all()
    return jsonify({"items": [m.to_dict() for m in items], "count": len(items)})

@matches_bp.route("/<int:match_id>", methods=["GET"])
@cache.cached(timeout=30)
def get_match(match_id):
    m = Match.query.get_or_404(match_id)
    return jsonify(m.to_dict())

@matches_bp.route("/upcoming", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
def get_upcoming():
    from datetime import datetime, timezone
    league = request.args.get("league", "PL").upper()
    limit = min(int(request.args.get("limit", 5)), 20)
    items = (Match.query
             .filter_by(league=league, season="2025", status="SCHEDULED")
             .filter(Match.kickoff_at >= datetime.now(timezone.utc))
             .order_by(Match.kickoff_at.asc())
             .limit(limit).all())
    return jsonify({"items": [m.to_dict() for m in items]})

@matches_bp.route("/results", methods=["GET"])
@cache.cached(timeout=120, query_string=True)
def get_results():
    league = request.args.get("league", "PL").upper()
    limit = min(int(request.args.get("limit", 10)), 50)
    matchweek = request.args.get("matchweek", type=int)
    q = (Match.query.filter_by(league=league, season="2025", status="FT")
         .order_by(Match.kickoff_at.desc()))
    if matchweek: q = q.filter_by(matchweek=matchweek)
    items = q.limit(limit).all()
    return jsonify({"items": [m.to_dict() for m in items]})

@matches_bp.route("/rounds", methods=["GET"])
def get_rounds():
    """Tra ve danh sach vong dau unique de hien thi GW bar."""
    from app.extensions import db
    league = request.args.get("league", "PL").upper()
    season = request.args.get("season", "2025")

    rows = (db.session.query(Match.matchweek, Match.round)
            .filter(Match.league == league, Match.season == season)
            .filter(Match.matchweek != None)
            .distinct()
            .order_by(Match.matchweek.asc())
            .all())

    UCL_LABELS = {
        1:"Vòng 1",2:"Vòng 2",3:"Vòng 3",4:"Vòng 4",
        5:"Vòng 5",6:"Vòng 6",7:"Vòng 7",8:"Vòng 8",
        9:"Playoff",10:"Vòng 1/8",11:"Tứ kết",12:"Bán kết",13:"Chung kết"
    }

    rounds = []
    for mw, rnd in rows:
        if league == "UCL":
            label = UCL_LABELS.get(mw, rnd or f"Vòng {mw}")
        else:
            label = f"GW {mw}"
        rounds.append({"matchweek": mw, "label": label, "round": rnd})

    return jsonify({"rounds": rounds, "league": league})

@matches_bp.route("/bracket", methods=["GET"])
def get_bracket():
    """UCL knockout bracket tu FotMob playoff API."""
    import requests, urllib3
    urllib3.disable_warnings()
    league = request.args.get("league", "UCL").upper()
    if league != "UCL":
        return jsonify({"error": "Only UCL bracket available"}), 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.fotmob.com/",
    }
    try:
        r = requests.get("https://www.fotmob.com/api/leagues?id=42",
                         headers=headers, verify=False, timeout=15)
        data = r.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    playoff = data.get("playoff", {})
    rounds_raw = playoff.get("rounds", [])

    STAGE_LABELS = {
        "playoff": "Playoff",
        "1/8": "Vòng 1/8",
        "1/4": "Tứ kết",
        "1/2": "Bán kết",
        "final": "Chung kết",
    }

    def badge(team_id):
        if not team_id: return ""
        return f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}_small.png"

    rounds = []
    for rnd in rounds_raw:
        stage = rnd.get("stage", "")
        matchups_raw = rnd.get("matchups", [])
        matchups = []
        for mu in matchups_raw:
            h_id = mu.get("homeTeamId")
            a_id = mu.get("awayTeamId")
            agg  = mu.get("aggregatedResult") or {}
            winner = mu.get("aggregatedWinner")
            loser  = mu.get("aggregatedLoser")

            # Parse 2 matches (leg1, leg2)
            matches = []
            for i, m in enumerate(mu.get("matches", [])):
                mh = m.get("home", {})
                ma = m.get("away", {})
                st = m.get("status", {})
                finished = st.get("finished", False)
                started  = st.get("started", False)
                score_str = st.get("scoreStr", "")
                hs, as_ = None, None
                if score_str:
                    norm = score_str.replace(" ","").replace("-",":")
                    if ":" in norm:
                        parts = norm.split(":")
                        try: hs, as_ = int(parts[0]), int(parts[1])
                        except: pass
                matches.append({
                    "match_id":   m.get("matchId"),
                    "leg":        i + 1,
                    "kickoff":    st.get("utcTime"),
                    "status":     "FT" if finished else ("LIVE" if started else "SCHEDULED"),
                    "home_name":  mh.get("name",""),
                    "home_short": mh.get("shortName",""),
                    "home_id":    mh.get("id"),
                    "home_score": hs,
                    "away_name":  ma.get("name",""),
                    "away_short": ma.get("shortName",""),
                    "away_id":    ma.get("id"),
                    "away_score": as_,
                    "home_winner": mh.get("winner", False),
                    "away_winner": ma.get("winner", False),
                })

            # TBD teams (vong sau chua biet)
            tbd1 = mu.get("tbdTeam1", False)
            tbd2 = mu.get("tbdTeam2", False)
            home_name = mu.get("homeTeam") or (mu.get("homeTeamPlaceholder") if tbd1 else None)
            away_name = mu.get("awayTeam") or (mu.get("awayTeamPlaceholder") if tbd2 else None)

            matchups.append({
                "draw_order":  mu.get("drawOrder"),
                "home_id":     h_id,
                "home_name":   home_name or "",
                "home_short":  mu.get("homeTeamShortName",""),
                "home_badge":  badge(h_id),
                "away_id":     a_id,
                "away_name":   away_name or "",
                "away_short":  mu.get("awayTeamShortName",""),
                "away_badge":  badge(a_id),
                "agg_home":    agg.get("homeScore"),
                "agg_away":    agg.get("awayScore"),
                "winner_id":   (winner if isinstance(winner, int) else winner.get("id")) if winner else None,
                "winner_name": (None if isinstance(winner, int) else winner.get("name")) if winner else None,
                "loser_id":    (loser if isinstance(loser, int) else loser.get("id")) if loser else None,
                "tbd_home":    tbd1,
                "tbd_away":    tbd2,
                "best_of":     mu.get("bestOf", 2),
                "matches":     matches,
            })

        rounds.append({
            "stage": stage,
            "label": STAGE_LABELS.get(stage, stage),
            "matchups": matchups,
        })

    return jsonify({"rounds": rounds, "type": playoff.get("type","")})