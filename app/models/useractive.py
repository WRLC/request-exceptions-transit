from app.extensions import db
from app.models.user import User


# User Active class
class UserActive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey(User.id), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('user', 'active', name='_user_active_uc'),
    )

    # Constructor
    def __repr__(self):
        return '<UserActive %r>' % self.id
