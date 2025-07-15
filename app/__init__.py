from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models
