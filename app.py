from flask import Flask, render_template, redirect, url_for, flash, session, request, abort, Response
from settings import database, shared_secret, log_file
from models import db, InstitutionForm, add_institution_form_submit, Institution, get_all_institutions, user_login, \
    get_all_last_updates, User
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from flask_apscheduler import APScheduler
import atexit
import schedulers
import emails
import jwt
import pandas as pd
import io
from functools import wraps

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

# database
with app.app_context():  # need to be in app context to create the database
    db.create_all()  # create the database

# scheduler
scheduler = APScheduler()  # create the scheduler
scheduler.init_app(app)  # initialize the scheduler
scheduler.start()  # start the scheduler
atexit.register(lambda: scheduler.shutdown())  # Shut down the scheduler when exiting the app


# Background task to update the reports
@scheduler.task('cron', id='update_reports', minute=55, max_instances=3)  # run at 55 minutes past the hour
def update_reports():
    with scheduler.app.app_context():  # need to be in app context to access the database
        schedulers.update_reports()  # update the reports


# Background task to send emails
@scheduler.task('cron', id='send_emails', hour=6, max_instances=1)  # run at 6am
def send_emails():
    with scheduler.app.app_context():
        emails.send_emails()  # send the emails


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


# decorator for pages that need auth
def auth_required(f):
    @wraps(f)  # preserve the original function's metadata
    def decorated(*args, **kwargs):  # the wrapper function
        if 'username' not in session:  # if the user is not logged in
            return redirect(url_for('login'))  # redirect to the login page
        else:
            return f(*args, **kwargs)  # otherwise, call the original function

    return decorated


# Home page
@app.route('/')
@auth_required
def hello_world():  # put application's code here
    if 'admin' not in session['authorizations']:  # Check if user is an admin
        return redirect(url_for('view_institution', code=session['user_home']))  # Redirect to institution page

    institutions = get_all_institutions()  # Get all institutions from database
    updates = get_all_last_updates()  # Get all last updates from database

    return render_template('index.html', institutions=institutions, updates=updates)  # Render home page


# Login page
@app.route('/login')
def login():
    if 'username' in session:  # if the user is already logged in
        return redirect(url_for('hello_world'))  # redirect to the home page
    else:
        return render_template('login.html')  # otherwise, render the login page


# Login handler
@app.route('/login/n', methods=['GET'])
def new_login():
    session.clear()  # clear the session
    if 'wrt' in request.cookies:  # if the login cookie is present
        encoded_token = request.cookies['wrt']  # get the login cookie
        user_data = jwt.decode(encoded_token, app.config['SHARED_SECRET'], algorithms=['HS256'])  # decode the token
        user_login(session, user_data)  # log the user in

        if 'exceptions' in session['authorizations']:  # if the user is an exceptions user
            return redirect(url_for('hello_world'))  # redirect to the home page
        else:
            abort(403)  # otherwise, abort with a 403 error
    else:
        return "no login cookie"  # if the login cookie is not present, return an error


# Logout handler
@app.route('/logout')
@auth_required
def logout():
    session.clear()  # clear the session
    return redirect(url_for('hello_world'))  # redirect to the home page


# View institution
@app.route('/<code>')
@auth_required
def view_institution(code):
    if session['user_home'] != code and 'admin' not in session['authorizations']:  # Check if user is an admin
        abort(403)

    institution = Institution.query.get_or_404(code)  # Get institution from database
    updated = Institution.get_last_update(institution)  # Get last updated datetime for nstitution
    statuses = Institution.get_statuses(institution)  # Get statuses for institution class
    request_exceptions = []  # Create empty list for request exceptions

    for status in statuses:  # Loop through statuses
        exceptions = Institution.get_exceptions_by_status(institution, status.borreqstat)  # Get exceptions by status
        request_exceptions.append(exceptions)  # Add exceptions to list

    # Render institution page
    return render_template('institution.html', institution=institution, updated=updated, exceptions=request_exceptions)


# Report download
@app.route('/<code>/download')
@auth_required
def report_download(code):
    if session['user_home'] != code and 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin and not at their home institution, abort with a 403 error

    inst = Institution.query.get_or_404(code)  # get the institution
    reqs = Institution.get_all_requests(inst)  # get all requests for the institution

    buffer = io.BytesIO()

    df = pd.DataFrame.from_dict(reqs)
    df.to_excel(buffer, index=False)

    headers = {
        'Content-Disposition': 'attachment; filename=' + code + '.xlsx',
        'Content-type': 'application/vnd.ms-excel'
    }
    return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)


# Edit institution
@app.route('/<code>/edit', methods=['GET', 'POST'])
@auth_required
def edit_institution(code):
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

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
@auth_required
def add_institution():
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    form = InstitutionForm()  # Load form

    if form.validate_on_submit():  # If form is submitted and valid
        add_institution_form_submit(form)  # Add institution to database
        flash('Institution added successfully', 'success')  # Flash success message
        return redirect(url_for('view_institution', code=form.code.data))  # Redirect to view institution page

    return render_template('add_institution.html', form=form)  # Render add institution page


# View users
@app.route('/users')
@auth_required
def view_users():
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error
    users = db.session.execute(db.select(User).order_by(User.last_login.desc())).scalars()  # get all users
    return render_template('users.html', users=users)  # render the users admin page


if __name__ == '__main__':
    app.run()
