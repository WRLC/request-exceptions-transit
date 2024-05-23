from app.extensions import db


# Institution class
class Institution(db.Model):
    code = db.Column(db.String(255), primary_key=True)
    inst_code = db.Column(db.String(255), nullable=False, unique=True)
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

    # Get the institution code
    @staticmethod
    def get_inst_code(inst_code):
        inst = db.session.execute(
            db.select(
                Institution
            ).filter(
                Institution.inst_code == inst_code
            )
        ).scalar_one_or_none()
        return inst.code
