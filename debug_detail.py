import os

os.environ["DISABLE_SCHEDULER"] = "1"
from scripts.crawlers.ucl_players import UCLPlayersCrawler
from app import create_app
from app.extensions import db
from scripts.utils.db_writer import DBWriter

app = create_app()
with app.app_context():
    records = UCLPlayersCrawler().run_sync()
    with_goals = [r for r in records if r.get("goals", 0) > 0]
    print(f"Records to write - goals>0: {len(with_goals)}")

    writer = DBWriter()
    n = writer.upsert_players(records, league="UCL")
    print(f"Upserted: {n}")

    from app.models import Statistic

    cnt = Statistic.query.filter_by(league="UCL", season="2025").filter(Statistic.goals > 0).count()
    print(f"In DB after upsert - goals>0: {cnt}")