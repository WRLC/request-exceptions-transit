from flask import Flask, render_template, redirect, url_for, flash
from settings import database, shared_secret, log_file
from models import InstitutionForm, add_institution_form_submit
import logging
import os
from utils import db
import flask_excel as excel
from logging.handlers import TimedRotatingFileHandler
from flask_apscheduler import APScheduler
import atexit
import schedulers

app = Flask(__name__)

# set up logging to work with WSGI server
if __name__ != '__main__':  # if running under WSGI
    gunicorn_logger = logging.getLogger('gunicorn.error')  # get the gunicorn logger
    app.logger.handlers = gunicorn_logger.handlers  # set the app logger handlers to the gunicorn logger handlers
    app.logger.setLevel(gunicorn_logger.level)  # set the app logger level to the gunicorn logger level

app.config['SCHEDULER_API_ENABLED'] = True  # enable APScheduler
app.config['SESSION_KEY'] = os.urandom(24)  # generate a random session key
app.config['SHARED_SECRET'] = shared_secret  # set the shared secret for JWT
app.config['SQLALCHEMY_DATABASE_URI'] = database  # set the database URI
app.secret_key = app.config['SESSION_KEY']  # set the session key
app.config['LOG_FILE'] = log_file  # set the audit log file

db.init_app(app)  # initialize SQLAlchemy
excel.init_excel(app)  # initialize Flask-Excel

# database
with app.app_context():  # need to be in app context to create the database
    db.create_all()  # create the database

# scheduler
scheduler = APScheduler()  # create the scheduler
scheduler.init_app(app)  # initialize the scheduler
scheduler.start()  # start the scheduler
atexit.register(lambda: scheduler.shutdown())  # Shut down the scheduler when exiting the app


# Background task to update the reports
@scheduler.task('cron', id='update_reports', minute=55)  # run at 55 minutes past the hour
def update_reports():
    with scheduler.app.app_context():  # need to be in app context to access the database
        schedulers.update_reports()  # update the reports


# set up error handlers & templates for HTTP codes used in abort()
#   see http://flask.pocoo.org/docs/1.0/patterns/errorpages/
# 400 error handler
@app.errorhandler(400)
def badrequest(e):
    return render_template('error_400.html', e=e), 400  # render the error template


# 403 error handler
@app.errorhandler(403)
def forbidden(e):
    return render_template('unauthorized.html', e=e), 403  # render the error template


# 500 error handler
@app.errorhandler(500)
def internalerror(e):
    return render_template('error_500.html', e=e), 500  # render the error template


# audit log
audit_log = logging.getLogger('audit')  # create the audit log
audit_log.setLevel(logging.INFO)  # set the audit log level
file_handler = TimedRotatingFileHandler(app.config['LOG_FILE'], when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(logging.Formatter('%(asctime)s\t%(message)s'))  # set the file handler format
audit_log.addHandler(file_handler)  # add the file handler to the audit log


@app.route('/')
def hello_world():  # put application's code here
    content = 'Hello World!'
    return render_template('index.html', content=content)


@app.route('/institution/add', methods=['GET', 'POST'])
def add_institution():
    form = InstitutionForm()

    if form.validate_on_submit():
        message = add_institution_form_submit(form)
        flash(message, 'success')
        return redirect(url_for('hello_world'))

    return render_template('add_institution.html', form=form)


if __name__ == '__main__':
    app.run()
