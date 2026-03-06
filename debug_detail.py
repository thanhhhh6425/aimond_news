import sys, os
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()
from app import create_app
app = create_app()
with app.app_context():
    from app.models import Club
    clubs = Club.query.filter_by(league="PL").limit(5).all()
    for c in clubs:
        print(f"{c.name}: stadium={c.stadium_name}, badge={c.badge_url}")