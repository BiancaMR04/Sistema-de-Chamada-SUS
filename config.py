"""
Configuration settings for Sistema de Chamada SUS.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///chamada_sus.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # e-SUS Integration
    ESUS_API_URL = os.environ.get('ESUS_API_URL', 'https://api.esus.gov.br')
    ESUS_API_KEY = os.environ.get('ESUS_API_KEY', '')
    ESUS_API_TIMEOUT = int(os.environ.get('ESUS_API_TIMEOUT', 3))
    
    # Audio settings
    AUDIO_ENABLED = os.environ.get('AUDIO_ENABLED', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
