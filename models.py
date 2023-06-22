from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy

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
        requests = db.session.execute(
            db.select(
                RequestException.borreqstat, RequestException.internalid, RequestException.borcreate,
                RequestException.title, RequestException.author, RequestException.networknum,
                RequestException.partnerstat, RequestException.reqsend, RequestException.days,
                RequestException.requestor, RequestException.partnername, RequestException.partnercode,
                TransitStart.event_id, TransitStart.transit_date
            ).join(
                Institution, RequestException.instcode == Institution.code
            ).outerjoin(
                ExternalRequestInTransit, (RequestException.title == ExternalRequestInTransit.title) &
                                          (RequestException.requestor == ExternalRequestInTransit.requestor) &
                                          (Institution.fulfillment_code == ExternalRequestInTransit.external_id)
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
    request_id = db.Column(db.ForeignKey(ExternalRequestInTransit.request_id))
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
    admin = db.Column(db.Boolean, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Constructor
    def __repr__(self):
        return '<User %r>' % self.username


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
