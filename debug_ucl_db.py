import sys, os, json
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")

from app import create_app
app = create_app()

with app.app_context():
    from app.models import Match, Club
    from sqlalchemy import func

    print("=" * 50)
    print("UCL MATCHES SUMMARY")
    print("=" * 50)
    total = Match.query.filter_by(league="UCL").count()
    ft    = Match.query.filter_by(league="UCL", status="FT").count()
    sch   = Match.query.filter_by(league="UCL", status="SCHEDULED").count()
    print(f"Total: {total} | FT: {ft} | SCHEDULED: {sch}")

    print("\n--- Rounds ---")
    rounds = (Match.query.filter_by(league="UCL")
              .with_entities(Match.round, Match.matchweek, func.count(Match.id))
              .group_by(Match.round, Match.matchweek).all())
    for r, mw, cnt in rounds:
        print(f"  round='{r}' matchweek={mw}: {cnt} matches")

    print("\n--- Sample matches ---")
    for m in Match.query.filter_by(league="UCL").limit(5).all():
        print(f"  {m.home_team_name} vs {m.away_team_name} | {m.status} | round={m.round} | knockout={m.is_knockout}")

    print("\n--- Knockout ---")
    ko = Match.query.filter_by(league="UCL", is_knockout=True).count()
    print(f"  is_knockout=True: {ko}")

    print("\n--- API /api/matches/rounds?league=UCL ---")
    client = app.test_client()
    resp = client.get("/api/matches/rounds?league=UCL&season=2025")
    data = json.loads(resp.data)
    print(f"  HTTP {resp.status_code}")
    if resp.status_code == 200:
        print(f"  rounds: {data.get('rounds')}")
        print(f"  current_round: {data.get('current_round')}")
    else:
        print(f"  Error: {data}")

    print("\n--- API /api/matches/bracket?league=UCL ---")
    resp2 = client.get("/api/matches/bracket?league=UCL&season=2025")
    data2 = json.loads(resp2.data)
    print(f"  HTTP {resp2.status_code}")
    if resp2.status_code == 200:
        print(f"  Keys: {list(data2.keys())}")
    else:
        print(f"  Error: {data2}")