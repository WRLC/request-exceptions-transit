import sqlalchemy as sa
from utils import db


##################
# Object Classes #
##################

# Institution class
class Institution(db.Model):
    code = sa.Column(sa.String(255), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    fulfillment_code = sa.Column(sa.String(255), nullable=False, unique=True)
    partner_code = sa.Column(sa.String(255), nullable=False, unique=True)
    key = sa.Column(sa.String(255), nullable=True)
    exceptions = sa.Column(sa.String(255), nullable=True)
    ext_requests_in_transit = sa.Column(sa.String(255), nullable=True)
    in_transit_data = sa.Column(sa.String(255), nullable=True)

    def __int__(self, code, name, fulfillment_code, partner_code, key, exceptions, ext_requests_in_transit,
                in_transit_data):
        self.code = code
        self.name = name
        self.fulfillment_code = fulfillment_code
        self.partner_code = partner_code
        self.key = key
        self.exceptions = exceptions
        self.ext_requests_in_transit = ext_requests_in_transit
        self.in_transit_data = in_transit_data


# Exception class
class RequestException(db.Model):
    exception_id = sa.Column(sa.BigInteger, primary_key=True)
    fulfillmentreqid = sa.Column(sa.String(255), nullable=True)
    requestorid = sa.Column(sa.String(255), nullable=True)
    borreqstat = sa.Column(sa.String(255), nullable=True)
    internalid = sa.Column(sa.String(255), nullable=True)
    borcreate = sa.Column(sa.Date, nullable=True)
    title = sa.Column(sa.String(510), nullable=True)
    author = sa.Column(sa.String(255), nullable=True)
    networknum = sa.Column(sa.String(255), nullable=True)
    partnerstat = sa.Column(sa.String(255), nullable=True)
    reqsend = sa.Column(sa.DateTime, nullable=True)
    days = sa.Column(sa.Integer, nullable=True)
    requestor = sa.Column(sa.String(255), nullable=True)
    partnercode = sa.Column(sa.ForeignKey(Institution.partner_code))
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(
        self, fulfillmentreqid, requestorid, borreqstat, internalid, borcreate, title, author, networknum, partnerstat,
        reqsend, days, requestor, partnercode, instcode
    ):
        self.fulfillmentreqid = fulfillmentreqid
        self.requestorid = requestorid
        self.borreqstat = borreqstat
        self.internalid = internalid
        self.borcreate = borcreate
        self.title = title
        self.author = author
        self.networknum = networknum
        self.partnerstat = partnerstat
        self.reqsend = reqsend
        self.days = days
        self.requestor = requestor
        self.partnercode = partnercode
        self.instcode = instcode


# External request in transit class
class ExternalRequestInTransit(db.Model):
    request_id = sa.Column(sa.BigInteger, primary_key=True)
    external_id = sa.Column(sa.ForeignKey(Institution.fulfillment_code), nullable=False)
    requestor_id = sa.Column(sa.String(255), nullable=False)
    title = sa.Column(sa.String(510), nullable=False)
    author = sa.Column(sa.String(255), nullable=True)
    barcode = sa.Column(sa.String(255), nullable=True)
    item_id = sa.Column(sa.String(255), nullable=True, index=True)
    isbn = sa.Column(sa.String(255), nullable=True)
    issn = sa.Column(sa.String(255), nullable=True)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, external_id, requestor_id, title, author, barcode, item_id, isbn, issn, instcode):
        self.external_id = external_id
        self.requestor_id = requestor_id
        self.title = title
        self.author = author
        self.barcode = barcode
        self.item_id = item_id
        self.isbn = isbn
        self.issn = issn
        self.instcode = instcode


# In transit data class
class InTransitData(db.Model):
    event_id = sa.Column(sa.BigInteger, primary_key=True)
    item_id = sa.Column(sa.ForeignKey(ExternalRequestInTransit.item_id))
    transit_date = sa.Column(sa.DateTime, nullable=False)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, item_id, transit_date, instcode):
        self.item_id = item_id
        self.transit_date = transit_date
        self.instcode = instcode
