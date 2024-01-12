import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # base configuration
    SECRET_KEY = os.getenv("SECRET_APP_KEY")
    SHARED_SECRET = os.getenv("SHARED_SECRET")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE")  # set the database URI
    ADMINS = os.getenv("ADMINS")
    ALLREPORTS = os.getenv("ALLREPORTS")
    LOG_FILE = os.getenv("LOG_FILE")
    LOG_DIR = os.getenv("LOG_DIR")
    SMTP_ADDRESS = os.getenv("SMTP_ADDRESS")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SITE_URL = os.getenv("SITE_URL")
    SAML_SP = os.getenv("SAML_SP")
    COOKIE_ISSUING_FILE = os.getenv("COOKIE_ISSUING_FILE")
    SCHEDULER_API_ENABLED = True
