# main.py

import asyncio
import logging
from datetime import datetime
from config import Config
from data_operations import DataManager, TelegramClientWrapper
from stock_operations import StockScanner
from data_processor import DataProcessor

logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting the application")
    config = Config()
    data_manager = DataManager(config)
    telegram_client = TelegramClientWrapper(config)
    stock_scanner = StockScanner(config, telegram_client, data_manager)

    logger.info(f"Started at: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}")

    try:
        # Create and use DataProcessor
        data_processor = DataProcessor(config)
        broadcast_data = data_processor.process_data()
        
        if broadcast_data is None:
            logger.error("Failed to process data. Exiting.")
            return

        nsecodelist = [item.upper() for item in broadcast_data["nsecode"].tolist()]

        await telegram_client.connect()

        cached_stocks = set(data_manager.read_cached())
        new_stocks = set(nsecodelist) - cached_stocks
        
        for nsecode in new_stocks:
            await telegram_client.send_message(telegram_client.bot_name, f'/chart NSE:{nsecode} 1W')
            logger.info(f"Sent chart request for new stock: {nsecode}")

        data_manager.write_cached(list(cached_stocks.union(new_stocks)))

        await stock_scanner.scan_stocks(broadcast_data, nsecodelist)

    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
    finally:
        await telegram_client.disconnect()

    logger.info(f"Ended at: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}")

if __name__ == '__main__':
    asyncio.run(main())