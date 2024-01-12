from app.extensions import db
from app.models.institution import Institution


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
