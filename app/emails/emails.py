from flask import current_app
import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.extensions import db
from app.utils import utils
from app.models.user import User
from app.models.institution import Institution
from app.models.userday import UserDay


def send_emails():
    today = datetime.datetime.now().strftime('%w')  # get the day of the week as a number (0-6) (Sunday-Saturday)

    users_today = db.session.execute(db.session.query(  # Get list of users for today
        User).outerjoin(UserDay).filter(UserDay.day == today)).scalars()

    users = []  # List of users
    institutions = []  # List of institutions

    for user in users_today:  # Iterate through list of users
        users.append((user.emailaddress, user.instcode))
        if user.instcode not in institutions:  # If institution is not in list of institutions
            institutions.append(user.instcode)  # Add institution to list of institutions

    if len(users) == 0:  # If there are no users for today
        current_app.logger.info('No emails for today')
        return 'No emails for today'

    # Iterate through list of institutions
    for institution in institutions:
        inst_users = []  # List of users for the institution
        for user in users:
            if user[1] == institution:
                inst_users.append(user[0])

        if len(inst_users) == 0:  # If there are no users for the institution,
            continue  # skip to the next institution

        # Generate report for each institution
        inst = Institution.query.filter_by(code=institution).first()  # get the institution
        reqs = utils.get_all_requests(inst)  # get all requests for the institution

        if len(reqs) == 0:  # If there are no requests for the institution,
            current_app.logger.info('No requests for {}'.format(institution))  # log info
            continue  # skip to the next institution

        df = pd.DataFrame.from_dict(reqs)  # create a dataframe from the requests
        df.to_excel('/tmp/{}.xlsx'.format(institution), index=False, header=True)  # write dataframe to excel file

        # Create email
        sender_email = current_app.config['SENDER_EMAIL']  # sender email address
        message = MIMEMultipart("alternative")  # create message
        message["Subject"] = '%s Request Status Exceptions report' % institution.upper()  # set subject
        message["From"] = sender_email  # set sender

        # Create the plain-text and HTML version of your message
        text = """\
        The report is attached.
        """

        html = """\
        <html>
          <body>
            <p>The report is attached.</p>
          </body>
        </html>
        """

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        # Add attachment to message
        with open('/tmp/{}.xlsx'.format(institution), 'rb') as fp:  # open excel file
            part = MIMEApplication(fp.read(), Name='{}.xlsx'.format(institution))  # create attachment
        part['Content-Disposition'] = 'attachment; filename="{}.xlsx"'.format(institution)  # set attachment filename
        message.attach(part)  # attach attachment to message

        # Send email to each user
        for inst_user in inst_users:  # Iterate through list of users
            message["To"] = inst_user  # set recipient

            try:  # try to send email
                smtp = smtplib.SMTP(current_app.config['SMTP_ADDRESS'])  # create smtp server
                smtp.sendmail(sender_email, inst_user, message.as_string())  # send email
                smtp.quit()  # quit smtp server
            except Exception as e:  # catch exception
                current_app.logger.error('Error sending email to {}: {}'.format(inst_user, str(e)))  # log error
            else:  # if no exception
                current_app.logger.info('Email sent to %s' % inst_user)  # log info
