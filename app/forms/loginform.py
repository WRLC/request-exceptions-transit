from flask import current_app
from flask_wtf import FlaskForm
from wtforms import SelectField
from app.extensions import db
from app.models.user import User
from datetime import datetime


# Login form class
class LoginForm(FlaskForm):
    institution = SelectField('Login At', choices=[
        ('au', 'American University'),
        ('amulaw', 'AU Washington College of Law'),
        ('cu', 'Catholic University of America'),
        ('ga', 'Gallaudet University'),
        ('gm', 'George Mason University'),
        ('gw', 'George Washington University'),
        ('gwalaw', 'GW Jacob Burns Law Library'),
        ('hi', 'GW Himmelfarb Health Sciences Library'),
        ('gt', 'Georgetown University'),
        ('gt-law', 'Georgetown University Law'),
        ('hu', 'Howard University'),
        ('mu', 'Marymount University'),
        ('dc', 'University of the District of Columbia'),
        ('wr', 'WRLC SCF'),
    ])

    # Construct login URL
    @staticmethod
    def construct_login_url(institution):
        login_url = current_app.config['SAML_SP']
        login_url += current_app.config['COOKIE_ISSUING_FILE']
        login_url += '?institution='
        login_url += institution
        login_url += '&url='
        login_url += current_app.config['SITE_URL']
        login_url += '/login/n'
        return login_url

    # Log the user in
    @staticmethod
    def user_login(session, user_data):

        # Set the session variables
        session['username'] = user_data['primary_id']  # Set the username
        session['user_home'] = user_data['inst']  # Set the user's home institution
        session['display_name'] = user_data['full_name']  # Set the user's display name
        session['authorizations'] = user_data['authorizations']  # Set the user's authorizations
        session['email'] = user_data['email']  # Set the user's email

        user = LoginForm.check_user(session['username'])  # Check if the user exists in the database

        # If the user is in the database...
        if user is not None:
            LoginForm.set_email(user, session)  # ...set the user's email address
            LoginForm.set_user_admin(user, session)  # ...set the user's admin status
            LoginForm.set_user_allreports(user, session)  # ...set the user's allreports status
            if 'exceptions' in session['authorizations']:
                LoginForm.set_last_login(user)  # ...set the last login time for the user

        # If the user isn't in the database...
        else:
            admincheck = LoginForm.admincheck_user(session)  # ...check if the user is an admin
            allreportscheck = LoginForm.allreportscheck_user(session)  # ...check if the user is an admin
            LoginForm.add_user(session, admincheck, allreportscheck)  # ...add the user to the database
            LoginForm.set_user_admin(user, session)  # ...set the user's admin status
            LoginForm.set_user_allreports(user, session)  # ...set the user's allreports status

    # Check if the user exists in the database
    @staticmethod
    def check_user(username):
        user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
        return user

    # Set the user's email address
    @staticmethod
    def set_email(user, session):
        user.emailaddress = session['email']
        db.session.commit()

    # Set the last login time for the user
    @staticmethod
    def set_last_login(user):
        user.last_login = datetime.now()  # Set the last login time to the current time
        db.session.commit()  # Commit the changes

    # Set the user's admin status based on the database
    @staticmethod
    def set_user_admin(user, session):
        if user.admin is True:  # Check if the user is an admin
            if 'exceptions' not in session['authorizations']:
                session['authorizations'].append(
                    'exceptions')  # If they are, add the admin authorization to the session
            session['authorizations'].append('admin')  # If they are, add the admin authorization to the session

    # Check if the username is in the admin list
    @staticmethod
    def admincheck_user(session):
        if session['username'] in current_app.config['ADMINS']:  # Check if the user is an admin
            admincheck = True  # If they are, set admincheck to True
        else:
            admincheck = False  # If they are not, set admincheck to False

        return admincheck

    # Set the user's allreport status based on the database
    @staticmethod
    def set_user_allreports(user, session):
        if user.allreports is True:  # Check if the user is an admin
            if 'exceptions' not in session['authorizations']:
                session['authorizations'].append(
                    'exceptions')  # If they are, add the admin authorization to the session
            session['authorizations'].append('allreports')  # If they are, add the admin authorization to the session

    # Check if the username is in the allreports list
    @staticmethod
    def allreportscheck_user(session):
        if session['username'] in current_app.config['ALLREPORTS']:  # Check if the user is an admin
            allreportscheck = True  # If they are, set admincheck to True
        else:
            allreportscheck = False  # If they are not, set admincheck to False

        return allreportscheck

    # Add the user to the database
    @staticmethod
    def add_user(session, admincheck, allreportscheck):

        # Create the user object
        user = User(
            username=session['username'],
            displayname=session['display_name'],
            instcode=session['user_home'],
            emailaddress=session['email'],
            admin=admincheck,
            allreports=allreportscheck,
            last_login=datetime.now()
        )
        db.session.add(user)  # Add the user to the database
        db.session.commit()  # Commit the changes
