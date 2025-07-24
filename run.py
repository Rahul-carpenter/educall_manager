import os
from app import app, db
from flask_migrate import Migrate, upgrade, migrate, init, stamp

# Migration directory
migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
migrate_obj = Migrate(app, db)

def setup_migrations():
    with app.app_context():
        try:
            if not os.path.exists(migrations_dir) or not os.listdir(migrations_dir):
                print("📂 No migrations folder or it's empty. Initializing migrations...")
                init()
                stamp()  # avoid duplicate revisions
                migrate(message="Initial migration")
                upgrade()
            else:
                print("✅ Migrations folder found. Running upgrade...")
                migrate(message="Auto migration")
                upgrade()
        except Exception as e:
            print(f"❌ Migration error: {e}")

if __name__ == "__main__":
    setup_migrations()
    print("🚀 Starting Flask app...")

    # Use environment variable to toggle debug mode
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]

    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
