from app.extensions import db
from app.models.user import User


# User Day class
class UserDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey(User.id), nullable=False)
    day = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('user', 'day', name='_user_day_uc'),
    )

    # Constructor
    def __repr__(self):
        return '<UserDay %r>' % self.id
