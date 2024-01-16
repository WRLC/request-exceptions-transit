from flask import Flask
from app.extensions import db, scheduler
from config import Config
import atexit


def create_app(config_class=Config):
    app = Flask(__name__)  # Create the Flask app
    app.config.from_object(config_class)  # Load the configuration file

    # Initialize Flask extensions here
    db.init_app(app)  # Initialize the database
    scheduler.init_app(app)  # Initialize the scheduler

    # Register blueprints here
    from app.report import bp as report_bp  # Import the report blueprint
    app.register_blueprint(report_bp)  # Register the report blueprint

    # App context
    from app.models import externalrequestintransit, institution, instupdate, requestexception, statususer, \
        transitstart, user, userday
    from app.schedulers import schedulers
    with app.app_context():
        db.create_all()
        scheduler.start()  # start the scheduler
        atexit.register(lambda: scheduler.shutdown())  # Shut down the scheduler when exiting the app

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db, "scheduler": scheduler}

    return app
