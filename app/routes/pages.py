"""
app/routes/pages.py - Serve HTML pages
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    return render_template("pages/home.html")

@pages_bp.route("/matches")
def matches():
    return render_template("pages/matches.html")

@pages_bp.route("/table")
def table():
    return render_template("pages/table.html")

@pages_bp.route("/statistics")
def statistics():
    return render_template("pages/statistics.html")

@pages_bp.route("/players")
def players():
    return render_template("pages/players.html")

@pages_bp.route("/players/<int:player_id>")
def player_detail(player_id):
    return render_template("pages/player_detail.html", player_id=player_id)

@pages_bp.route("/clubs")
def clubs():
    return render_template("pages/clubs.html")

@pages_bp.route("/clubs/<int:club_id>")
def club_detail(club_id):
    return render_template("pages/club_detail.html", club_id=club_id)

@pages_bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("pages.index"))
    return render_template("pages/login.html")

@pages_bp.route("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("pages.index"))
    return render_template("pages/register.html")

@pages_bp.route("/profile")
@login_required
def profile():
    return render_template("pages/profile.html")

# Admin: trigger manual crawl
@pages_bp.route("/api/admin/trigger/<job_id>", methods=["POST"])
@login_required
def trigger_crawl(job_id):
    from flask import current_app, jsonify
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    from app.services.scheduler import trigger_job
    ok = trigger_job(job_id, current_app._get_current_object())
    return jsonify({"success": ok, "job": job_id})

@pages_bp.route("/api/admin/scheduler", methods=["GET"])
@login_required
def scheduler_status():
    from flask import jsonify
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    from app.services.scheduler import get_scheduler_status
    return jsonify(get_scheduler_status())

@pages_bp.route("/bracket")
def bracket():
    return render_template("pages/bracket.html")

@pages_bp.route("/news")
def news():
    return render_template("pages/news.html")