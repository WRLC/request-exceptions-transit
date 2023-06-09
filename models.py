from utils import db


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

    def __repr__(self):
        return '<Institution %r>' % self.code


# Request Exception class
class RequestException(db.Model):
    exception_id = db.Column(db.BigInteger, primary_key=True)
    fulfillmentreqid = db.Column(db.String(255), nullable=True)
    requestorid = db.Column(db.String(255), nullable=True)
    borreqstat = db.Column(db.String(255), nullable=True)
    internalid = db.Column(db.String(255), nullable=True)
    borcreate = db.Column(db.Date, nullable=True)
    title = db.Column(db.String(510), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    networknum = db.Column(db.String(255), nullable=True)
    partnerstat = db.Column(db.String(255), nullable=True)
    reqsend = db.Column(db.DateTime, nullable=True)
    days = db.Column(db.Integer, nullable=True)
    requestor = db.Column(db.String(255), nullable=True)
    partnercode = db.Column(db.ForeignKey(Institution.partner_code))
    instcode = db.Column(db.ForeignKey(Institution.code))

    def __repr__(self):
        return '<RequestException %r>' % self.exception_id


# External Request in Transit class
class ExternalRequestInTransit(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    request_id = db.Column(db.BigInteger, nullable=False, index=True)
    external_id = db.Column(db.ForeignKey(Institution.fulfillment_code), nullable=False)
    requestor = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(510), nullable=False)
    author = db.Column(db.String(255), nullable=True)
    isbn = db.Column(db.String(255), nullable=True)
    issn = db.Column(db.String(255), nullable=True)
    instcode = db.Column(db.ForeignKey(Institution.code))

    def __repr__(self):
        return '<ExternalRequestInTransit %r>' % self.request_id


# Transit Start class
class TransitStart(db.Model):
    event_id = db.Column(db.BigInteger, primary_key=True)
    request_id = db.Column(db.ForeignKey(ExternalRequestInTransit.request_id))
    transit_date = db.Column(db.DateTime, nullable=False)
    instcode = db.Column(db.ForeignKey(Institution.code))

    def __repr__(self):
        return '<InTransitData %r>' % self.event_id
