from dotenv import load_dotenv
import os
from flask_migrate import upgrade, migrate, init, stamp
from app import app, db

# Load environment variables from .env
load_dotenv()

def run_migrations():
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    
    with app.app_context():
        if not os.path.exists(migrations_dir):
            print("📂 No migrations folder found. Initializing Alembic...")
            init()
            stamp(revision="head")  # 👈 Avoid missing revision errors
            migrate()
            upgrade()
        else:
            print("✅ Migrations folder found. Running upgrade...")
            try:
                migrate()
                upgrade()
            except Exception as e:
                print(f"⚠️ Migration error: {e}")

if __name__ == "__main__":
    run_migrations()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
