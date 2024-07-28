import os
from dotenv import load_dotenv

load_dotenv()


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    PORT = os.getenv('PORT', 5001)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URL') or \
        'sqlite:///' + os.path.join(basedir, 'calendar.db')
    if os.environ.get('DB_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ['DB_URL']
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    REDIS_URL = os.getenv('REDIS_URL')
    MAIL_SERVER = os.getenv('MAIL_HOST')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_ENCRYPTION') == 'TLS'
    MAIL_USE_SSL = os.getenv('MAIL_ENCRYPTION') == 'SSL'
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_FROM_ADDRESS')
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME')
    MAIL_PORT = os.getenv('MAIL_PORT', 587 if MAIL_USE_TLS else 465)
    HOLIDAY_API_KEY = os.getenv('HOLIDAY_API_KEY')
