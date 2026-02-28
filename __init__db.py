import os
os.environ['DISABLE_SCHEDULER'] = '1'
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print("Done!")