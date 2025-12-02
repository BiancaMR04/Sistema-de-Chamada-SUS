"""
Configuration settings for Sistema de Chamada SUS.
"""
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

# Maximum timeout for e-SUS API (in seconds)
ESUS_MAX_TIMEOUT = 3


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///chamada_sus.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # e-SUS Integration
    ESUS_API_URL = os.environ.get('ESUS_API_URL', 'https://api.esus.gov.br')
    ESUS_API_KEY = os.environ.get('ESUS_API_KEY', '')
    ESUS_API_TIMEOUT = min(int(os.environ.get('ESUS_API_TIMEOUT', ESUS_MAX_TIMEOUT)), ESUS_MAX_TIMEOUT)
    
    # Audio settings
    AUDIO_ENABLED = os.environ.get('AUDIO_ENABLED', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    def __init__(self):
        """Validate production configuration."""
        super().__init__()
        if self.SECRET_KEY == 'dev-secret-key':
            warnings.warn(
                "WARNING: Using default SECRET_KEY in production. "
                "Set SECRET_KEY environment variable for security.",
                UserWarning
            )


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
