from app.extensions import db
from app.models.user import User


class StatusUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    user = db.Column(db.ForeignKey(User.id), nullable=False)
    __table_args__ = (
        db.UniqueConstraint('status', 'user', name='_status_user_uc'),
    )

    # Constructor
    def __repr__(self):
        return '<StatusUser %r>' % self.id
