import sys, os
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()
from app import create_app
app = create_app()
with app.app_context():
    from app.models import Match
    rows = (Match.query.filter_by(league="PL", season="2025", matchweek=29)
            .order_by(Match.kickoff_at).all())
    for r in rows:
        has_events = bool(r.events_json)
        print(f"{r.home_team_name} vs {r.away_team_name} | {r.status} | events={'YES' if has_events else 'NO'}")