from app import app, db
from flask_migrate import Migrate, upgrade
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Initialize Flask-Migrate
migrate_obj = Migrate(app, db)

if __name__ == "__main__":
    with app.app_context():
        upgrade()  # run migrations
    app.run(host="0.0.0.0", port=5000)

