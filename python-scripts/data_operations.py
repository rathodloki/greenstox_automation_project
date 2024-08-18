import pandas as pd
import csv
from telethon import TelegramClient
from logger import setup_logger

logger = setup_logger()

class DataManager:
    def __init__(self, config):
        self.config = config
        self.broadcast_csv = self.config.get('python_scripts', 'broadcast_csv')
        self.cached_file = "stock.cache"
        self.recommendation_file = "csv/recommendation.csv"

    def read_broadcast_data(self):
        try:
            data = pd.read_csv(self.broadcast_csv)
            logger.info(f"Successfully read broadcast data from {self.broadcast_csv}")
            return data
        except Exception as e:
            logger.error(f"Failed to read broadcast data: {e}")
            raise

    def read_cached(self):
        try:
            with open(self.cached_file, "r") as file:
                data = [line.strip() for line in file if line.strip()]
            logger.info(f"Successfully read cached data from {self.cached_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to read cached data: {e}")
            return []

    def write_cached(self, data):
        try:
            with open(self.cached_file, "w") as file:
                file.writelines("\n".join(data))
            logger.info(f"Successfully wrote cached data to {self.cached_file}")
        except Exception as e:
            logger.error(f"Failed to write cached data: {e}")
            raise

class TelegramClientWrapper:
    def __init__(self, config):
        self.config = config
        self.api_id = self.config.get('python_scripts', 'api_id')
        self.api_hash = self.config.get('python_scripts', 'api_hash')
        self.chat_id = self.config.get('python_scripts', 'chat_id')
        self.bot_name = self.config.get('python_scripts', 'chart_bot_name')
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)

    async def connect(self):
        try:
            await self.client.connect()
            logger.info("Successfully connected to Telegram")
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            raise

    async def disconnect(self):
        try:
            await self.client.disconnect()
            logger.info("Successfully disconnected from Telegram")
        except Exception as e:
            logger.error(f"Failed to disconnect from Telegram: {e}")

    async def send_message(self, to, message, reply_to=None):
        try:
            sent_message = await self.client.send_message(to, message, reply_to=reply_to)
            logger.info(f"Successfully sent message to {to}")
            return sent_message
        except Exception as e:
            logger.error(f"Failed to send message to {to}: {e}")
            raise
