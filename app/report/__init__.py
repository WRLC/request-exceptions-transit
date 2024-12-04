""" The report package is responsible for generating reports for the user. """
from flask import Blueprint

bp = Blueprint('report', __name__)

from app.report import routes  # pylint: disable=wrong-import-position
