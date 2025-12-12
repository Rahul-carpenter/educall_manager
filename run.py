from app import app
import os

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
