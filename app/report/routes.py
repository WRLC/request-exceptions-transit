"""
This module contains the routes for the report blueprint.
"""
from pymemcache.client.base import Client as memcacheClient
from flask import current_app, render_template, redirect, url_for, session, flash, request, abort, Response
from app.extensions import db
from app.utils import utils
from app.models.institution import Institution
from app.models.user import User, user_login
from app.forms.institutionform import InstitutionForm
from app.forms.usersettingsform import UserSettingsForm
import pandas as pd
import io
from functools import wraps
from app.report import bp


# set up error handlers & templates for HTTP codes used in abort()
@bp.errorhandler(400)
def badrequest(e):
    """
    400 error handler

    :param e: error
    :return: error template
    """
    return render_template('error_400.html', e=e), 400  # render the error template


@bp.errorhandler(403)
def forbidden(e):
    """ 403 error handler """
    return render_template('unauthorized.html', e=e), 403  # render the error template


@bp.errorhandler(500)
def internalerror(e):
    """ 500 error handler """
    return render_template('error_500.html', e=e), 500  # render the error template


def auth_required(f):
    """ Decorator to require authentication """
    @wraps(f)  # preserve the original function's metadata
    def decorated(*args, **kwargs):
        """ Wrapper function """
        if 'username' not in session:  # if the user is not logged in
            return redirect(url_for('report.login'))  # redirect to the login page
        else:
            return f(*args, **kwargs)  # otherwise, call the original function

    return decorated


@bp.route('/')
@auth_required
def hello_world():  # put application's code here
    """ Home page """
    # Check if user is an admin or has allreports authorization
    if 'admin' not in session['authorizations'] and 'allreports' not in session['authorizations']:
        return redirect(url_for('report.view_institution', code=session['user_home']))  # Redirect to institution page

    institutions = utils.get_all_institutions()  # Get all institutions from database
    updates = utils.get_all_last_updates()  # Get all last updates from database

    return render_template('index.html', institutions=institutions, updates=updates)  # Render home page


@bp.route('/login/')
def login():
    """ Login page """
    saml_sp = current_app.config['SAML_SP']  # Get SAML SP URL
    cookie_file = current_app.config['COOKIE_ISSUING_FILE']  # Get cookie issuing file
    slug = current_app.config['SERVICE_SLUG']  # Get service slug
    return redirect(saml_sp + cookie_file + '?service=' + slug)  # Redirect to SAML SP


@bp.route('/login/n/', methods=['GET'])
def new_login():
    """ New login handler """
    cookie_name = current_app.config['COOKIE_PREFIX'] + current_app.config['SERVICE_SLUG']
    session.clear()  # clear the session
    if cookie_name in request.cookies:  # if the login cookie is present
        memcached_key = request.cookies[cookie_name]  # get the login cookie
        memcached = memcacheClient((current_app.config['MEMCACHED_SERVER'], 11211))
        user_data = {}
        for line in memcached.get(memcached_key).decode('utf-8').splitlines():
            key, value = line.split('=')
            user_data[key] = value
        user_login(session, user_data)  # Log the user in
        return redirect(url_for('report.hello_world'))
    else:
        return "no login cookie"  # if the login cookie is not present, return an error


@bp.route('/logout/')
@auth_required
def logout():
    """ Logout handler """
    session.clear()  # clear the session
    return redirect(
        current_app.config['SAML_SP'] +
        current_app.config['LOGOUT_SCRIPT'] +
        '?service=' +
        current_app.config['SERVICE_SLUG']
    )  # redirect to the logout script


@bp.route('/<code>/')
@auth_required
def view_institution(code):
    """ Institution page """
    if (
        session['user_home'] != code and  # Check if user is at their home institution
        'admin' not in session['authorizations'] and  # Check if user is an admin
        'allreports' not in session['authorizations']  # Check if user has allreports authorization
    ):
        # if the user is not at their home institution, doesn't have allreports authorization, and is not an admin,
        # abort with a 403 error
        abort(403)

    institution = Institution.query.get_or_404(code)  # Get institution from database
    updated = utils.get_last_update(institution.code)  # Get last updated datetime for nstitution
    request_exceptions = utils.get_exceptions(session, institution)  # get user's exceptions for institution

    # Render institution page
    return render_template('institution.html', institution=institution, updated=updated, exceptions=request_exceptions)


