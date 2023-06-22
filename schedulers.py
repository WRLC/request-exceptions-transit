import requests
from models import db, get_all_institutions, RequestException, ExternalRequestInTransit, TransitStart
from bs4 import BeautifulSoup


def update_reports():
    institutions = get_all_institutions()  # Get all institutions

    for institution in institutions:  # loop through institutions

        ##############
        # Exceptions #
        ##############

        # Delete existing data for the institution
        delete_rows(RequestException, institution.code)

        # Get updated report for the institution
        updated_exc = api_call('exceptions', institution)  # Make the API call

        # map columns to database columns
        mapped_exc = map_columns(updated_exc)  # dictionary to map column names to column numbers

        exceptions = updated_exc.find_all('Row')  # Get rows from the BeautifulSoup object

        for row in exceptions:  # loop through rows
            exception = RequestException(  # create a RequestException object
                instcode=institution.code,
                borreqstat=set_value(row, mapped_exc, 'Borrowing Request Status'),
                internalid=set_value(row, mapped_exc, 'Internal Id'),
                borcreate=set_value(row, mapped_exc, 'Borrowing Creation Date'),
                title=set_value(row, mapped_exc, 'Title'),
                author=set_value(row, mapped_exc, 'Author'),
                networknum=set_value(row, mapped_exc, 'Network Number'),
                isbn=set_value(row, mapped_exc, 'ISBN (Normalized)'),
                issn=set_value(row, mapped_exc, 'ISSN (Normalized)'),
                requestor=set_value(row, mapped_exc, 'Full Name'),
                partnerstat=set_value(row, mapped_exc, 'Partner Active Status'),
                reqsend=set_value(row, mapped_exc, 'Request Sending Date'),
                days=set_value(row, mapped_exc, ' TIMESTAMPDIFF( SQL_TSI_DAY , Request Sending Date,  CURRENT_DATE )'),
                partnername=set_value(row, mapped_exc, 'Partner Name'),
                partnercode=set_value(row, mapped_exc, 'Partner Code'),
            )
            db.session.add(exception)  # Add the exception to the database
            db.session.commit()  # Commit the exception to the database

        ################################
        # External Requests in Transit #
        ################################

        # Get existing data for the institution
        existing_ext = db.session.execute(db.select(ExternalRequestInTransit)
                                          .filter_by(instcode=institution.code)).scalars()

        updated_ext = api_call('ext_requests_in_transit', institution)  # Get updated data for the institution
        mapped_ext = map_columns(updated_ext)  # Map columns to database columns
        ext_requests = updated_ext.find_all('Row')  # Get rows from the BeautifulSoup object
        updated_req_ids = []  # Create empty list to hold updated request ids

        for request in ext_requests:  # loop through rows
            ext_req = ExternalRequestInTransit(  # Create a RequestException object
                request_id=set_value(request, mapped_ext, 'Request Id'),
                instcode=institution.code,
                external_id=set_value(request, mapped_ext, 'External Id'),
                requestor=set_value(request, mapped_ext, 'Full Name'),
                title=set_value(request, mapped_ext, 'Title'),
                author=set_value(request, mapped_ext, 'Author'),
                barcode=set_value(request, mapped_ext, 'Barcode'),
                physical_item_id=set_value(request, mapped_ext, 'Physical Item Id'),
                isbn=set_value(request, mapped_ext, 'ISBN (Normalized)'),
                issn=set_value(request, mapped_ext, 'ISSN (Normalized)'),
            )
            updated_req_ids.append(ext_req.request_id)  # Add the request id to the list

            # Check if the updated request id already exists in the database
            ext_test = db.session.execute(db.select(ExternalRequestInTransit.request_id)
                                          .filter_by(request_id=ext_req.request_id)).scalar_one_or_none()

            if ext_test is not None:  # If the updated request id already exists in the database
                db.session.merge(ext_req)  # Update the external request in transit in the database
                db.session.commit()
            else:  # If the updated request id does not exist in the database
                db.session.add(ext_req)  # Add the external request in transit to the database
                db.session.commit()

        # Delete old data from the database
        for request in existing_ext:  # loop through existing external requests in transit
            if str(request.request_id) not in updated_req_ids:  # If the existing request id is not in the updated list
                db.session.delete(request)  # Delete the external request in transit from the database
                db.session.commit()

        #################
        # Transit Start #
        #################

        # Get existing data for the institution
        existing_transit = db.session.execute(db.select(TransitStart)
                                              .filter_by(instcode=institution.code)).scalars()

        updated_transit = api_call('in_transit_data', institution)  # Get updated data for the institution
        mapped_transit = map_columns(updated_transit)  # Map columns to database columns
        transit_data = updated_transit.find_all('Row')  # Get rows from the BeautifulSoup object
        updated_event_ids = []  # Create empty list to hold updated event ids

        for event in transit_data:
            transit_event = TransitStart(  # Create a TransitStart object
                event_id=set_value(event, mapped_transit, 'Event id'),
                instcode=institution.code,
                request_id=set_value(event, mapped_transit, 'Request id'),
                transit_date=set_value(event, mapped_transit, 'Event Start Date and Time'),
            )
            updated_event_ids.append(transit_event.event_id)  # Add the event id to the list

            # Check if the updated event id already exists in the database
            transit_test = db.session.execute(db.select(TransitStart.event_id)
                                              .filter_by(event_id=transit_event.event_id)).scalar_one_or_none()

            if transit_test is not None:  # If the updated event id already exists in the database
                db.session.merge(transit_event)  # Update the transit start in the database
                db.session.commit()
            else:  # If the updated event id does not exist in the database
                db.session.add(transit_event)  # Add the transit start to the database
                db.session.commit()

        # Delete old data from the database
        for event in existing_transit:  # loop through existing transit starts
            if str(event.event_id) not in updated_event_ids:  # If the existing event id is not in the updated list
                db.session.delete(event)  # Delete the transit start from the database
                db.session.commit()


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


def map_columns(soup):
    columns = soup.find_all('xsd:element')  # Get columns from the BeautifulSoup object
    mapped = {}  # dictionary to map column names to database columns
    for column in columns:  # loop through columns
        mapped[column['saw-sql:columnHeading']] = column['name']  # map column names to database columns

    return mapped
