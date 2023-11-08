from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired
from wtforms.widgets import ListWidget, CheckboxInput
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import aliased
from settings import admins
from datetime import datetime

db = SQLAlchemy()  # Create a database object


##################
# Object Classes #
##################

# Institution class
class Institution(db.Model):
    code = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    fulfillment_code = db.Column(db.String(255), nullable=False, unique=True)
    partner_code = db.Column(db.String(255), nullable=False, unique=True)
    key = db.Column(db.String(255), nullable=True)
    exceptions = db.Column(db.String(255), nullable=True)
    ext_requests_in_transit = db.Column(db.String(255), nullable=True)
    in_transit_data = db.Column(db.String(255), nullable=True)

    # Constructor
    def __repr__(self):
        return '<Institution %r>' % self.code

    # Get institution's last update datetime
    def get_last_update(self):
        updated = db.session.execute(
            db.select(
                InstUpdate
            ).filter(
                InstUpdate.instcode == self.code
            ).order_by(
                InstUpdate.last_update.desc()
            )
        ).first()

        return updated

    # Get all current RequestExceptions statuses for the institution
    def get_statuses(self):
        statuses = db.session.execute(
            db.select(
                RequestException.borreqstat
            ).filter(
                RequestException.instcode == self.code
            ).group_by(
                RequestException.borreqstat
            ).order_by(
                RequestException.borreqstat
            )
        ).mappings().all()
        return statuses

    # Get all current RequestExceptions for the institution by status
    def get_exceptions_by_status(self, status):
        ib = aliased(Institution)
        il = aliased(Institution)
        requests = db.session.execute(
            db.select(
                RequestException.borreqstat, RequestException.internalid, RequestException.borcreate,
                RequestException.title, RequestException.author, RequestException.networknum,
                RequestException.partnerstat, RequestException.reqsend, RequestException.days,
                RequestException.requestor, RequestException.partnername, RequestException.partnercode,
                ExternalRequestInTransit.request_id, TransitStart.transit_date
            ).join(
                ib, RequestException.instcode == ib.code
            ).outerjoin(
                il, RequestException.partnercode == il.partner_code
            ).outerjoin(
                ExternalRequestInTransit, (ExternalRequestInTransit.title == RequestException.title) &
                                          (ExternalRequestInTransit.external_id == ib.fulfillment_code) &
                                          (ExternalRequestInTransit.instcode == il.code)
            ).outerjoin(
                TransitStart, ExternalRequestInTransit.request_id == TransitStart.request_id
            ).filter(
                RequestException.instcode == self.code,
                RequestException.borreqstat == status
            ).order_by(
                RequestException.borreqstat, RequestException.internalid.desc(), RequestException.borcreate.desc(),
                RequestException.reqsend.desc()
            )
        ).mappings().all()
        return requests

    # Get all current RequestExceptions for all institutions
    def get_all_requests(self):
        ib = aliased(Institution)
        il = aliased(Institution)
        requests = db.session.execute(
            db.select(
                RequestException.borreqstat.label('Borrowing Request Status'),
                RequestException.internalid.label('Internal ID'),
                RequestException.borcreate.label('Borrowing Request Date'),
                RequestException.title.label('Title'),
                RequestException.author.label('Author'),
                RequestException.networknum.label('Network Number'),
                RequestException.partnerstat.label('Partner Active Status'),
                RequestException.reqsend.label('Request Sending Date'),
                RequestException.days.label('Days Since Request'),
                RequestException.requestor.label('Requestor'),
                RequestException.partnername.label('Partner Name'),
                RequestException.partnercode.label('Partner Code'),
                ExternalRequestInTransit.request_id.label('In Transit?'),
                TransitStart.transit_date.label('In Transit Start')
            ).join(
                ib, RequestException.instcode == ib.code
            ).outerjoin(
                il, RequestException.partnercode == il.partner_code
            ).outerjoin(
                ExternalRequestInTransit, (ExternalRequestInTransit.title == RequestException.title) &
                                          (ExternalRequestInTransit.external_id == ib.fulfillment_code) &
                                          (ExternalRequestInTransit.instcode == il.code)
            ).outerjoin(
                TransitStart, ExternalRequestInTransit.request_id == TransitStart.request_id
            ).filter(
                RequestException.instcode == self.code,
            ).order_by(
                RequestException.borreqstat, RequestException.internalid.desc(), RequestException.borcreate.desc(),
                RequestException.reqsend.desc()
            )
        ).mappings().all()

        requests_dict = [dict(row) for row in requests]

        columns = ['Borrowing Request Status', 'Internal ID', 'Borrowing Request Date', 'Title', 'Author',
                   'Network Number',
                   'Requestor', 'Partner Active Status', 'Request Sending Date', 'Days Since Request', 'Partner Name',
                   'Partner Code', 'In Transit?', 'In Transit Start']

        parsed_requests = []  # List to hold parsed requests

        for request in requests_dict:  # Parse requests
            if request['In Transit?'] is None:  # If the request is not in transit
                request['In Transit?'] = 'N'  # Set the value to 'N'
            else:  # If the request is in transit
                request['In Transit?'] = 'Y'  # Set the value to 'Y'
            ordered_request = {k: request[k] for k in columns}  # Create a dictionary of the request
            parsed_requests.append(ordered_request)  # Add the parsed request to the list

        return parsed_requests  # Return the list of parsed requests


