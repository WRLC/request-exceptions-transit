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
    current_app.logger.setLevel(current_app.config['LOG_LEVEL'])  # set log level
    today = datetime.datetime.now().strftime('%w')  # get the day of the week as a number (0-6) (Sunday-Saturday)

    users_today = db.session.execute(db.session.query(  # Get list of users for today
        User).outerjoin(UserDay).filter(UserDay.day == today)).scalars()

    if users_today is None:  # If there are no users for today
        current_app.logger.info('No emails for today')
        return 'No emails for today'

    else:
        for user in users_today:  # Iterate through list of users
            inst = db.session.execute(db.select(Institution).where(Institution.code == user.instcode)).scalar_one()

            # Generate report
            reqs = utils.get_exceptions_xlsx(user, inst)  # get all requests for the institution

            if len(reqs) == 0:  # If there are no requests for the institution,
                current_app.logger.info('No requests for {}'.format(inst.code))  # log info
                continue  # skip to the next user

            df = pd.DataFrame.from_dict(reqs)  # create a dataframe from the requests
            df.to_excel('/tmp/{}.xlsx'.format(inst.code), index=False, header=True)  # write dataframe to excel file

            # Create email
            sender_email = current_app.config['SENDER_EMAIL']  # sender email address
            message = MIMEMultipart("alternative")  # create message
            message["Subject"] = '%s Request Status Exceptions report' % inst.code.upper()  # set subject
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
            with open('/tmp/{}.xlsx'.format(inst.code), 'rb') as fp:  # open excel file
                part = MIMEApplication(fp.read(), Name='{}.xlsx'.format(inst.code))  # create attachment
            part['Content-Disposition'] = 'attachment; filename="{}.xlsx"'.format(inst.code)  # set attachment filename
            message.attach(part)  # attach attachment to message

            message["To"] = user.emailaddress  # set recipient

            try:  # try to send email
                smtp = smtplib.SMTP(current_app.config['SMTP_ADDRESS'])  # create smtp server
                smtp.sendmail(sender_email, user.emailaddress, message.as_string())  # send email
                smtp.quit()  # quit smtp server
            except Exception as e:  # catch exception
                current_app.logger.error('Error sending email to {}: {}'.format(user.emailaddress, str(e)))  # log error
            else:  # if no exception
                current_app.logger.info('Email sent to %s' % user.emailaddress)  # log info
