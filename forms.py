from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class InstitutionForm(FlaskForm):
    code = StringField('code', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    fulfillment_code = StringField('fulfillment_code', validators=[DataRequired()])
    partner_code = StringField('partner_code', validators=[DataRequired()])
    key = StringField('key', validators=[DataRequired()])
    exceptions = StringField('exceptions', validators=[DataRequired()])
    ext_requests_in_transit = StringField('ext_requests_in_transit', validators=[DataRequired()])
    in_transit_data = StringField('in_transit_data', validators=[DataRequired()])
