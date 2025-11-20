import os

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///databricks.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SPARK_MASTER = os.environ.get('SPARK_MASTER') or 'local[*]'
    SPARK_APP_NAME = 'OpenSourceDatabricks'
