from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from config import Config
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    #in realworld application need to change this to the frontend url
    CORS(app)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)

    api = Api(app)
    from app.resources import init_routes
    init_routes(api)

    JWTManager(app)
    
    scheduler = BackgroundScheduler()
    logger = logging.getLogger('apscheduler')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    scheduler.add_jobstore(SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI']))
    scheduler.start()
    
    app.scheduler = scheduler

    return app



# def create_celery_app():
#     app = create_app()
#     celery = Celery(app.import_name, broker=app.config['REDIS_URL'])
#     celery.conf.update(app.config)
#     from app.tasks import celery as celery_blueprint
#     celery.register_blueprint(celery_blueprint)
#     return celery