@bp.route('/<code>/download/')
@auth_required
def report_download(code):
    """ Download report """
    if (
        session['user_home'] != code and  # Check if user is at their home institution
        'admin' not in session['authorizations'] and  # Check if user is an admin
        'allreports' not in session['authorizations']  # Check if user has allreports authorization
    ):
        # if the user is not at their home institution, doesn't have allreports authorization, and is not an admin,
        # abort with a 403 error
        abort(403)

    user = utils.get_user(session['username'])  # get the user from the database
    inst = Institution.query.get_or_404(code)  # get the institution
    reqs = utils.get_exceptions_xlsx(user, inst)  # get all requests for the institution

    buffer = io.BytesIO()

    df = pd.DataFrame.from_dict(reqs)
    df.to_excel(buffer, index=False)

    headers = {
        'Content-Disposition': 'attachment; filename=' + code + '.xlsx',
        'Content-type': 'application/vnd.ms-excel'
    }
    return Response(buffer.getvalue(), mimetype='application/vnd.ms-excel', headers=headers)


@bp.route('/<code>/edit/', methods=['GET', 'POST'])
@auth_required
def edit_institution(code):
    """ Edit institution page """
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    institution = Institution.query.get_or_404(code)  # Get institution from database
    form = InstitutionForm(obj=institution)  # Load form with institution data

    if form.validate_on_submit():  # If form is submitted and valid
        form.populate_obj(institution)  # Populate institution with form data
        db.session.commit()  # Commit changes to database
        flash('Institution updated successfully', 'success')  # Flash success message
        return redirect(url_for('report.view_institution', code=form.code.data))  # Redirect to view institution page

    return render_template('edit_institution.html', form=form)  # Render edit institution page


@bp.route('/add/', methods=['GET', 'POST'])
@auth_required
def add_institution():
    """ Add institution page """
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    form = InstitutionForm()  # Load form

    if form.validate_on_submit():  # If form is submitted and valid
        form.add_institution_form_submit(form)  # Add institution to database
        flash('Institution added successfully', 'success')  # Flash success message
        return redirect(url_for('report.view_institution', code=form.code.data))  # Redirect to view institution page

    return render_template('add_institution.html', form=form)  # Render add institution page


# noinspection PyUnresolvedReferences
@bp.route('/users/')
@auth_required
def view_users():
    """ Users page """
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error
    users = db.session.execute(db.select(User).order_by(User.last_login.desc())).scalars()  # get all users
    return render_template('users.html', users=users)  # render the users admin page


@bp.route('/settings/', methods=['GET', 'POST'])
@auth_required
def edit_settings():
    """ Edit user settings """
    # get the user from the database
    user = utils.get_user(session['username'])  # get the user from the database
    days = utils.get_user_days(user)  # get the user's days
    user_statuses = utils.get_user_statuses(user)  # user statuses
    user_active = utils.get_user_active(user)  # user active status
    userdays = []  # create an empty list for the user's days
    useractive = 0  # create an empty variable for the user's active status
    userstatuses = []  # create an empty list for the user's statuses

    for day in days:  # for each existing user day
        userdays.append(day.day)  # add the day to the list

    if user_active:  # if the user has an active status
        useractive = user_active.active

    for status in user_statuses:  # for each existing user status
        userstatuses.append(status.status)

    form = UserSettingsForm()  # load the form

    # if the form is submitted and valid
    if form.validate_on_submit():
        form.update_user_settings(form, user)  # update the user settings
        flash('Settings updated successfully', 'success')  # flash a success message
        return redirect(url_for('report.edit_settings'))

    # render the settings page
    return render_template('settings.html', form=form, days=userdays, active=useractive,
                           statuses=userstatuses, user=user)
