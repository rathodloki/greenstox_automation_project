import requests
from bs4 import BeautifulSoup
import pandas as pd

# Read the filtered_stocks.csv file
csv_file_path = '/home/ubuntu/python-scripts/csv/filtered_stocks.csv'
portfolio_df = pd.read_csv(csv_file_path)

# Extract necessary columns from the original CSV
nse_code_list = portfolio_df['nsecode'].tolist()
stock_name_list = portfolio_df['name'].tolist()
bse_code_list = portfolio_df['bsecode'].tolist()
volume_list = portfolio_df['volume'].tolist()

# Lists to store data
current_price_list = []
finstar_list = []
value_star_list = []

for share_name in nse_code_list:
    link_blueprint = "https://ticker.finology.in/company/"
    page = requests.get(link_blueprint + share_name.upper())
    link_soup = BeautifulSoup(page.content, 'html.parser')
    
    # Extracting necessary data
    price_class = link_soup.find(class_="d-block h1 currprice")
    if price_class:
        current_price_element = price_class.find(class_="Number")
        if current_price_element:
            current_price = current_price_element.get_text()
        else:
            current_price = "N/A"
    else:
        current_price = "N/A"
    current_price_list.append(current_price)
    # Extracting finstar and value star ratings
    star_class = link_soup.find(id="mainContent_ltrlOverAllRating")
    if star_class is not None:
        current_star = star_class.get('aria-label')
    else:
        current_star = "N/A"
    star_class = link_soup.find(id="mainContent_ValuationRating")
    if star_class is not None:
        value_star = star_class.get('aria-label')
    else:
        value_star = "N/A"

    finstar_list.append(current_star)
    value_star_list.append(value_star)

# Creating a DataFrame
final_data = pd.DataFrame({
    'nsecode': nse_code_list,
    'stock name': stock_name_list,
    'bsecode': bse_code_list,
    'volume': volume_list,
    'Current Price': current_price_list,
    'finstar': finstar_list,
    'value star': value_star_list
})

# Printing the DataFrame
print(final_data)

# Saving the data to broadcast.csv
final_data.to_csv('/var/www/html/broadcast.csv', index=False)

