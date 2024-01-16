from app.models.institution import Institution
from app.models.instupdate import InstUpdate
from app.models.requestexception import RequestException
from app.models.externalrequestintransit import ExternalRequestInTransit
from app.models.transitstart import TransitStart
from app.models.userday import UserDay
from app.models.useractive import UserActive
from app.models.statususer import StatusUser
from app.models.user import User
from sqlalchemy.orm import aliased
from app.extensions import db


# Get all institutions
def get_all_institutions():
    institutions = db.session.execute(db.select(Institution).order_by(Institution.name)).scalars()
    return institutions


# Get all current RequestExceptions for an institution
def get_all_requests(institution, repstatuses, partnerstat):
    ib = aliased(Institution)
    il = aliased(Institution)
    requests = db.session.execute(
        db.select(
            RequestException.borreqstat.label('Borrowing Request Status'),
            RequestException.internalid.label('Internal ID'),
            RequestException.borcreate.label('Borrowing Request Date'),
            RequestException.title.label('Title'),
            RequestException.author.label('Author'),
            RequestException.networknum.label('Network Number'),
            RequestException.partnerstat.label('Partner Active Status'),
            RequestException.reqsend.label('Request Sending Date'),
            RequestException.days.label('Days Since Request'),
            RequestException.requestor.label('Requestor'),
            RequestException.partnername.label('Partner Name'),
            RequestException.partnercode.label('Partner Code'),
            ExternalRequestInTransit.request_id.label('In Transit?'),
            TransitStart.transit_date.label('In Transit Start')
        ).join(
            ib, RequestException.instcode == ib.code
        ).outerjoin(
            il, RequestException.partnercode == il.partner_code
        ).outerjoin(
            ExternalRequestInTransit, (ExternalRequestInTransit.title == RequestException.title) &
                                      (ExternalRequestInTransit.external_id == ib.fulfillment_code) &
                                      (ExternalRequestInTransit.instcode == il.code)
        ).outerjoin(
            TransitStart, ExternalRequestInTransit.request_id == TransitStart.request_id
        ).filter(
            RequestException.instcode == institution.code,
            RequestException.borreqstat.in_([status.borreqstat for status in repstatuses]),
            RequestException.partnerstat.in_(partnerstat)
        ).order_by(
            RequestException.borreqstat, RequestException.internalid.desc(), RequestException.borcreate.desc(),
            RequestException.reqsend.desc()
        )
    ).mappings().all()

    requests_dict = [dict(row) for row in requests]

    columns = ['Borrowing Request Status', 'Internal ID', 'Borrowing Request Date', 'Title', 'Author',
               'Network Number',
               'Requestor', 'Partner Active Status', 'Request Sending Date', 'Days Since Request', 'Partner Name',
               'Partner Code', 'In Transit?', 'In Transit Start']

    parsed_requests = []  # List to hold parsed requests

    for request in requests_dict:  # Parse requests
        if request['In Transit?'] is None:  # If the request is not in transit
            request['In Transit?'] = 'N'  # Set the value to 'N'
        else:  # If the request is in transit
            request['In Transit?'] = 'Y'  # Set the value to 'Y'
        ordered_request = {k: request[k] for k in columns}  # Create a dictionary of the request
        parsed_requests.append(ordered_request)  # Add the parsed request to the list

    return parsed_requests  # Return the list of parsed requests


# Get all current RequestExceptions for the institution by status
def get_exceptions_by_status(institution, status, partnerstat):
    ib = aliased(Institution)
    il = aliased(Institution)
    requests = db.session.execute(
        db.select(
            RequestException.borreqstat, RequestException.internalid, RequestException.borcreate,
            RequestException.title, RequestException.author, RequestException.networknum,
            RequestException.partnerstat, RequestException.reqsend, RequestException.days,
            RequestException.requestor, RequestException.partnername, RequestException.partnercode,
            ExternalRequestInTransit.request_id, TransitStart.transit_date
        ).join(
            ib, RequestException.instcode == ib.code
        ).outerjoin(
            il, RequestException.partnercode == il.partner_code
        ).outerjoin(
            ExternalRequestInTransit, (ExternalRequestInTransit.title == RequestException.title) &
                                      (ExternalRequestInTransit.external_id == ib.fulfillment_code) &
                                      (ExternalRequestInTransit.instcode == il.code)
        ).outerjoin(
            TransitStart, ExternalRequestInTransit.request_id == TransitStart.request_id
        ).filter(
            RequestException.instcode == institution.code,
            RequestException.borreqstat == status,
            RequestException.partnerstat.in_(partnerstat)
        ).order_by(
            RequestException.borreqstat, RequestException.internalid.desc(), RequestException.borcreate.desc(),
            RequestException.reqsend.desc()
        )
    ).mappings().all()

    return requests


