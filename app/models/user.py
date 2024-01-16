from app.extensions import db
from app.models.institution import Institution


# User class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    displayname = db.Column(db.String(255), nullable=True)
    instcode = db.Column(db.ForeignKey(Institution.code))
    emailaddress = db.Column(db.String(255), nullable=True)
    admin = db.Column(db.Boolean, nullable=False)
    allreports = db.Column(db.Boolean, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Constructor
    def __repr__(self):
        return '<User %r>' % self.username
