from bs4 import BeautifulSoup
import requests
import pandas as pd

# Function to get a valid response from URLs
def get_valid_response(urls):
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            pass
    return None

# Function to fetch fundamentals data
def fundamentals(symbols, key=None):
    if not isinstance(symbols, list):
        symbols = [symbols]  # Convert a single symbol to a list

    keys = ['Quarterly Results', 'Profit & Loss', 'Balance Sheet',
            'Cash Flows', 'Ratios', 'Shareholding Pattern q',
            'Shareholding Pattern y']

    all_results = {}

    for symbol in symbols:
        results = {}

        urls = [f'https://www.screener.in/company/{symbol}/', f'https://www.screener.in/company/{symbol}/consolidated/']
        response = get_valid_response(urls)
        if response is None:
            print(f"Skipping {symbol}. Unable to fetch data from screener.in.")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        for i, table in enumerate(soup.find_all('table', class_='data-table')):
            column_header_raw = table.find_all('th')
            column_header = [headers.text.strip() for headers in column_header_raw]

            df = pd.DataFrame(columns=column_header)

            column_data = table.find_all('tr')

            for row in column_data[1:]:
                row_data = row.find_all('td')
                individual_row_data = [data.text.strip() for data in row_data]
                length = len(df)
                df.loc[length] = individual_row_data

            df.insert(0, 'Symbol', symbol)
            df = df.rename(columns={df.columns[1]: 'Particulars'})
            results[keys[i]] = df

        all_results[symbol] = results

    if key is not None:
        selected_results = {symbol: results[key] for symbol, results in all_results.items() if key in results}
        return selected_results
    else:
        return None

# Read stock symbols from 'chartink_results.csv'
csv_file_path = '/home/ubuntu/python-scripts/csv/chartink_result.csv'  # Replace with the actual file path
portfolio_df = pd.read_csv(csv_file_path)
#portfolio = portfolio_df['nsecode'].tolist()
portfolio = [nsecode.replace("-", "_") for nsecode in portfolio_df['nsecode'].tolist()]

# Create a DataFrame to store filtered stock information
filtered_stocks = pd.DataFrame()

for stock_symbol in portfolio:
    # Fetch Profit & Loss data for each stock
    data = fundamentals(stock_symbol, 'Quarterly Results')
    if data and stock_symbol in data:
        profit_loss_df = data[stock_symbol]
        # Filter data for Operating Profit for last 5 quarterly periods
        operating_profit_df = profit_loss_df[profit_loss_df['Particulars'] == 'Operating Profit']

        # If Operating Profit data is not found, try Financing Profit
        if operating_profit_df.empty:
            financing_profit_df = profit_loss_df[profit_loss_df['Particulars'] == 'Financing Profit']

            if not financing_profit_df.empty:
                last_5_quarters = financing_profit_df.iloc[:, -5:]

                # Remove commas from the numbers and convert to float
                last_5_quarters = last_5_quarters.replace(',', '', regex=True).astype(float)

                # Check for any negative values in the last 5 quarters of Financing Profit
                if not (last_5_quarters < 0).any().any():
                    filtered_stocks = pd.concat([filtered_stocks, portfolio_df[portfolio_df['nsecode'] == stock_symbol]])

                    # Print relevant info (optional)
                    print(f"Stock: {stock_symbol}")
                    print(f"No negative Financing Profit in last 5 quarters.")
                    print("\n\n")
                else:
                    print(f"Stock: {stock_symbol} skipped. Negative Financing Profit found in last 5 quarters.")
            else:
                print(f"Stock: {stock_symbol} skipped. No Financing Profit data found.")
        else:
            last_5_quarters = operating_profit_df.iloc[:, -5:]

            # Remove commas from the numbers and convert to float
            last_5_quarters = last_5_quarters.replace(',', '', regex=True).astype(float)

            # Check for any negative values in the last 5 quarters of Operating Profit
            if not (last_5_quarters < 0).any().any():

                filtered_stocks = pd.concat([filtered_stocks, portfolio_df[portfolio_df['nsecode'] == stock_symbol]])
                # Print relevant info (optional)
                print(f"Stock: {stock_symbol}")
                print(f"No negative Operating Profit in last 5 quarters.")
                print("\n\n")
            else:
                print(f"Stock: {stock_symbol} skipped. Negative Operating Profit found in last 5 quarters.")

# Save filtered stock information to a new CSV file
filtered_stocks.to_csv('/home/ubuntu/python-scripts/csv/filtered_stocks.csv', index=False)