# Get institution's last update datetime
def get_last_update(instcode):
    updated = db.session.execute(
        db.select(
            InstUpdate
        ).filter(
            InstUpdate.instcode == instcode
        ).order_by(
            InstUpdate.last_update.desc()
        )
    ).first()

    return updated


# Get all last updated times for institutions
def get_all_last_updates():
    updates = db.session.execute(
        db.select(
            InstUpdate.instcode, db.func.max(InstUpdate.last_update).label('last_update')
        ).group_by(InstUpdate.instcode)
    ).all()

    return updates


# Get the request exceptions for an institutions (for XLSX)
def get_exceptions_xlsx(user, institution):
    user = get_user(user.username)  # get the current user from the database
    institution_statuses = get_statuses(institution.code)  # get inst's current exception statuses
    user_statuses = get_user_statuses(user)  # get the user's selected statuses

    # if the user has NOT selected any statuses...
    if len(user_statuses) == 0:
        repstatuses = institution_statuses

    # if the user HAS selected statuses...
    else:
        repstatuses = get_user_selected_statuses(user_statuses, institution_statuses)

    user_partnerstat = get_user_active(user)  # get the user's selected partner status
    partnerstat = get_all_partnerstat()  # get all possible partner statuses
    if user_partnerstat is not None:  # if the user has selected a partner status
        if user_partnerstat.active == 1:  # if the user has selected 'Active Only'
            partnerstat = ['Active']  # set the partner status to 'Active'

    request_exceptions = get_all_requests(institution, repstatuses, partnerstat)  # Get all exceptions

    return request_exceptions  # Return list of exceptions


# Get the request exceptions for an institution
def get_exceptions(session, institution):

    user = get_user(session['username'])  # get the current user from the database
    institution_statuses = get_statuses(institution.code)  # get inst's current exception statuses
    user_statuses = get_user_statuses(user)  # get the user's selected statuses

    # if the user has NOT selected any statuses...
    if len(user_statuses) == 0:
        repstatuses = institution_statuses  # ...use all of the institution's current statuses

    # if the user HAS selected statuses...
    else:
        repstatuses = get_user_selected_statuses(user_statuses, institution_statuses)

    user_partnerstat = get_user_active(user)  # get the user's selected partner status
    partnerstat = get_all_partnerstat()  # get all possible partner statuses
    if user_partnerstat is not None:  # if the user has selected a partner status
        if user_partnerstat.active == 1:  # if the user has selected 'Active Only'
            partnerstat = ['Active']  # set the partner status to 'Active'

    request_exceptions = []  # Create empty list for request exceptions

    for status in repstatuses:  # Loop through the user's SELECTED statuses that are CURRENT for the institution
        exceptions = get_exceptions_by_status(institution, status.borreqstat, partnerstat)  # Get exceptions
        request_exceptions.append(exceptions)  # Add exceptions to list

    return request_exceptions  # Return list of exceptions


# Get all current RequestExceptions statuses for the institution
def get_statuses(instcode):
    reqstatuses = db.session.execute(
        db.select(
            RequestException.borreqstat
        ).filter(
            RequestException.instcode == instcode
        ).group_by(
            RequestException.borreqstat
        ).order_by(
            RequestException.borreqstat
        )
    ).mappings().all()
    return reqstatuses


def get_user_days(user):
    user_days = db.session.execute(db.select(UserDay).filter(UserDay.user == user.id)).scalars().all()
    return user_days


def get_user_active(user):
    user_active = db.session.execute(db.select(UserActive).filter(UserActive.user == user.id)).scalar_one_or_none()
    return user_active


def get_user_statuses(user):
    user_statuses = db.session.execute(db.select(StatusUser).filter(StatusUser.user == user.id)).scalars().all()
    return user_statuses


# Get the user from the database
def get_user(username):
    user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
    return user


