import sys
import requests
from models import get_all_institutions, RequestException
from utils import db
from bs4 import BeautifulSoup


def update_reports():
    print("Updating reports...")
    institutions = get_all_institutions()  # Get all institutions

    for institution in institutions:  # loop through institutions

        ##############
        # Exceptions #
        ##############

        # Delete existing data for the institution
        delete_rows(RequestException, institution.code)

        # Get updated report for the institution
        reptype = 'exceptions'  # Alma Analytics report type
        soup = api_call(reptype, institution)  # Make the API call

        # map columns to database columns
        columns = soup.find_all('xsd:element')  # Get columns from the BeautifulSoup object
        mapped = {}  # dictionary to map column names to database columns
        for column in columns:  # loop through columns
            mapped[column['saw-sql:columnHeading']] = column['name']  # map column names to database columns

        exceptions = soup.find_all('Row')  # Get rows from the BeautifulSoup object
        for row in exceptions:  # loop through rows
            exception = RequestException(  # create a RequestException object
                instcode=institution.code,
                borreqstat=set_value(row, mapped, 'Borrowing Request Status'),
                internalid=set_value(row, mapped, 'Internal Id'),
                borcreate=set_value(row, mapped, 'Borrowing Creation Date'),
                title=set_value(row, mapped, 'Title'),
                author=set_value(row, mapped, 'Author'),
                networknum=set_value(row, mapped, 'Network Number'),
                isbn=set_value(row, mapped, 'ISBN (Normalized)'),
                issn=set_value(row, mapped, 'ISSN (Normalized)'),
                requestor=set_value(row, mapped, 'Full Name'),
                partnerstat=set_value(row, mapped, 'Partner Active Status'),
                reqsend=set_value(row, mapped, 'Request Sending Date'),
                days=set_value(row, mapped, ' TIMESTAMPDIFF( SQL_TSI_DAY , Request Sending Date,  CURRENT_DATE )'),
                partnercode=set_value(row, mapped, 'Partner Code'),
            )
            print(exception.networknum, file=sys.stderr)
            db.session.add(exception)  # Add the exception to the database
            db.session.commit()  # Commit the exception to the database


# Get the value of a column from a row
def set_value(row, mapped, column):
    try:
        value = row.find(mapped[column]).get_text()  # get the column value
    except AttributeError:
        value = None
    return value


# Delete all rows from a table for a given institution
def delete_rows(obtype, instcode):
    objs = obtype.query.filter_by(instcode=instcode).all()
    for obj in objs:
        db.session.delete(obj)
        db.session.commit()


def api_call(reptype, institution):
    api = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/'  # Alma API route
    endpoint = 'analytics/reports?'  # Alma API endpoint
    static_params = 'limit=1000&col_names=true'  # Alma API static parameters
    params = '&path=' + getattr(institution, reptype) + '&apikey=' + institution.key  # Alma API parameters
    path = api + endpoint + static_params + params  # Full Alma API path
    response = requests.request('GET', path).content  # Make the API call
    soup = soupify(response)  # Turn the API response into a BeautifulSoup object
    return soup


def soupify(response):
    soup = BeautifulSoup(response, features="xml")  # Turn the API response into a BeautifulSoup object
    return soup
