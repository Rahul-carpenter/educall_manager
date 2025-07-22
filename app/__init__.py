from flask import Flask
import os
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)

app.jinja_env.globals['datetime'] = datetime.datetime

from app import routes, models
