from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

db = SQLAlchemy()  # Create a database object
scheduler = APScheduler()  # Create a scheduler object
