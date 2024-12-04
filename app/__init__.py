"""Initialize the Flask app"""
import atexit
from flask import Flask
from config import Config
from app.extensions import db, scheduler
from app.report import bp as report_bp


def create_app(config_class=Config):
    """Create the Flask app"""
    application = Flask(__name__)  # Create the Flask app
    application.config.from_object(config_class)  # Load the configuration file

    # Initialize Flask extensions here
    db.init_app(application)  # Initialize the database
    scheduler.init_app(application)  # Initialize the scheduler

    # Register blueprints here
    application.register_blueprint(report_bp)  # Register the report blueprint

    # App context
    with application.app_context():
        db.create_all()  # Create the database tables
        scheduler.start()  # Start the scheduler
        atexit.register(lambda: scheduler.shutdown())  # pylint: disable=unnecessary-lambda

    # shell context for flask cli
    @application.shell_context_processor
    def ctx():
        return {"app": application, "db": db, "scheduler": scheduler}

    return application
