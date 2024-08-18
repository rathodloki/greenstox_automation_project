# stock_operations.py

import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StockScanner:
    def __init__(self, config, telegram_client, data_manager):
        self.config = config
        self.telegram_client = telegram_client
        self.data_manager = data_manager
        self.recommendation_file = self.config.get('python_scripts', 'csv_dir') + "/recommendation.csv"

    async def scan_stocks(self, broadcast_pd, nsecodelist):
        for nsecode in nsecodelist:
            nsecode = nsecode.replace("-", "_")
            await self.scan_stock(broadcast_pd, nsecode)

    async def scan_stock(self, broadcast_pd, nsecode):
        try:
            recommend_pd = self.read_recommendation_data()
            filtered_recommend_pd = recommend_pd[recommend_pd['nsecode'] == nsecode].sort_values(by='date').tail(1)
            filtered_broadcast_pd = broadcast_pd[broadcast_pd['nsecode'] == nsecode]

            if filtered_recommend_pd.empty or filtered_broadcast_pd.empty:
                logger.info(f"No data found for stock: {nsecode}")
                return

            recommend_row = filtered_recommend_pd.iloc[0]
            broadcast_row = filtered_broadcast_pd[['nsecode', 'Current Price']].iloc[0]

            current_price = float(broadcast_row['Current Price'])
            recommended_price = float(recommend_row['price'])

            if self.should_notify(current_price, recommended_price):
                await self.send_notification(recommend_row, broadcast_row)
            elif self.should_update(current_price, recommended_price):
                self.update_price_recommendation(nsecode, current_price)
        except Exception as e:
            logger.error(f"Error scanning stock {nsecode}: {e}")

    def should_notify(self, current_price, recommended_price):
        return True
        return current_price > recommended_price * 1.1

    def should_update(self, current_price, recommended_price):
        return True
        return current_price > recommended_price * 1.03

    async def send_notification(self, recommend_row, broadcast_row):
        try:
            current_price = float(broadcast_row['Current Price'])
            recommended_price = float(recommend_row['price'])
            percentage = ((current_price - recommended_price) / recommended_price) * 100
            returns = f"{percentage:.2f}%"
            message = f"🚀 Our recommended stock ({recommend_row['nsecode']}) is on {returns} increase, from {recommended_price} to {int(current_price)}!💹 "
            sent_message = await self.telegram_client.send_message(self.telegram_client.chat_id, message, reply_to=int(recommend_row['message_id']))
            self.update_price_recommendation(recommend_row['nsecode'], current_price, sent_message.id, returns)
            logger.info(f"Notification sent for stock {recommend_row['nsecode']}")
        except Exception as e:
            logger.error(f"Failed to send notification for stock {recommend_row['nsecode']}: {e}")

    def update_price_recommendation(self, nsecode, price, message_id="empty", returns="no"):
        try:
            recommend_pd = self.read_recommendation_data()
            new_row = {
                'post_id': len(recommend_pd) + 1,
                'nsecode': nsecode,
                'price': price,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'message_id': message_id,
                'returns': returns
            }
            recommend_pd = recommend_pd.append(new_row, ignore_index=True)
            self.write_recommendation_data(recommend_pd)
            logger.info(f"Successfully updated price recommendation for {nsecode}")
        except Exception as e:
            logger.error(f"Error updating price recommendation for {nsecode}: {e}")

    def read_recommendation_data(self):
        try:
            return pd.read_csv(self.recommendation_file)
        except Exception as e:
            logger.error(f"Error reading recommendation data: {e}")
            return pd.DataFrame(columns=['post_id', 'nsecode', 'price', 'date', 'message_id', 'returns'])

    def write_recommendation_data(self, df):
        try:
            df.to_csv(self.recommendation_file, index=False)
            logger.info(f"Successfully wrote recommendation data to {self.recommendation_file}")
        except Exception as e:
            logger.error(f"Error writing recommendation data: {e}")