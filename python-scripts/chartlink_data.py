import requests
from bs4 import BeautifulSoup
import pandas as pd

charting_Link ="https://chartink.com/screener/"
charting_url = 'https://chartink.com/screener/process'

condition = "( {57960} ( latest Close >= 50 and latest Ema ( close,5 ) > latest Ema ( close,26 ) and latest Ema ( close,13 ) > latest Ema ( close,26 ) and latest Close > 1 day ago Close * 1.03 and latest Volume > latest Sma ( volume,20 ) * 1.0 and latest Ema ( close,5 ) > latest Ema ( close,13 ) and latest High = latest Max ( 260 , latest High ) * 1 and 1 day ago Close > 2 days ago Close * 0.98  ) ) "

def GetDataFromchartink(payload):
    payload ={'scan_clause': payload}

    with requests.Session() as s:
        r = s.get(charting_Link)
        soup = BeautifulSoup(r.text,"html.parser")
        csrf = soup.select_one("[name='csrf-token']")['content']
        s.headers['x-csrf-token'] = csrf
        r = s.post(charting_url,data=payload)

        df = pd.DataFrame()
        for item in r.json()['data']:
            df = pd.concat([df, pd.DataFrame([item])], ignore_index=True)
    return df

data = GetDataFromchartink(condition)
data.to_csv("/home/ubuntu/python-scripts/csv/chartink_result.csv")
print(data)