def get_user_selected_statuses(user_statuses, institution_statuses):
    # ...get a list of the user's SELECTED status CODES
    userstatuses = []  # create an empty list for the user's selected status codes
    for user_status in user_statuses:  # for each selected status
        userstatuses.append(user_status.status)  # add the status code to the list

    # ...then iterate through the status map to get the user's SELECTED status LABELS
    statuslabels = []  # create an empty list for the statuses to be reported

    statuses = get_all_statuses()  # get all possible statuses
    for status in statuses:  # for each possible status
        if status['code'] in userstatuses:  # if the status code is in the user's selected statuses
            statuslabels.append(status['label'])  # add the status label to the list

    # ...then iterate through INSTITUTION'S CURRENT exception statuses looking for the user's SELECTED statuses
    repstatuses = []
    for institution_status in institution_statuses:
        if institution_status.borreqstat in statuslabels:
            repstatuses.append(institution_status)

    return repstatuses


def get_all_statuses():
    statuses = [
        {'code': 'AUTOMATIC_RENEW', 'label': 'Automatic renew'},
        {'code': 'AUTO_WILL_SUPPLY', 'label': 'Automatic will supply'},
        {'code': 'BAD_CITATION', 'label': 'Bad citation'},
        {'code': 'CANCEL_NOT_ACCEPTED', 'label': 'Cancel request not accepted'},
        {'code': 'CANCELLED', 'label': 'Cancelled by partner'},
        {'code': 'CLAIMED', 'label': 'Claimed'},
        {'code': 'CONDITIONAL', 'label': 'Conditional'},
        {'code': 'REQUEST_CREATED_BOR', 'label': 'Created borrowing request'},
        {'code': 'DAMAGED_COMMUNICATED', 'label': 'Damaged communicated'},
        {'code': 'DECLARED_LOST', 'label': 'Declared lost by partner'},
        {'code': 'RECEIVED_DIGITALLY', 'label': 'Digitally received by library'},
        {'code': 'EXPIRED', 'label': 'Expired'},
        {'code': 'EXTERNALLY_OBTAINED', 'label': 'Externally Obtained'},
        {'code': 'LENDER_CHECK_IN', 'label': 'Lender check in'},
        {'code': 'LOCAL_HOLDING', 'label': 'Local holding'},
        {'code': 'LOCATE_FAILED', 'label': 'Locate failed'},
        {'code': 'LOCATE_IN_PROCESS', 'label': 'Locate in process'},
        {'code': 'LOST_AND_FEE_PAID', 'label': 'Lost and fee paid'},
        {'code': 'LOST_COMMUNICATED', 'label': 'Lost communicated'},
        {'code': 'MANUAL_RENEW', 'label': 'Manual renew'},
        {'code': 'MEDIATED_RENEWAL', 'label': 'Mediated Patron Renewal'},
        {'code': 'OVERDUE_ITEM', 'label': 'Overdue request'},
        {'code': 'PENDING_APPROVAL', 'label': 'Pending Approval'},
        {'code': 'REACTIVATED', 'label': 'Reactivated'},
        {'code': 'READY_TO_SEND', 'label': 'Ready to be sent'},
        {'code': 'RECALLED_BOR', 'label': 'Recalled by partner'},
        {'code': 'REJECT', 'label': 'Reject'},
        {'code': 'RENEW_NOT_ACCEPTED', 'label': 'Renew request not accepted'},
        {'code': 'RENEW_REQUESTED', 'label': 'Renew requested'},
        {'code': 'RENEWED', 'label': 'Renewed by partner'},
        {'code': 'DAMAGED', 'label': 'Reported damaged item to partner'},
        {'code': 'REPORT_LOST', 'label': 'Reported lost item to partner'},
        {'code': 'REQUEST_ACCEPTED', 'label': 'Request accepted'},
        {'code': 'REQUEST_SENT', 'label': 'Request sent to partner'},
        {'code': 'RETURNED_TO_PARTNER', 'label': 'Returned item to partner'},
        {'code': 'SHIPPED_DIGITALLY', 'label': 'Shipped Digitally'},
        {'code': 'SHIPPED_PHYSICALLY', 'label': 'Shipped Physically'},
        {'code': 'CANCEL_REPLY', 'label': 'Waiting for cancel response'},
        {'code': 'RECEIVE_DIGITALLY_REPLY', 'label': 'Waiting for receive digitally'},
        {'code': 'WILL_SUPPLY', 'label': 'Will supply'}
    ]
    return statuses


def get_all_partnerstat():
    partnerstat = ['Active', 'Non Active']
    return partnerstat
