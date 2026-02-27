"""app/routes/statistics.py"""
from flask import Blueprint, request, jsonify
from app.models import Statistic, TeamStatistic
from app.extensions import db

statistics_bp = Blueprint("statistics", __name__)

VALID_SORTS = {
    "goals", "assists", "appearances", "minutes_played",
    "clean_sheets", "saves", "yellow_cards", "red_cards",
    "expected_goals", "average_rating"
}

@statistics_bp.route("/players", methods=["GET"])
def get_player_stats():
    league   = request.args.get("league", "PL").upper()
    season   = request.args.get("season", "2025")
    sort_by  = request.args.get("sort", "goals")
    position = request.args.get("position", "").upper()
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(int(request.args.get("per_page", 50)), 200)

    if sort_by not in VALID_SORTS:
        sort_by = "goals"

    col = getattr(Statistic, sort_by, Statistic.goals)

    q = (db.session.query(Statistic)
         .filter(Statistic.league == league, Statistic.season == season)
         .filter(col > 0))

    if position:
        from app.models import Player
        q = q.join(Player, Statistic.player_id == Player.id).filter(Player.position == position)

    q = q.order_by(col.desc())
    p = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [s.to_dict() for s in p.items],
        "total": p.total, "page": p.page, "pages": p.pages,
        "sort_by": sort_by, "league": league
    })

@statistics_bp.route("/teams", methods=["GET"])
def get_team_stats():
    league  = request.args.get("league", "PL").upper()
    season  = request.args.get("season", "2025")
    sort_by = request.args.get("sort", "goals_scored")
    allowed = {"goals_scored","goals_conceded","clean_sheets","possession_avg","pass_accuracy"}
    if sort_by not in allowed:
        sort_by = "goals_scored"
    col   = getattr(TeamStatistic, sort_by, TeamStatistic.goals_scored)
    items = (TeamStatistic.query
             .filter_by(league=league, season=season)
             .order_by(col.desc()).all())
    return jsonify({"items": [s.to_dict() for s in items], "sort_by": sort_by})