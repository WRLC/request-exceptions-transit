from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms.widgets import CheckboxInput
from app.extensions import db
from app.models.userday import UserDay
from app.models.statususer import StatusUser
from app.models.useractive import UserActive


# User Settings form class
class UserSettingsForm(FlaskForm):
    sunday = BooleanField('Sunday', widget=CheckboxInput())
    monday = BooleanField('Monday', widget=CheckboxInput())
    tuesday = BooleanField('Tuesday', widget=CheckboxInput())
    wednesday = BooleanField('Wednesday', widget=CheckboxInput())
    thursday = BooleanField('Thursday', widget=CheckboxInput())
    friday = BooleanField('Friday', widget=CheckboxInput())
    saturday = BooleanField('Saturday', widget=CheckboxInput())
    active = BooleanField('Show only Active requests', widget=CheckboxInput())
    AUTOMATIC_RENEW = BooleanField('Automatic renew', widget=CheckboxInput())
    AUTO_WILL_SUPPLY = BooleanField('Automatic will supply', widget=CheckboxInput())
    BAD_CITATION = BooleanField('Bad citation', widget=CheckboxInput())
    CANCEL_NOT_ACCEPTED = BooleanField('Cancel request not accepted', widget=CheckboxInput())
    CANCELLED = BooleanField('Cancelled by partner', widget=CheckboxInput())
    CLAIMED = BooleanField('Claimed', widget=CheckboxInput())
    CONDITIONAL = BooleanField('Conditional', widget=CheckboxInput())
    REQUEST_CREATED_BOR = BooleanField('Created borrowing request', widget=CheckboxInput())
    DAMAGED_COMMUNICATED = BooleanField('Damaged communicated', widget=CheckboxInput())
    DECLARED_LOST = BooleanField('Declared lost by partner', widget=CheckboxInput())
    RECEIVED_DIGITALLY = BooleanField('Digitally received by library', widget=CheckboxInput())
    EXPIRED = BooleanField('Expired', widget=CheckboxInput())
    EXTERNALLY_OBTAINED = BooleanField('Externally Obtained', widget=CheckboxInput())
    LENDER_CHECK_IN = BooleanField('Lender check in', widget=CheckboxInput())
    LOCAL_HOLDING = BooleanField('Local holding', widget=CheckboxInput())
    LOCATE_FAILED = BooleanField('Locate failed', widget=CheckboxInput())
    LOCATE_IN_PROCESS = BooleanField('Locate in process', widget=CheckboxInput())
    LOST_AND_FEE_PAID = BooleanField('Lost and fee paid', widget=CheckboxInput())
    LOST_COMMUNICATED = BooleanField('Lost communicated', widget=CheckboxInput())
    MANUAL_RENEW = BooleanField('Manual renew', widget=CheckboxInput())
    MEDIATED_RENEWAL = BooleanField('Mediated Patron Renewal', widget=CheckboxInput())
    OVERDUE_ITEM = BooleanField('Overdue request', widget=CheckboxInput())
    PENDING_APPROVAL = BooleanField('Pending Approval', widget=CheckboxInput())
    REACTIVATED = BooleanField('Reactivated', widget=CheckboxInput())
    READY_TO_SEND = BooleanField('Ready to be sent', widget=CheckboxInput())
    RECALLED_BOR = BooleanField('Recalled by partner', widget=CheckboxInput())
    REJECT = BooleanField('Reject', widget=CheckboxInput())
    RENEW_NOT_ACCEPTED = BooleanField('Renew request not accepted', widget=CheckboxInput())
    RENEW_REQUESTED = BooleanField('Renew requested', widget=CheckboxInput())
    RENEWED = BooleanField('Renewed by partner', widget=CheckboxInput())
    DAMAGED = BooleanField('Reported damaged item to partner', widget=CheckboxInput())
    REPORT_LOST = BooleanField('Reported lost item to partner', widget=CheckboxInput())
    REQUEST_ACCEPTED = BooleanField('Request accepted', widget=CheckboxInput())
    REQUEST_SENT = BooleanField('Request sent to partner', widget=CheckboxInput())
    RETURNED_TO_PARTNER = BooleanField('Returned item to partner', widget=CheckboxInput())
    SHIPPED_DIGITALLY = BooleanField('Shipped Digitally', widget=CheckboxInput())
    SHIPPED_PHYSICALLY = BooleanField('Shipped Physically', widget=CheckboxInput())
    CANCEL_REPLY = BooleanField('Waiting for cancel response', widget=CheckboxInput())
    RECEIVE_DIGITALLY_REPLY = BooleanField('Waiting for receive digitally', widget=CheckboxInput())
    WILL_SUPPLY = BooleanField('Will supply', widget=CheckboxInput())

    # Update user settings
    @staticmethod
    def update_user_settings(form, user):
        db.session.execute(db.delete(UserDay).where(UserDay.user == user.id))  # delete all the user's days
        days = [
            (0, form.data['sunday']),
            (1, form.data['monday']),
            (2, form.data['tuesday']),
            (3, form.data['wednesday']),
            (4, form.data['thursday']),
            (5, form.data['friday']),
            (6, form.data['saturday']),
        ]
        for day in days:  # for each day
            if day[1] is True:
                user_day = UserDay(user=user.id, day=day[0])  # create a new user day
                db.session.add(user_day)  # add the user day to the database

        db.session.execute(db.delete(UserActive).where(UserActive.user == user.id))  # delete the user's active pref
        if form.data['active'] is True:
            user_active = UserActive(user=user.id, active=True)
            db.session.add(user_active)  # add the user active to the database

        db.session.execute(db.delete(StatusUser).where(StatusUser.user == user.id))  # delete all the user's statuses
        reqstatuses = [
            ('AUTOMATIC_RENEW', form.data['AUTOMATIC_RENEW']),
            ('AUTO_WILL_SUPPLY', form.data['AUTO_WILL_SUPPLY']),
            ('BAD_CITATION', form.data['BAD_CITATION']),
            ('CANCEL_NOT_ACCEPTED', form.data['CANCEL_NOT_ACCEPTED']),
            ('CANCELLED', form.data['CANCELLED']),
            ('CLAIMED', form.data['CLAIMED']),
            ('CONDITIONAL', form.data['CONDITIONAL']),
            ('REQUEST_CREATED_BOR', form.data['REQUEST_CREATED_BOR']),
            ('DAMAGED_COMMUNICATED', form.data['DAMAGED_COMMUNICATED']),
            ('DECLARED_LOST', form.data['DECLARED_LOST']),
            ('RECEIVED_DIGITALLY', form.data['RECEIVED_DIGITALLY']),
            ('EXPIRED', form.data['EXPIRED']),
            ('EXTERNALLY_OBTAINED', form.data['EXTERNALLY_OBTAINED']),
            ('LENDER_CHECK_IN', form.data['LENDER_CHECK_IN']),
            ('LOCAL_HOLDING', form.data['LOCAL_HOLDING']),
            ('LOCATE_FAILED', form.data['LOCATE_FAILED']),
            ('LOCATE_IN_PROCESS', form.data['LOCATE_IN_PROCESS']),
            ('LOST_AND_FEE_PAID', form.data['LOST_AND_FEE_PAID']),
            ('LOST_COMMUNICATED', form.data['LOST_COMMUNICATED']),
            ('MANUAL_RENEW', form.data['MANUAL_RENEW']),
            ('MEDIATED_RENEWAL', form.data['MEDIATED_RENEWAL']),
            ('OVERDUE_ITEM', form.data['OVERDUE_ITEM']),
            ('PENDING_APPROVAL', form.data['PENDING_APPROVAL']),
            ('REACTIVATED', form.data['REACTIVATED']),
            ('READY_TO_SEND', form.data['READY_TO_SEND']),
            ('RECALLED_BOR', form.data['RECALLED_BOR']),
            ('REJECT', form.data['REJECT']),
            ('RENEW_NOT_ACCEPTED', form.data['RENEW_NOT_ACCEPTED']),
            ('RENEW_REQUESTED', form.data['RENEW_REQUESTED']),
            ('RENEWED', form.data['RENEWED']),
            ('DAMAGED', form.data['DAMAGED']),
            ('REPORT_LOST', form.data['REPORT_LOST']),
            ('REQUEST_ACCEPTED', form.data['REQUEST_ACCEPTED']),
            ('REQUEST_SENT', form.data['REQUEST_SENT']),
            ('RETURNED_TO_PARTNER', form.data['RETURNED_TO_PARTNER']),
            ('SHIPPED_DIGITALLY', form.data['SHIPPED_DIGITALLY']),
            ('SHIPPED_PHYSICALLY', form.data['SHIPPED_PHYSICALLY']),
            ('CANCEL_REPLY', form.data['CANCEL_REPLY']),
            ('RECEIVE_DIGITALLY_REPLY', form.data['RECEIVE_DIGITALLY_REPLY']),
            ('WILL_SUPPLY', form.data['WILL_SUPPLY']),
        ]
        for status in reqstatuses:  # for each status
            if status[1] is True:
                status_user = StatusUser(status=status[0], user=user.id)  # create a new status user
                db.session.add(status_user)  # add the status user to the database

        db.session.commit()  # commit changes to the database
