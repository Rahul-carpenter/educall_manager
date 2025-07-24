from app import app, db
from flask_migrate import Migrate, upgrade, migrate, init, stamp
import os

migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")

migrate_obj = Migrate(app, db)

def setup_migrations():
    with app.app_context():
        if not os.path.exists(migrations_dir):
            print("📂 No migrations folder found. Initializing...")
            init()
            stamp()  # mark current DB state to avoid duplicate revision issues
            migrate(message="Initial migration")
            upgrade()
        else:
            print("✅ Migrations folder found. Running upgrade...")
            migrate(message="Auto migration")
            upgrade()

if __name__ == "__main__":
    setup_migrations()
    print("🚀 Starting the Flask app...")
    app.run(debug=True)  # Turn off debug in production
