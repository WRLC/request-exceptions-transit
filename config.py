import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # base configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE")  # set the database URI
    SECRET_KEY = os.getenv("SECRET_APP_KEY")
    SHARED_SECRET = os.getenv("SHARED_SECRET")
    ADMINS = os.getenv("ADMINS")
    ALLREPORTS = os.getenv("ALLREPORTS")
    LOG_FILE = os.getenv("LOG_FILE")
    LOG_DIR = os.getenv("LOG_DIR")
    SMTP_ADDRESS = os.getenv("SMTP_ADDRESS")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SITE_URL = os.getenv("SITE_URL")
    SAML_SP = os.getenv("SAML_SP")
    COOKIE_ISSUING_FILE = os.getenv("COOKIE_ISSUING_FILE")
    LOGOUT_SCRIPT = os.getenv("LOGOUT_SCRIPT")
    COOKIE_PREFIX = os.getenv("COOKIE_PREFIX")
    MEMCACHED_SERVER = os.getenv("MEMCACHED_SERVER")
    SERVICE_SLUG = os.getenv("SERVICE_SLUG")
    SCHEDULER_API_ENABLED = True
