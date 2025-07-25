import os
from app import app, db
from flask_migrate import Migrate, upgrade

# Initialize Flask-Migrate
migrate_obj = Migrate(app, db)

if __name__ == "__main__":
    with app.app_context():
        print("🔄 Running DB upgrade...")
        try:
            upgrade()  # Only upgrade, don't generate or init migrations
            print("✅ DB is up-to-date.")
        except Exception as e:
            print(f"❌ Migration error during upgrade: {e}")

    print("🚀 Starting Flask app...")

    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
