import json
import os
from logger import setup_logger

logger = setup_logger()

class Config:
    def __init__(self):
        secret_file = os.getenv("SECRET_FILE")
        try:
            with open(secret_file, 'r') as file:
                self.secrets = json.load(file)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
        
    def get(self, section, key):
        try:
            return self.secrets[section][key]
        except KeyError:
            logger.error(f"Configuration key not found: {section}.{key}")
            raise
