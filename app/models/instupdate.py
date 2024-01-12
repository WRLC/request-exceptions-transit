from app.extensions import db
from app.models.institution import Institution


# Institution Update class
class InstUpdate(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    last_update = db.Column(db.DateTime, nullable=False)

    # Constructor
    def __repr__(self):
        return '<InstUpdate %r>' % self.id
