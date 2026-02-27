"""app/routes/players.py"""
from flask import Blueprint, request, jsonify
from app.models import Player, Club
from app.extensions import cache

players_bp = Blueprint("players", __name__)

@players_bp.route("/", methods=["GET"])
def get_players():
    league   = request.args.get("league", "PL").upper()
    season   = request.args.get("season", "2025")
    position = request.args.get("position", "").upper()
    club_sid = request.args.get("club_source_id", "")
    club_id  = request.args.get("club_id", type=int)
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(int(request.args.get("per_page", 48)), 200)

    q = Player.query.filter_by(league=league, season=season)
    if position:
        q = q.filter_by(position=position)
    if club_id:
        q = q.filter_by(club_id=club_id)
    elif club_sid:
        club = Club.query.filter_by(source_id=club_sid, league=league).first()
        if club:
            q = q.filter_by(club_id=club.id)

    q = q.order_by(Player.name.asc())
    p = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [pl.to_dict() for pl in p.items],
        "total": p.total, "page": p.page, "pages": p.pages
    })

@players_bp.route("/<int:player_id>", methods=["GET"])
def get_player(player_id):
    pl = Player.query.get_or_404(player_id)
    data = pl.to_dict(include_stats=True)
    # Flatten stats vao root
    stats = pl.statistics.filter_by(league=pl.league, season=pl.season).first()
    if stats:
        data.update(stats.to_dict())
    return jsonify(data)

@players_bp.route("/search", methods=["GET"])
def search_players():
    q_str  = request.args.get("q", "").strip()
    league = request.args.get("league", "PL").upper()
    if not q_str:
        return jsonify({"items": [], "total": 0})
    players = (Player.query
               .filter_by(league=league)
               .filter(Player.name.ilike(f"%{q_str}%"))
               .limit(10).all())
    return jsonify({"items": [p.to_dict() for p in players], "total": len(players)})