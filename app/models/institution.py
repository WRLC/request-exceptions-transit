from app.extensions import db


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
