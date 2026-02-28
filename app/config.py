"""
app/config.py - Cấu hình môi trường cho AimondNews
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "aimond-secret-key-change-in-prod")
    DEBUG = False
    TESTING = False

    # --- Database ---
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # --- Cache ---
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # 5 phút

    # --- Season Config (CỐ ĐỊNH mùa giải 2025-2026) ---
    CURRENT_SEASON = "2025"              # ID mùa giải PL
    CURRENT_SEASON_UCL = "2025"         # ID mùa giải UCL
    PL_SEASON_LABEL = "2025/26"
    UCL_SEASON_LABEL = "2025/26"

    # --- League IDs ---
    PL_COMPETITION_ID = "EN_PR"         # Premier League ID trên PL.com
    UCL_COMPETITION_ID = "UEFA_CHAMPIONS_LEAGUE"

    # --- Crawler ---
    CRAWLER_HEADLESS = True
    CRAWLER_TIMEOUT = 30000             # 30 giây
    CRAWLER_RETRY = 3
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    # --- Scheduler intervals (giây) ---
    SCHEDULE_LIVE_MATCH_INTERVAL = 60          # Cập nhật trận live mỗi 1 phút
    SCHEDULE_STANDINGS_INTERVAL = 3600         # BXH mỗi 1 tiếng
    SCHEDULE_NEWS_INTERVAL = 1800              # Tin tức mỗi 30 phút
    SCHEDULE_PLAYERS_INTERVAL = 86400          # Cầu thủ mỗi 24 tiếng


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///aimond_dev.db"
    )
    CACHE_TYPE = "SimpleCache"
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    # Đã đổi từ RedisCache sang SimpleCache để không bị sập trên Render
    CACHE_TYPE = "SimpleCache"
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}