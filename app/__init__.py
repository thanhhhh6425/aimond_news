"""
app/__init__.py - Flask Application Factory
"""
import os
from flask import Flask
from .config import config_map
from .extensions import db, migrate, login_manager, bcrypt, cors, cache


def create_app(env: str = None) -> Flask:
    """
    Tạo và cấu hình Flask app theo pattern App Factory.
    Gọi: create_app('development') hoặc create_app('production')
    """
    env = env or os.getenv("FLASK_ENV", "development")
    config = config_map.get(env, config_map["default"])

    # Đường dẫn tuyệt đối — hoạt động đúng trên cả Windows lẫn Linux
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config.from_object(config)

    # ── Khởi tạo Extensions ──
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    cache.init_app(app)

    # ── Đăng ký Models (để Migrate nhận diện) ──
    with app.app_context():
        from .models import (  # noqa: F401
            User, Club, Player, Match, Standing,
            Statistic, TeamStatistic, News,
        )

    # ── Đăng ký Blueprints (Routes) ──
    _register_blueprints(app)

    # ── Khởi động Scheduler (Background Jobs) ──
    if not app.testing:
        if not os.environ.get("DISABLE_SCHEDULER"):
            from .services.scheduler import start_scheduler
            start_scheduler(app)

    return app


def _register_blueprints(app: Flask):
    from .routes.auth import auth_bp
    from .routes.news import news_bp
    from .routes.matches import matches_bp
    from .routes.standings import standings_bp
    from .routes.statistics import statistics_bp
    from .routes.players import players_bp
    from .routes.clubs import clubs_bp
    from .routes.chatbot import chatbot_bp
    from .routes.pages import pages_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(news_bp, url_prefix="/api/news")
    app.register_blueprint(matches_bp, url_prefix="/api/matches")
    app.register_blueprint(standings_bp, url_prefix="/api/standings")
    app.register_blueprint(statistics_bp, url_prefix="/api/statistics")
    app.register_blueprint(players_bp, url_prefix="/api/players")
    app.register_blueprint(clubs_bp, url_prefix="/api/clubs")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(pages_bp)  # Serve HTML (no prefix)