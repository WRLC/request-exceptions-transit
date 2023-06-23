import requests
from models import db, get_all_institutions, RequestException, ExternalRequestInTransit, TransitStart, InstUpdate
from datetime import datetime
from bs4 import BeautifulSoup
from logging.handlers import TimedRotatingFileHandler
from settings import scheduler_log_dir
import logging

# scheduler log
logdir = scheduler_log_dir
log_file = logdir + 'scheduler.log'
scheduler_log = logging.getLogger('scheduler')  # create the scheduler log
scheduler_log.setLevel(logging.INFO)  # set the scheduler log level
file_handler = TimedRotatingFileHandler(log_file, when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(  # set the file handler format
    logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %H:%M:%S'
    ))
scheduler_log.addHandler(file_handler)  # add the file handler to the scheduler log


def update_reports():
    existing_ext = None  # Initialize variables
    existing_transit = None  # Initialize variables
    institutions = get_all_institutions()  # Get all institutions
    updated = 0  # Set updated to 0

    for institution in institutions:  # loop through institutions
        if institution.code is not None:  # Check if the institution has a code

            # Exceptions
            if institution.exceptions is not None:  # Check if the institution has an exceptions report
                delete_rows(RequestException, institution.code)  # Delete existing data for the institution
                updated_exc = api_call('exceptions', institution)  # Get updated report for the institution
                mapped_exc = map_columns(updated_exc)  # map columns to database columns
                exceptions = updated_exc.find_all('Row')  # Get rows from the BeautifulSoup object
                if exceptions is not None:  # Check if there are any exceptions
                    new_exception_count = 0  # Initialize new exception count
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
                            days=set_value(row, mapped_exc,
                                           ' TIMESTAMPDIFF( SQL_TSI_DAY , Request Sending Date,  CURRENT_DATE )'),
                            partnername=set_value(row, mapped_exc, 'Partner Name'),
                            partnercode=set_value(row, mapped_exc, 'Partner Code'),
                        )
                        try:
                            db.session.add(exception)  # Add the exception to the database
                        except Exception as e:
                            scheduler_log.error(  # Log the error
                                'Exception for {} not added to database: {}'.format(institution.code, e))
                        else:
                            db.session.commit()  # Commit the exception to the database
                            new_exception_count += 1  # Increment new exception count
                    if new_exception_count > 0:  # Check if there were any new exceptions
                        scheduler_log.info(  # Log the number of new exceptions added
                            '{} exceptions added for {}'.format(new_exception_count, institution.code))
                    updated += 1  # Increment updated

            # External Requests in Transit
            if institution.ext_requests_in_transit is not None:
                # Get existing data for the institution
                try:
                    existing_ext = db.session.execute(db.select(ExternalRequestInTransit)
                                                      .filter_by(instcode=institution.code)).scalars()
                except Exception as e:
                    scheduler_log.error(  # Log the error
                        'Existing external requests in transit for {} not retrieved: {}'.format(institution.code, e))

                updated_ext = api_call('ext_requests_in_transit', institution)  # Get updated data for the institution
                mapped_ext = map_columns(updated_ext)  # Map columns to database columns
                ext_requests = updated_ext.find_all('Row')  # Get rows from the BeautifulSoup object
                updated_req_ids = []  # Create empty list to hold updated request ids
                if ext_requests is not None:  # Check if there are any external requests in transit
                    merged_ext_count = 0  # Initialize merged count
                    new_ext_count = 0  # Initialize new count
                    deleted_ext_count = 0  # Initialize deleted count
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

                        ext_test = None  # Initialize variable

                        try:  # Check if the updated request id already exists in the database
                            ext_test = db.session.execute(
                                db.select(ExternalRequestInTransit.request_id)
                                .filter_by(request_id=ext_req.request_id)).scalar_one_or_none()
                        except Exception as e:
                            scheduler_log.error(  # Log the error
                                'External request in transit {} for {} not retrieved: {}'.format(
                                    ext_req.request_id, institution.code, e))

                        if ext_test is not None:  # If the updated request id already exists in the database
                            try:
                                db.session.merge(ext_req)  # Update the external request in transit in the database
                            except Exception as e:
                                scheduler_log.error(  # Log the error
                                    'External request in transit {} for {} not updated: {}'.format(
                                        ext_test.request_id, institution.code, e))
                            else:
                                db.session.commit()
                                merged_ext_count += 1  # Increment merged count
                        else:  # If the updated request id does not exist in the database
                            try:
                                db.session.add(ext_req)  # Add the external request in transit to the database
                            except Exception as e:
                                scheduler_log.error(  # Log the error
                                    'External request in transit {} for {} not added: {}'.format(
                                        ext_req.request_id, institution.code, e))
                            else:
                                db.session.commit()
                                new_ext_count += 1  # Increment new count

                    # Delete old data from the database
                    for request in existing_ext:  # loop through existing external requests in transit
                        if str(request.request_id) not in updated_req_ids:  # If existing request not in updated list
                            try:
                                db.session.delete(request)  # Delete the external request in transit from the database
                            except Exception as e:
                                scheduler_log.error(  # Log the error
                                    'External request in transit {} for {} not deleted: {}'.format(
                                        request.request_id, institution.code, e))
                            else:
                                db.session.commit()
                                deleted_ext_count += 1  # Increment deleted count
                    if merged_ext_count > 0:
                        scheduler_log.info(  # Log the number of merged external requests in transit
                            '{} external requests in transit merged for {}'.format(merged_ext_count, institution.code))
                    if new_ext_count > 0:
                        scheduler_log.info(  # Log the number of new external requests in transit
                            '{} external requests in transit added for {}'.format(new_ext_count, institution.code))
                    if deleted_ext_count > 0:
                        scheduler_log.info(  # Log the number of deleted external requests in transit
                            '{} external requests in transit deleted for {}'.format(
                                deleted_ext_count, institution.code))
                    updated += 1  # Increment updated

            # Transit Start
            if institution.in_transit_data is not None:
                # Get existing data for the institution
                try:
                    existing_transit = db.session.execute(db.select(TransitStart)
                                                          .filter_by(instcode=institution.code)).scalars()
                except Exception as e:
                    scheduler_log.error(  # Log the error
                        'Existing transit start events for {} not retrieved: {}'.format(institution.code, e))

                updated_transit = api_call('in_transit_data', institution)  # Get updated data for the institution
                mapped_transit = map_columns(updated_transit)  # Map columns to database columns
                transit_data = updated_transit.find_all('Row')  # Get rows from the BeautifulSoup object
                updated_event_ids = []  # Create empty list to hold updated event ids
                if transit_data is not None:  # Check if there are any transit events
                    merged_transit_count = 0  # Initialize merged count
                    new_transit_count = 0  # Initialize new count
                    deleted_transit_count = 0  # Initialize deleted count
                    for event in transit_data:
                        transit_event = TransitStart(  # Create a TransitStart object
                            event_id=set_value(event, mapped_transit, 'Event id'),
                            instcode=institution.code,
                            request_id=set_value(event, mapped_transit, 'Request id'),
                            transit_date=set_value(event, mapped_transit, 'Event Start Date and Time'),
                        )
                        updated_event_ids.append(transit_event.event_id)  # Add the event id to the list

                        # Check if the updated event id already exists in the database
                        transit_test = db.session.execute(db.select(TransitStart.event_id).filter_by(
                            event_id=transit_event.event_id)).scalar_one_or_none()

                        if transit_test is not None:  # If the updated event id already exists in the database
                            try:
                                db.session.merge(transit_event)  # Update the transit start in the database
                            except Exception as e:
                                scheduler_log.error(  # Log the error
                                    'Transit start event {} for {} not updated: {}'.format(
                                        transit_test.event_id, institution.code, e))
                            else:
                                db.session.commit()
                                merged_transit_count += 1  # Increment merged count
                        else:  # If the updated event id does not exist in the database
                            try:
                                db.session.add(transit_event)  # Add the transit start to the database
                            except Exception as e:
                                scheduler_log.error(  # Log the error
                                    'Transit start event {} for {} not added: {}'.format(
                                        transit_event.event_id, institution.code, e))
                            else:
                                db.session.commit()
                                new_transit_count += 1  # Increment new count

                    # Delete old data from the database
                    for event in existing_transit:  # loop through existing transit starts
                        if str(event.event_id) not in updated_event_ids:  # If existing event id not in updated list
                            try:
                                db.session.delete(event)  # Delete the transit start from the database
                            except Exception as e:
                                scheduler_log.error(  # Log the error
                                    'Transit start event {} for {} not deleted: {}'.format(
                                        event.event_id, institution.code, e))
                            else:
                                db.session.commit()
                                deleted_transit_count += 1  # Increment deleted count
                    if merged_transit_count > 0:
                        scheduler_log.info(  # Log the number of merged transit starts
                            '{} transit start events merged for {}'.format(merged_transit_count, institution.code))
                    if new_transit_count > 0:
                        scheduler_log.info(  # Log the number of new transit starts
                            '{} transit start events added for {}'.format(new_transit_count, institution.code))
                    if deleted_transit_count > 0:
                        scheduler_log.info(  # Log the number of deleted transit starts
                            '{} transit start events deleted for {}'.format(
                                deleted_transit_count, institution.code))
                    updated += 1  # Increment updated

            # Institution Update
            if updated > 0:
                inst_update = InstUpdate(institution.code, datetime.now())  # Create an InstUpdate object
                try:
                    db.session.add(inst_update)  # add the institution update to the database
                except Exception as e:
                    scheduler_log.error(  # Log the error
                        'Institution update for {} not added: {}'.format(institution.code, e))
                else:
                    db.session.commit()
                    scheduler_log.info(  # Log the institution update
                        '{} updated'.format(institution.code))


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
        try:
            db.session.delete(obj)
        except Exception as e:
            scheduler_log.error(  # Log the error
                '{} {} for {} not deleted: {}'.format(obtype, obj.exception_id, instcode, e))
            continue
        else:
            db.session.commit()


def api_call(reptype, institution):
    api = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/'  # Alma API route
    endpoint = 'analytics/reports?'  # Alma API endpoint
    static_params = 'limit=1000&col_names=true'  # Alma API static parameters
    params = '&path=' + getattr(institution, reptype) + '&apikey=' + institution.key  # Alma API parameters
    path = api + endpoint + static_params + params  # Full Alma API path
    try:
        response = requests.request('GET', path).content  # Make the API call
    except requests.exceptions.RequestException as e:
        scheduler_log.log('ERROR', 'API call failed for ' + institution.code + ' ' + reptype + ' ' + str(e))
        return None
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
