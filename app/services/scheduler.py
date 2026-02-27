"""
app/services/scheduler.py
APScheduler - Background jobs tự động cập nhật dữ liệu.
Real-time: LIVE(60s), END_DETECT(90s), STANDINGS(1h), NEWS(30m), PLAYERS(24h), FIXTURES(6h)
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger(__name__)
_scheduler = None


def start_scheduler(app):
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(
        jobstores={"default": MemoryJobStore()},
        executors={"default": ThreadPoolExecutor(max_workers=4)},
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 30},
        timezone="UTC",
    )
    _scheduler.add_job(_job_live_matches, IntervalTrigger(seconds=60),
                       id="live_matches", args=[app], replace_existing=True)
    _scheduler.add_job(_job_match_end_detector, IntervalTrigger(seconds=90),
                       id="match_end_detector", args=[app], replace_existing=True)
    _scheduler.add_job(_job_standings, IntervalTrigger(hours=1),
                       id="standings", args=[app], replace_existing=True)
    _scheduler.add_job(_job_news, IntervalTrigger(minutes=30),
                       id="news", args=[app], replace_existing=True)
    _scheduler.add_job(_job_players, CronTrigger(hour=3, minute=0),
                       id="players", args=[app], replace_existing=True)
    _scheduler.add_job(_job_fixtures, IntervalTrigger(hours=6),
                       id="fixtures", args=[app], replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started with 6 jobs")
    _run_initial_crawl(app)


def _run_initial_crawl(app):
    import threading
    def run():
        with app.app_context():
            _job_standings(app)
            _job_fixtures(app)
            _job_news(app)
    threading.Thread(target=run, daemon=True).start()


def _run_crawler_sync(crawler_class):
    try:
        return crawler_class().run_sync()
    except Exception as e:
        logger.error(f"Crawler error: {e}")
        return []


def _job_live_matches(app):
    with app.app_context():
        try:
            from app.models import Match
            live_count = Match.query.filter_by(status="LIVE").count()
            soon = Match.query.filter(
                Match.status == "SCHEDULED",
                Match.kickoff_at <= datetime.now(timezone.utc) + timedelta(minutes=10),
                Match.kickoff_at >= datetime.now(timezone.utc) - timedelta(hours=3),
            ).count()
            if not live_count and not soon:
                return
            from scripts.crawlers.pl_matches import PLMatchesCrawler
            from scripts.crawlers.ucl_matches import UCLMatchesCrawler
            from scripts.utils.db_writer import DBWriter
            data = (_run_crawler_sync(PLMatchesCrawler) +
                    _run_crawler_sync(UCLMatchesCrawler))
            if data:
                DBWriter().upsert_matches(data)
        except Exception as e:
            logger.error(f"LiveJob error: {e}")


def _job_match_end_detector(app):
    with app.app_context():
        try:
            from app.models import Match
            now = datetime.now(timezone.utc)
            ended = Match.query.filter(
                Match.status == "LIVE",
                Match.kickoff_at <= now - timedelta(minutes=95),
            ).all()
            if not ended:
                return
            from scripts.crawlers.pl_matches import PLMatchesCrawler
            from scripts.crawlers.ucl_matches import UCLMatchesCrawler
            from scripts.utils.db_writer import DBWriter
            results = (_run_crawler_sync(PLMatchesCrawler) +
                       _run_crawler_sync(UCLMatchesCrawler))
            ended_ids = {m.source_id for m in ended}
            just_finished = [r for r in results if r.get("status") == "FT"
                             and r.get("source_id") in ended_ids]
            if just_finished:
                DBWriter().upsert_matches(just_finished)
                logger.info(f"EndDetector: {len(just_finished)} FT -> updating standings")
                _job_standings(app)
        except Exception as e:
            logger.error(f"EndDetector error: {e}")


def _job_standings(app):
    with app.app_context():
        try:
            from scripts.crawlers.pl_standings import PLStandingsCrawler
            from scripts.crawlers.ucl_standings import UCLStandingsCrawler
            from scripts.utils.db_writer import DBWriter
            w = DBWriter()
            pl = _run_crawler_sync(PLStandingsCrawler)
            ucl = _run_crawler_sync(UCLStandingsCrawler)
            if pl: w.upsert_standings(pl, league="PL")
            if ucl: w.upsert_standings(ucl, league="UCL")
        except Exception as e:
            logger.error(f"StandingsJob error: {e}")


def _job_news(app):
    with app.app_context():
        try:
            from scripts.crawlers.pl_news import PLNewsCrawler
            from scripts.crawlers.ucl_news import UCLNewsCrawler
            from scripts.utils.db_writer import DBWriter
            w = DBWriter()
            pl = _run_crawler_sync(PLNewsCrawler)
            ucl = _run_crawler_sync(UCLNewsCrawler)
            if pl: w.upsert_news(pl)
            if ucl: w.upsert_news(ucl)
        except Exception as e:
            logger.error(f"NewsJob error: {e}")


def _job_players(app):
    with app.app_context():
        try:
            from scripts.crawlers.pl_players import PLPlayersCrawler
            from scripts.utils.db_writer import DBWriter
            data = _run_crawler_sync(PLPlayersCrawler)
            if data: DBWriter().upsert_players(data)
        except Exception as e:
            logger.error(f"PlayersJob error: {e}")


def _job_fixtures(app):
    with app.app_context():
        try:
            from scripts.crawlers.pl_matches import PLMatchesCrawler
            from scripts.crawlers.ucl_matches import UCLMatchesCrawler
            from scripts.utils.db_writer import DBWriter
            w = DBWriter()
            pl = _run_crawler_sync(PLMatchesCrawler)
            ucl = _run_crawler_sync(UCLMatchesCrawler)
            if pl: w.upsert_matches(pl)
            if ucl: w.upsert_matches(ucl)
        except Exception as e:
            logger.error(f"FixturesJob error: {e}")


def trigger_job(job_id: str, app) -> bool:
    mapping = {
        "live": _job_live_matches, "standings": _job_standings,
        "news": _job_news, "players": _job_players, "fixtures": _job_fixtures,
    }
    fn = mapping.get(job_id)
    if fn:
        fn(app)
        return True
    return False


def get_scheduler_status() -> dict:
    if not _scheduler:
        return {"running": False, "jobs": []}
    return {
        "running": _scheduler.running,
        "jobs": [{"id": j.id, "name": j.name,
                  "next_run": j.next_run_time.isoformat() if j.next_run_time else None}
                 for j in _scheduler.get_jobs()],
    }