import os
os.environ["DISABLE_SCHEDULER"] = "1"
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    from app.models import Player
    # Kiem tra 1 cau thu UCL cu the
    players = Player.query.filter_by(league="UCL", season="2025").filter(
        Player.shirt_number != None
    ).limit(5).all()
    print(f"UCL players with shirt_number: {Player.query.filter_by(league='UCL',season='2025').filter(Player.shirt_number!=None).count()}")
    for p in players:
        print(f"  {p.name} | shirt={p.shirt_number} | nationality={p.nationality}")