# Institution form class
class InstitutionForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    fulfillment_code = StringField('Fulfillment Code', validators=[DataRequired()])
    partner_code = StringField('Partner Code', validators=[DataRequired()])
    key = StringField('API Key')
    exceptions = StringField('Exceptions Path')
    ext_requests_in_transit = StringField('External Requests in Transit Path')
    in_transit_data = StringField('In Transit Data Path')


# Request Exception class
class RequestException(db.Model):
    exception_id = db.Column(db.BigInteger, primary_key=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    borreqstat = db.Column(db.String(255), nullable=True)
    internalid = db.Column(db.String(255), nullable=True)
    borcreate = db.Column(db.Date, nullable=True)
    title = db.Column(db.String(510), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    networknum = db.Column(db.String(255), nullable=True)
    isbn = db.Column(db.String(255), nullable=True)
    issn = db.Column(db.String(255), nullable=True)
    requestor = db.Column(db.String(255), nullable=True)
    partnerstat = db.Column(db.String(255), nullable=True)
    reqsend = db.Column(db.DateTime, nullable=True)
    days = db.Column(db.Integer, nullable=True)
    partnername = db.Column(db.String(255), nullable=True)
    partnercode = db.Column(db.String(255), nullable=True)

    # Constructor
    def __repr__(self):
        return '<RequestException %r>' % self.exception_id


# External Request in Transit class
class ExternalRequestInTransit(db.Model):
    request_id = db.Column(db.BigInteger, primary_key=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    external_id = db.Column(db.String(255), nullable=False)
    requestor = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(510), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    barcode = db.Column(db.String(255), nullable=True)
    physical_item_id = db.Column(db.String(255), nullable=True)
    isbn = db.Column(db.String(255), nullable=True)
    issn = db.Column(db.String(255), nullable=True)

    # Constructor
    def __repr__(self):
        return '<ExternalRequestInTransit %r>' % self.request_id


# Transit Start class
class TransitStart(db.Model):
    event_id = db.Column(db.BigInteger, primary_key=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    request_id = db.Column(db.String(255), nullable=False)
    transit_date = db.Column(db.DateTime, nullable=False)

    # Constructor
    def __repr__(self):
        return '<InTransitData %r>' % self.event_id


# Institution Update class
class InstUpdate(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    last_update = db.Column(db.DateTime, nullable=False)
    
    # Constructor
    def __repr__(self):
        return '<InstUpdate %r>' % self.id
    

# User class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    displayname = db.Column(db.String(255), nullable=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    emailaddress = db.Column(db.String(255), nullable=True)
    admin = db.Column(db.Boolean, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Constructor
    def __repr__(self):
        return '<User %r>' % self.username


# User Day class
class UserDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey(User.id))
    day = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('user', 'day', name='_user_day_uc'),
    )

    # Constructor
    def __repr__(self):
        return '<UserDay %r>' % self.id


# User Settings form class
class UserSettingsForm(FlaskForm):
    sunday = BooleanField('Sunday', widget=CheckboxInput())
    monday = BooleanField('Monday', widget=CheckboxInput())
    tuesday = BooleanField('Tuesday', widget=CheckboxInput())
    wednesday = BooleanField('Wednesday', widget=CheckboxInput())
    thursday = BooleanField('Thursday', widget=CheckboxInput())
    friday = BooleanField('Friday', widget=CheckboxInput())
    saturday = BooleanField('Saturday', widget=CheckboxInput())


####################
# Helper Functions #
####################

# Add institution form submit
def add_institution_form_submit(form):
    institution = Institution(  # Build institution object from form data
        code=form.code.data, name=form.name.data, fulfillment_code=form.fulfillment_code.data,
        partner_code=form.partner_code.data, key=form.key.data, exceptions=form.exceptions.data,
        ext_requests_in_transit=form.ext_requests_in_transit.data, in_transit_data=form.in_transit_data.data
    )
    db.session.add(institution)  # Add institution to database
    db.session.commit()  # Commit changes to database


# Get all institutions
def get_all_institutions():
    institutions = db.session.execute(db.select(Institution).order_by(Institution.name)).scalars()
    return institutions


# Log the user in
def user_login(session, user_data):

    # Set the session variables
    session['username'] = user_data['primary_id']  # Set the username
    session['user_home'] = user_data['inst']  # Set the user's home institution
    session['display_name'] = user_data['full_name']  # Set the user's display name
    session['authorizations'] = user_data['authorizations']  # Set the user's authorizations
    session['email'] = user_data['email']  # Set the user's email

    user = check_user(session['username'])  # Check if the user exists in the database

    # If the user is in the database...
    if user is not None:
        set_email(user, session)  # ...set the user's email address
        set_user_admin(user, session)  # ...set the user's admin status
        if 'exceptions' in session['authorizations']:
            set_last_login(user)  # ...set the last login time for the user

    # If the user isn't in the database...
    else:
        admincheck = admincheck_user(session)  # ...check if the user is an admin
        add_user(session, admincheck)  # ...add the user to the database


# Check if the user exists in the database
def check_user(username):
    user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
    return user


# Set the user's email address
def set_email(user, session):
    user.emailaddress = session['email']
    db.session.commit()


# Set the last login time for the user
def set_last_login(user):
    user.last_login = datetime.now()  # Set the last login time to the current time
    db.session.commit()  # Commit the changes


# Set the user's admin status based on the database
def set_user_admin(user, session):
    if user.admin is True:  # Check if the user is an admin
        if 'exceptions' not in session['authorizations']:
            session['authorizations'].append('exceptions')  # If they are, add the admin authorization to the session
        session['authorizations'].append('admin')  # If they are, add the admin authorization to the session


# Check if the username is in the admin list
def admincheck_user(session):
    if session['username'] in admins:  # Check if the user is an admin
        admincheck = True  # If they are, set admincheck to True
    else:
        admincheck = False  # If they are not, set admincheck to False

    return admincheck


# Add the user to the database
def add_user(session, admincheck):

    # Create the user object
    user = User(
        username=session['username'],
        displayname=session['display_name'],
        instcode=session['user_home'],
        emailaddress=session['email'],
        admin=admincheck,
        last_login=datetime.now()
    )
    db.session.add(user)  # Add the user to the database
    db.session.commit()  # Commit the changes


# Get all last updated times for institutions
def get_all_last_updates():
    updates = db.session.execute(
        db.select(
            InstUpdate.instcode, db.func.max(InstUpdate.last_update).label('last_update')
        ).group_by(InstUpdate.instcode)
    ).all()

    return updates
