from app.extensions import db
from app.models.institution import Institution


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
