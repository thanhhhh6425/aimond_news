"""
reset_and_crawl.py - Xoa DB va crawl lai toan bo
"""
import sys, logging, os
sys.path.insert(0, ".")

# TAT SCHEDULER truoc khi import app
os.environ["DISABLE_SCHEDULER"] = "1"

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()])
logger = logging.getLogger("reset")

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # ── STEP 1: Clear ──────────────────────────────────────────────────────
    logger.info("STEP 1: Clearing database...")
    for tbl in ["statistics","players","standings","matches","clubs"]:
        db.session.execute(db.text(f"DELETE FROM {tbl}"))
    db.session.commit()
    logger.info("  DB cleared!")

    from scripts.utils.db_writer import DBWriter
    writer = DBWriter()

    def crawl(cls, label):
        try:
            records = cls().run_sync()
            logger.info(f"  {label}: {len(records)} records")
            return records
        except Exception as e:
            logger.error(f"  {label} FAILED: {e}")
            import traceback; traceback.print_exc()
            return []

    # ── STEP 2: PL Clubs ───────────────────────────────────────────────────
    logger.info("STEP 2: PL Clubs...")
    from scripts.crawlers.pl_clubs import PLClubsCrawler
    pl_clubs = crawl(PLClubsCrawler, "PL Clubs")
    n = writer.upsert_clubs(pl_clubs, "PL")
    logger.info(f"  => {n} PL clubs in DB")

    # ── STEP 3: UCL Clubs ──────────────────────────────────────────────────
    logger.info("STEP 3: UCL Clubs...")
    from scripts.crawlers.pl_clubs import UCLClubsCrawler
    ucl_clubs = crawl(UCLClubsCrawler, "UCL Clubs")
    n = writer.upsert_clubs(ucl_clubs, "UCL")
    logger.info(f"  => {n} UCL clubs in DB")

    # Verify clubs da co ten
    sample = db.session.execute(db.text(
        "SELECT source_id, name, badge_url FROM clubs WHERE league='PL' LIMIT 3"
    )).fetchall()
    logger.info(f"  PL club samples: {[(r[0],r[1]) for r in sample]}")

    # ── STEP 4: Standings ──────────────────────────────────────────────────
    logger.info("STEP 4: Standings...")
    from scripts.crawlers.pl_standings  import PLStandingsCrawler
    from scripts.crawlers.ucl_standings import UCLStandingsCrawler
    writer.upsert_standings(crawl(PLStandingsCrawler,  "PL Standings"),  "PL")
    writer.upsert_standings(crawl(UCLStandingsCrawler, "UCL Standings"), "UCL")

    # ── STEP 5: Matches ────────────────────────────────────────────────────
    logger.info("STEP 5: Matches...")
    from scripts.crawlers.pl_matches  import PLMatchesCrawler
    from scripts.crawlers.ucl_matches import UCLMatchesCrawler
    writer.upsert_matches(crawl(PLMatchesCrawler,  "PL Matches"),  "PL")
    writer.upsert_matches(crawl(UCLMatchesCrawler, "UCL Matches"), "UCL")

    # ── STEP 6: Players ────────────────────────────────────────────────────
    logger.info("STEP 6: PL Players...")
    from scripts.crawlers.pl_players import PLPlayersCrawler
    writer.upsert_players(crawl(PLPlayersCrawler, "PL Players"), "PL")

    logger.info("STEP 6b: UCL Players...")
    from scripts.crawlers.ucl_players import UCLPlayersCrawler
    writer.upsert_players(crawl(UCLPlayersCrawler, "UCL Players"), "UCL")

    # ── STEP 7: Verify ─────────────────────────────────────────────────────
    logger.info("STEP 7: Verification")
    for tbl in ["clubs","standings","matches","players","statistics"]:
        pl  = db.session.execute(db.text(f"SELECT COUNT(*) FROM {tbl} WHERE league='PL'")).scalar()
        ucl = db.session.execute(db.text(f"SELECT COUNT(*) FROM {tbl} WHERE league='UCL'")).scalar()
        logger.info(f"  {tbl:12}: PL={pl:4d}, UCL={ucl:4d}")

    top5 = db.session.execute(db.text("""
        SELECT p.name, s.goals FROM statistics s
        JOIN players p ON s.player_id=p.id
        WHERE s.league='PL' AND s.goals>0
        ORDER BY s.goals DESC LIMIT 5
    """)).fetchall()
    logger.info("  Top 5 PL goals:")
    for r in top5:
        logger.info(f"    {r[0]}: {r[1]}")

    logger.info("=== DONE ===")