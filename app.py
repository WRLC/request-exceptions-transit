from flask import Flask, render_template, redirect, url_for, flash
from settings import database, shared_secret, log_file
from models import db, InstitutionForm, add_institution_form_submit, Institution, get_all_institutions
import logging
import os
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
@scheduler.task('cron', id='update_reports', minute=0)  # run at 55 minutes past the hour
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


# Home page
@app.route('/')
def hello_world():  # put application's code here
    institutions = get_all_institutions()  # Get all institutions from database
    return render_template('index.html', institutions=institutions)  # Render home page


# View institution
@app.route('/<code>')
def view_institution(code):
    institution = Institution.query.get_or_404(code)  # Get institution from database
    statuses = Institution.get_statuses(institution)  # Get statuses from Institution class
    request_exceptions = []  # Create empty list for request exceptions

    for status in statuses:  # Loop through statuses
        exceptions = Institution.get_exceptions_by_status(institution, status.borreqstat)  # Get exceptions by status
        request_exceptions.append(exceptions)  # Add exceptions to list

    # Render institution page
    return render_template('institution.html', institution=institution, exceptions=request_exceptions)


# Edit institution
@app.route('/<code>/edit', methods=['GET', 'POST'])
def edit_institution(code):
    institution = Institution.query.get_or_404(code)  # Get institution from database
    form = InstitutionForm(obj=institution)  # Load form with institution data

    if form.validate_on_submit():  # If form is submitted and valid
        form.populate_obj(institution)  # Populate institution with form data
        db.session.commit()  # Commit changes to database
        flash('Institution updated successfully', 'success')  # Flash success message
        return redirect(url_for('view_institution', code=form.code.data))  # Redirect to view institution page

    return render_template('edit_institution.html', form=form)  # Render edit institution page


# Add institution
@app.route('/add', methods=['GET', 'POST'])
def add_institution():
    form = InstitutionForm()  # Load form

    if form.validate_on_submit():  # If form is submitted and valid
        add_institution_form_submit(form)  # Add institution to database
        flash('Institution added successfully', 'success')  # Flash success message
        return redirect(url_for('view_institution', code=form.code.data))  # Redirect to view institution page

    return render_template('add_institution.html', form=form)  # Render add institution page


if __name__ == '__main__':
    app.run()
