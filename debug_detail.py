import sys, os
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()
from app import create_app
app = create_app()
with app.app_context():
    from app.routes.chatbot import _get_full_context
    ctx = _get_full_context()
    for line in ctx.split("\n"):
        if any(k in line.lower() for k in ["man city", "manchester city", "arsenal", "tong ban", "so luong"]):
            print(line)