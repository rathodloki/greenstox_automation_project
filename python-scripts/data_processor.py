# data_processor.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import logging
from logging.handlers import RotatingFileHandler

class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.logger = self.setup_logger()
        self.broadcast_csv = self.config.get('python_scripts', 'broadcast_csv')

    def setup_logger(self):
        logger = logging.getLogger('DataProcessor')
        logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def get_chartink_data(self):
        charting_url = 'https://chartink.com/screener/process'
        condition = "( {57960} ( latest Close >= 50 and latest Ema ( close,5 ) > latest Ema ( close,26 ) and latest Ema ( close,13 ) > latest Ema ( close,26 ) and latest Close > 1 day ago Close * 1.03 and latest Volume > latest Sma ( volume,20 ) * 1.0 and latest Ema ( close,5 ) > latest Ema ( close,13 ) and latest High = latest Max ( 260 , latest High ) * 1 and 1 day ago Close > 2 days ago Close * 0.98  ) ) "

        payload = {'scan_clause': condition}

        try:
            with requests.Session() as s:
                r = s.get('https://chartink.com/screener/')
                soup = BeautifulSoup(r.text, "html.parser")
                csrf = soup.select_one("[name='csrf-token']")['content']
                s.headers['x-csrf-token'] = csrf
                r = s.post(charting_url, data=payload)
                
                df = pd.DataFrame()
                for item in r.json()['data']:
                    df = pd.concat([df, pd.DataFrame([item])], ignore_index=True)
            
            self.logger.info("Successfully retrieved data from Chartink")
            return df
        except Exception as e:
            self.logger.error(f"Error retrieving data from Chartink: {e}")
            return pd.DataFrame()

    def get_fundamentals(self, symbols):
        def get_valid_response(urls):
            for url in urls:
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    return response
                except requests.exceptions.RequestException:
                    continue
            return None

        all_results = {}

        for symbol in symbols:
            urls = [f'https://www.screener.in/company/{symbol}/', f'https://www.screener.in/company/{symbol}/consolidated/']
            response = get_valid_response(urls)
            if response is None:
                self.logger.warning(f"Unable to fetch data for {symbol} from screener.in")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            quarterly_results = soup.find_all('table', class_='data-table')[0]
            column_header = [headers.text.strip() for headers in quarterly_results.find_all('th')]
            df = pd.DataFrame(columns=column_header)

            for row in quarterly_results.find_all('tr')[1:]:
                row_data = [data.text.strip() for data in row.find_all('td')]
                df.loc[len(df)] = row_data

            df.insert(0, 'Symbol', symbol)
            df = df.rename(columns={df.columns[1]: 'Particulars'})
            all_results[symbol] = df

        self.logger.info(f"Retrieved fundamentals for {len(all_results)} symbols")
        return all_results

    def filter_stocks(self, chartink_data, fundamentals):
        filtered_stocks = pd.DataFrame()

        for _, row in chartink_data.iterrows():
            symbol = row['nsecode'].replace("-", "_")
            if symbol in fundamentals:
                df = fundamentals[symbol]
                profit_df = df[df['Particulars'].isin(['Operating Profit', 'Financing Profit'])]
                
                if not profit_df.empty:
                    last_5_quarters = profit_df.iloc[:, -5:]
                    last_5_quarters = last_5_quarters.replace(',', '', regex=True).astype(float)
                    
                    if not (last_5_quarters < 0).any().any():
                        filtered_stocks = pd.concat([filtered_stocks, row.to_frame().T])

        self.logger.info(f"Filtered down to {len(filtered_stocks)} stocks")
        return filtered_stocks

    def get_additional_data(self, stocks):
        additional_data = []

        for _, stock in stocks.iterrows():
            share_name = stock['nsecode']
            url = f"https://ticker.finology.in/company/{share_name.upper()}"
            
            try:
                page = requests.get(url)
                soup = BeautifulSoup(page.content, 'html.parser')
                
                price_class = soup.find(class_="d-block h1 currprice")
                current_price = price_class.find(class_="Number").get_text() if price_class else "N/A"
                
                star_class = soup.find(id="mainContent_ltrlOverAllRating")
                finstar = star_class.get('aria-label') if star_class else "N/A"
                
                value_star_class = soup.find(id="mainContent_ValuationRating")
                value_star = value_star_class.get('aria-label') if value_star_class else "N/A"
                
                additional_data.append({
                    'nsecode': share_name,
                    'Current Price': current_price,
                    'finstar': finstar,
                    'value star': value_star
                })
            except Exception as e:
                self.logger.error(f"Error fetching additional data for {share_name}: {e}")
        
        self.logger.info(f"Retrieved additional data for {len(additional_data)} stocks")
        return pd.DataFrame(additional_data)

    def process_data(self):
        self.logger.info("Starting data processing")
        
        chartink_data = self.get_chartink_data()
        if chartink_data.empty:
            self.logger.error("No data retrieved from Chartink. Exiting.")
            return None

        symbols = [nsecode.replace("-", "_") for nsecode in chartink_data['nsecode'].tolist()]
        fundamentals = self.get_fundamentals(symbols)
        
        filtered_stocks = self.filter_stocks(chartink_data, fundamentals)
        if filtered_stocks.empty:
            self.logger.warning("No stocks passed the filtering criteria. Exiting.")
            return None

        additional_data = self.get_additional_data(filtered_stocks)
        
        final_data = pd.merge(filtered_stocks, additional_data, on='nsecode')
        
        # Select and rename columns for the final output
        output_columns = {
            'nsecode': 'nsecode',
            'name': 'stock name',
            'bsecode': 'bsecode',
            'volume': 'volume',
            'Current Price': 'Current Price',
            'finstar': 'finstar',
            'value star': 'value star'
        }
        final_output = final_data[list(output_columns.keys())].rename(columns=output_columns)
        
        final_output.to_csv(self.broadcast_csv, index=False)
        self.logger.info(f"Successfully wrote data to {self.broadcast_csv}")
        
        return final_output