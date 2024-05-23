from app.extensions import db
from app.models.institution import Institution
from datetime import datetime
from flask import current_app


# User class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    displayname = db.Column(db.String(255), nullable=True)
    instcode = db.Column(db.ForeignKey(Institution.inst_code))
    emailaddress = db.Column(db.String(255), nullable=True)
    admin = db.Column(db.Boolean, nullable=False)
    allreports = db.Column(db.Boolean, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Constructor
    def __repr__(self):
        return '<User %r>' % self.username

    # Log the user in
    @staticmethod
    def user_login(session, user_data):
        # Assemble to user's display name
        user_data['DisplayName'] = ''  # Initialize the display name
        if 'GivenName' in user_data:  # if the user has a first name...
            user_data['DisplayName'] += user_data['GivenName'] + ' '  # ...set the first name
        if 'Name' in user_data:
            user_data['DisplayName'] += user_data['Name']

        # Set the session variables
        session['username'] = user_data['UserName']  # Set the username
        session['display_name'] = user_data['DisplayName']  # Set the user's display name
        session['email'] = user_data['Email']  # Set the user's email
        session['user_home'] = Institution.get_inst_code(user_data['University'])
        session['authorizations'] = []  # Initialize the user's authorizations

        user = User.check_user(session['username'])  # Check if the user exists in the database

        # If the user is in the database...
        if user is not None:
            User.set_email(user, session)  # ...set the user's email address
            User.set_user_admin(user, session)  # ...set the user's admin status
            User.set_user_allreports(user, session)  # ...set the user's allreports status
            if 'exceptions' in session['authorizations']:
                User.set_last_login(user)  # ...set the last login time for the user

        # If the user isn't in the database...
        else:
            admincheck = User.admincheck_user(session)  # ...check if the user is an admin
            allreportscheck = User.allreportscheck_user(session)  # ...check if the user is an admin
            User.add_user(session, admincheck, allreportscheck)  # ...add the user to the database
            User.set_user_admin(session, admincheck)  # ...set the user's admin status
            User.set_user_allreports(session, allreportscheck)  # ...set the user's allreports status

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
    def set_user_admin(session, admincheck):
        if admincheck is True:  # Check if the user is an admin
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
    def set_user_allreports(session, allreportscheck):
        if allreportscheck is True:  # Check if the user is an admin
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
