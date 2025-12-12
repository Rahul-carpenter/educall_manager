import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env (for local use)
load_dotenv()

class Config:
    # Get the full DATABASE_URL from env (Render provides this automatically)
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        if os.getenv("FLASK_ENV") == "testing":
            DATABASE_URL = "sqlite:///:memory:"
        else:
            raise RuntimeError("DATABASE_URL is not set!")

    # Convert postgres:// to postgresql:// for SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # App Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")

    # Mail Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ["true", "1", "yes"]
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "rc26022020@gmail.com")
