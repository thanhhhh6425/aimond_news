import sys, os
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    # Tao bang neu chua co (an toan voi ca SQLite lan PostgreSQL)
    db.create_all()

    # Them cot moi neu chua co (dung try/except per column, rollback sau moi loi)
    cols = [
        ("is_knockout", "BOOLEAN DEFAULT FALSE"),
        ("leg",         "INTEGER"),
        ("agg_home",    "INTEGER"),
        ("agg_away",    "INTEGER"),
        ("ended_aet",   "BOOLEAN DEFAULT FALSE"),
        ("ended_pen",   "BOOLEAN DEFAULT FALSE"),
        ("events_json", "TEXT"),
        ("minute",      "INTEGER"),
    ]
    for col, dtype in cols:
        try:
            db.session.execute(db.text(f"ALTER TABLE matches ADD COLUMN {col} {dtype}"))
            db.session.commit()
            print(f"  Added column: {col}")
        except Exception as e:
            db.session.rollback()  # Quan trong: rollback de khong bi dong bang
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  Already exists: {col}")
            else:
                print(f"  Error {col}: {e}")

    # Crawl lai matches
    from scripts.crawlers.pl_matches  import PLMatchesCrawler
    from scripts.crawlers.ucl_matches import UCLMatchesCrawler
    from scripts.utils.db_writer      import DBWriter
    writer = DBWriter()

    db.session.execute(db.text("DELETE FROM matches"))
    db.session.commit()

    pl = PLMatchesCrawler().run_sync()
    n1 = writer.upsert_matches(pl, "PL")

    ucl = UCLMatchesCrawler().run_sync()
    n2 = writer.upsert_matches(ucl, "UCL")
    print(f"Done: PL={n1}, UCL={n2}")