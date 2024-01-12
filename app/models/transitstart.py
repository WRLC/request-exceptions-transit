from app.extensions import db
from app.models.institution import Institution


# Transit Start class
class TransitStart(db.Model):
    event_id = db.Column(db.BigInteger, primary_key=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    request_id = db.Column(db.String(255), nullable=False)
    transit_date = db.Column(db.DateTime, nullable=False)

    # Constructor
    def __repr__(self):
        return '<InTransitData %r>' % self.event_id
