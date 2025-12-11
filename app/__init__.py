from flask import Flask
import os
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    app.jinja_env.globals['datetime'] = datetime.datetime

    # import routes AFTER app is created
    from app import routes, models

    return app
