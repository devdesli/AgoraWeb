# logging_config.py
import os
import logging
from logging.handlers import RotatingFileHandler


upload_logger = logging.getLogger('upload_logger')
activity_logger = logging.getLogger('activity_logger')
error_logger = logging.getLogger('error_logger')

def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] in %(module)s: %(message)s')

    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    upload_handler = RotatingFileHandler('logs/upload.log', maxBytes=10240, backupCount=3)
    upload_handler.setFormatter(formatter)
    upload_logger = logging.getLogger('upload_logger')
    upload_logger.setLevel(logging.INFO)
    upload_logger.addHandler(upload_handler)

    activity_handler = RotatingFileHandler('logs/activity.log', maxBytes=10240, backupCount=3, delay=True)
    activity_handler.setFormatter(formatter)
    activity_logger = logging.getLogger('activity_logger')
    activity_logger.setLevel(logging.INFO)
    activity_logger.addHandler(activity_handler)

    error_handler = RotatingFileHandler('logs/error.log', maxBytes=10240, backupCount=3)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(error_handler)