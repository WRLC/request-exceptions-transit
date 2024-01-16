from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from app.extensions import db
from app.models.institution import Institution


# Institution form class
class InstitutionForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    fulfillment_code = StringField('Fulfillment Code', validators=[DataRequired()])
    partner_code = StringField('Partner Code', validators=[DataRequired()])
    key = StringField('API Key')
    exceptions = StringField('Exceptions Path')
    ext_requests_in_transit = StringField('External Requests in Transit Path')
    in_transit_data = StringField('In Transit Data Path')

    # Add institution form submit
    @staticmethod
    def add_institution_form_submit(form):
        institution = Institution(  # Build institution object from form data
            code=form.code.data, name=form.name.data, fulfillment_code=form.fulfillment_code.data,
            partner_code=form.partner_code.data, key=form.key.data, exceptions=form.exceptions.data,
            ext_requests_in_transit=form.ext_requests_in_transit.data, in_transit_data=form.in_transit_data.data
        )
        db.session.add(institution)  # Add institution to database
        db.session.commit()  # Commit changes to database
