"""
run.py - Entry point để chạy AimondNews
"""
import os
from app import create_app

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

# Tu dong tao bang khi khoi dong (can thiet cho PostgreSQL tren Render)
with app.app_context():
    from app.extensions import db
    db.create_all()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=(env == "development"),
        use_reloader=False,  # Tắt reloader để Scheduler không bị khởi động 2 lần
    )