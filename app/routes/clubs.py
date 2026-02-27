"""
app/routes/clubs.py - API câu lạc bộ
"""
from flask import Blueprint, request, jsonify
from app.models import Club
from app.extensions import cache

clubs_bp = Blueprint("clubs", __name__)

@clubs_bp.route("/", methods=["GET"])
@cache.cached(timeout=600, query_string=True)
def get_clubs():
    league = request.args.get("league", "PL").upper()
    season = request.args.get("season", "2025")
    items = (Club.query.filter_by(league=league, season=season)
             .order_by(Club.name.asc()).all())
    return jsonify({"items": [c.to_dict() for c in items], "total": len(items)})

@clubs_bp.route("/<int:club_id>", methods=["GET"])
def get_club(club_id):
    c = Club.query.get_or_404(club_id)
    include_players = request.args.get("players", "false").lower() == "true"
    league = request.args.get("league", "").upper()
    data = c.to_dict(include_players=include_players)
    # Dam bao badge_url luon co gia tri tu source_id
    if not data.get("badge_url") and data.get("source_id"):
        data["badge_url"] = f"https://images.fotmob.com/image_resources/logo/teamlogo/{data['source_id']}_small.png"
    # Sort players theo vi tri + so ao
    if include_players and data.get("players"):
        pos_order = {"GK":0,"DEF":1,"MID":2,"FWD":3}
        data["players"] = sorted(
            data["players"],
            key=lambda p: (pos_order.get(p.get("position","FWD"),9), p.get("shirt_number") or 99)
        )
    return jsonify(data)

@clubs_bp.route("/search", methods=["GET"])
def search_clubs():
    q_str = request.args.get("q", "").strip()
    league = request.args.get("league", "").upper()
    if not q_str: return jsonify({"items": []})
    q = Club.query.filter(Club.name.ilike(f"%{q_str}%"))
    if league: q = q.filter_by(league=league)
    items = q.limit(10).all()
    return jsonify({"items": [c.to_dict() for c in items]})