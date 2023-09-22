from logging.handlers import TimedRotatingFileHandler
from settings import log_dir
import logging

# scheduler log
logdir = log_dir  # set the log directory
log_file = logdir + '/email.log'  # set the log file
email_log = logging.getLogger('email')  # create the scheduler log
email_log.setLevel(logging.INFO)  # set the scheduler log level
file_handler = TimedRotatingFileHandler(log_file, when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(  # set the file handler format
    logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %H:%M:%S'
    ))
email_log.addHandler(file_handler)  # add the file handler to the scheduler log


def send_emails():
    # TODO: Query for all users getting an email today
    # TODO: Get list of institutions from users
    # TODO: Iterate through list of institutions
    # TODO: Generate report for each institution
    # TODO: Iterate through list of users for each institution
    # TODO: Send email to each user
    pass
