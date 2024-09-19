from app.extensions import db
from app.models.institution import Institution
from datetime import datetime
from flask import current_app
from flask.sessions import SessionMixin


# User class
class User(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(255), nullable=False)
    displayname: str = db.Column(db.String(255), nullable=True)
    instcode: str = db.Column(db.ForeignKey(Institution.inst_code))
    emailaddress: str = db.Column(db.String(255), nullable=True)
    admin: bool = db.Column(db.Boolean, nullable=False)
    allreports: bool = db.Column(db.Boolean, nullable=False)
    last_login: datetime = db.Column(db.DateTime, nullable=True)

    # Constructor
    def __repr__(self) -> str:
        return '<User %r>' % self.username


# Log the user in
def user_login(session: SessionMixin, user_data: dict) -> None:
    # Assemble to user's display name
    user_data['DisplayName']: str = ''  # Initialize the display name
    if 'GivenName' in user_data:  # if the user has a first name...
        user_data['DisplayName'] += user_data['GivenName'] + ' '  # ...set the first name
    if 'Name' in user_data:
        user_data['DisplayName'] += user_data['Name']

    # Set the session variables
    session['username']: str = user_data['UserName']  # Set the username
    session['display_name']: str = user_data['DisplayName']  # Set the user's display name
    session['email']: str = user_data['Email']  # Set the user's email
    session['user_home']: str = Institution.get_inst_code(user_data['University'])  # Set the user's home institution
    session['authorizations']: list = []  # Initialize the user's authorizations

    user: User = check_user(session['username'])  # Check if the user exists in the database

    # If the user is in the database...
    if user is not None:
        admincheck: bool = admincheck_user(session, user)  # ...check if the user is admin
        allreportscheck: bool = allreportscheck_user(session)  # ...check if the user is an admin
        set_email(user, session)  # ...set the user's email address
        if admincheck:  # ...set the user's admin status
            session['authorizations'].append('admin')
            user.admin = True
            db.session.commit()
        if allreportscheck:
            session['authorizations'].append('allreports')
            user.allreports = True
            db.session.commit()
        set_last_login(user)  # ...set the last login time for the user

    # If the user isn't in the database...
    else:
        admincheck: bool = admincheck_user(session)  # ...check if the user is an admin
        allreportscheck: bool = allreportscheck_user(session)  # ...check if the user is an admin
        add_user(session, admincheck, allreportscheck, user_data)  # ...add the user to the database
        set_admin(session, admincheck)  # ...set the user's admin status
        set_allreports(session, allreportscheck)  # ...set the user's allreports status


# Check if the user exists in the database
def check_user(username: str) -> User:
    user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
    return user


# Set the user's email address
def set_email(user: User, session: SessionMixin) -> None:
    user.emailaddress = session['email']
    db.session.commit()


# Set the last login time for the user
def set_last_login(user: User) -> None:
    user.last_login = datetime.now()  # Set the last login time to the current time
    db.session.commit()  # Commit the changes


# Add the user to the database
def add_user(session: SessionMixin, admincheck: bool, allreportscheck: bool, user_data: dict) -> None:
    user: User = User(  # Create the user object
        username=session['username'],
        displayname=session['display_name'],
        instcode=user_data['University'],
        emailaddress=session['email'],
        admin=admincheck,
        allreports=allreportscheck,
        last_login=datetime.now()
    )
    db.session.add(user)  # Add the user to the database
    db.session.commit()  # Commit the changes


# Set the user's admin status based on the database
def set_admin(session: SessionMixin, admincheck: bool) -> None:
    if admincheck is True:  # Check if the user is an admin
        session['authorizations'].append('admin')  # If they are, add the admin authorization to the session


# Set the user's allreport status based on the database
def set_allreports(session: SessionMixin, allreportscheck: bool) -> None:
    if allreportscheck is True:  # Check if the user is an admin
        session['authorizations'].append('allreports')  # If they are, add the admin authorization to the session


# Check if the username is in the admin list
def admincheck_user(session: SessionMixin, user=None) -> bool:
    admincheck: bool = False  # set admincheck to False to start
    admin: list = current_app.config['ADMINS']  # get config list of admins
    if user:  # If user object present...
        if user.admin:  # ...and admin true...
            admincheck = True  # ...set admincheck true
        elif session['username'] in admin:
            admincheck = True
    elif session['username'] in admin:  # If the username in admin list
        admincheck = True  # ...set admincheck to True

    return admincheck


# Check if the username is in the allreports list
def allreportscheck_user(session: SessionMixin, user: User = None) -> bool:
    allreportscheck: bool = False  # set allreportscheck to False to start
    allreports: list = current_app.config['ALLREPORTS']
    if user:  # If user object is present...
        if user.allreports:  # ...and user.allreports true...
            allreportscheck = True  # ...set allreports true
        elif session['username'] in allreports:
            allreportscheck = True
    elif session['username'] in allreports:  # If username in allreports list...
        allreportscheck = True  # ...set admincheck to True

    return allreportscheck
