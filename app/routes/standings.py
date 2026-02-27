"""
app/routes/standings.py - API bảng xếp hạng
"""
from flask import Blueprint, request, jsonify
from app.models import Standing

standings_bp = Blueprint("standings", __name__)

@standings_bp.route("/", methods=["GET"])
def get_standings():
    league = request.args.get("league", "PL").upper()
    season = request.args.get("season", "2025")
    group  = request.args.get("group")
    q = Standing.query.filter_by(league=league, season=season)
    if group: q = q.filter_by(group=group)
    items = q.order_by(Standing.group.asc(), Standing.position.asc()).all()
    return jsonify({"items": [s.to_dict() for s in items], "total": len(items)})

@standings_bp.route("/groups", methods=["GET"])
def get_groups():
    """UCL: trả về dict {group: [teams]}"""
    season = request.args.get("season", "2025")
    items = (Standing.query.filter_by(league="UCL", season=season)
             .order_by(Standing.group.asc(), Standing.position.asc()).all())
    groups = {}
    for s in items:
        key = s.group or "League Phase"
        groups.setdefault(key, []).append(s.to_dict())
    return jsonify({"groups": groups})