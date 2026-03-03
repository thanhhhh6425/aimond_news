import sys, os
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()
from app import create_app
app = create_app()
with app.app_context():
    from app.models import Player
    p = Player.query.filter_by(league="PL").first()
    data = p.to_dict(include_stats=True)
    # Simulate get_player route - flatten stats
    stats = p.statistics.filter_by(league=p.league, season=p.season).first()
    if stats:
        data.update(stats.to_dict())
    # In ket qua cuoi cung
    for k, v in data.items():
        if any(x in k.lower() for x in ["club", "venue", "stadium", "appear", "minute", "badge"]):
            print(f"  {k}: {v}")
    print("---")
    print(f"appearances in data: {data.get('appearances')}")
    print(f"minutes_played in data: {data.get('minutes_played')}")