"""
app/routes/news.py - API tin tức
"""
from flask import Blueprint, request, jsonify
from flask_caching import Cache
from app.models import News
from app.extensions import cache

news_bp = Blueprint("news", __name__)

def _paginate(q, page, per_page=20):
    p = q.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [i.to_dict() for i in p.items],
        "total": p.total, "page": p.page,
        "pages": p.pages, "per_page": per_page
    }

@news_bp.route("/", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
def get_news():
    league = request.args.get("league", "PL").upper()
    season = request.args.get("season", "2025")
    category = request.args.get("category")
    page = int(request.args.get("page", 1))
    q = News.query.filter_by(league=league, season=season)
    if category: q = q.filter_by(category=category)
    q = q.order_by(News.published_at.desc())
    return jsonify(_paginate(q, page))

@news_bp.route("/<int:news_id>", methods=["GET"])
@cache.cached(timeout=600)
def get_news_detail(news_id):
    n = News.query.get_or_404(news_id)
    return jsonify(n.to_dict(full=True))

@news_bp.route("/search", methods=["GET"])
def search_news():
    q_str = request.args.get("q", "").strip()
    league = request.args.get("league", "").upper()
    page = int(request.args.get("page", 1))
    if not q_str:
        return jsonify({"items": [], "total": 0})
    q = News.query.filter(News.title.ilike(f"%{q_str}%"))
    if league: q = q.filter_by(league=league)
    q = q.order_by(News.published_at.desc())
    return jsonify(_paginate(q, page, per_page=10))

@news_bp.route("/latest", methods=["GET"])
@cache.cached(timeout=120, query_string=True)
def get_latest():
    league = request.args.get("league", "PL").upper()
    limit = min(int(request.args.get("limit", 6)), 20)
    items = (News.query.filter_by(league=league, season="2025")
             .order_by(News.published_at.desc()).limit(limit).all())
    return jsonify({"items": [n.to_dict() for n in items]})