"""
scripts/run_all.py - Chay thu cong tat ca crawlers FotMob
Usage:
  python scripts/run_all.py
  python scripts/run_all.py --only standings
  python scripts/run_all.py --only matches
  python scripts/run_all.py --only news
  python scripts/run_all.py --only players
  python scripts/run_all.py --no-db
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_all")


def run_crawler(crawler_cls, write_db=True):
    crawler = crawler_cls()
    records = crawler.run_sync()
    league = crawler.LEAGUE
    ctype = crawler_cls.__name__.replace("Crawler", "").upper()
    logger.info(f"{league} {ctype}: {len(records)} records")

    if records:
        logger.info(f"  Sample: {records[0]}")

    if write_db and records:
        try:
            from app import create_app
            from scripts.utils.db_writer import DBWriter
            app = create_app()
            with app.app_context():
                writer = DBWriter()
                ctype_lower = ctype.lower()
                if "standings" in ctype_lower:
                    n = writer.upsert_standings(records, league=league)
                elif "matches" in ctype_lower:
                    n = writer.upsert_matches(records, league=league)
                elif "news" in ctype_lower:
                    n = writer.upsert_news(records, league=league)
                elif "players" in ctype_lower:
                    n = writer.upsert_players(records, league=league)
                elif "clubs" in ctype_lower:
                    n = writer.upsert_clubs(records, league=league)
                else:
                    n = 0
                logger.info(f"  DB upsert: {n} rows affected")
        except Exception as e:
            logger.error(f"  DB error: {e}", exc_info=True)

    return records


def main(only=None, no_db=False):
    from scripts.crawlers.pl_standings  import PLStandingsCrawler
    from scripts.crawlers.ucl_standings import UCLStandingsCrawler
    from scripts.crawlers.pl_matches    import PLMatchesCrawler
    from scripts.crawlers.ucl_matches   import UCLMatchesCrawler
    from scripts.crawlers.pl_news       import PLNewsCrawler
    from scripts.crawlers.ucl_news      import UCLNewsCrawler
    from scripts.crawlers.pl_players    import PLPlayersCrawler
    from scripts.crawlers.ucl_players   import UCLPlayersCrawler

    from scripts.crawlers.pl_clubs    import PLClubsCrawler, UCLClubsCrawler

    tasks = {
        "standings": [PLStandingsCrawler, UCLStandingsCrawler],
        "matches":   [PLMatchesCrawler,   UCLMatchesCrawler],
        "news":      [PLNewsCrawler,      UCLNewsCrawler],
        "players":   [PLPlayersCrawler,   UCLPlayersCrawler],
        "clubs":     [PLClubsCrawler,     UCLClubsCrawler],
    }

    write_db = not no_db
    if no_db:
        logger.info("=== DRY RUN (--no-db): khong ghi vao database ===")

    if only:
        crawlers = tasks.get(only, [])
        if not crawlers:
            logger.error(f"Unknown: {only}. Chon: {list(tasks.keys())}")
            return
        for cls in crawlers:
            run_crawler(cls, write_db)
    else:
        for group, crawlers in tasks.items():
            logger.info(f"\n=== {group.upper()} ===")
            for cls in crawlers:
                run_crawler(cls, write_db)

    logger.info("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", type=str, default=None)
    parser.add_argument("--no-db", action="store_true")
    args = parser.parse_args()
    main(only=args.only, no_db=args.no_db)