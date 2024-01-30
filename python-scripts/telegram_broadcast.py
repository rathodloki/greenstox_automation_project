from telethon import TelegramClient
from telethon.tl.functions.messages import SendMediaRequest
import subprocess, json, datetime, csv, requests
import pandas as pd
print(f"---------------Started at: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}---------------")
secrets = {}
with open('secret.json', 'r') as file:
    secrets = json.load(file)

api_id = secrets['api_id']
api_hash = secrets['api_hash']
chat_id = secrets['chat_id']
bot_name = '@chartbot_telegrambot'
broadcast_csv = '/var/www/html/broadcast.csv'
cached_file = "stock.cache"
recommendation_file = "/home/ubuntu/python-scripts/csv/recommendation.csv"

#running analyzing
subprocess.run(["python", "/home/ubuntu/python-scripts/analyzer.py"])
broadcast_pd = pd.read_csv(broadcast_csv)
nsecodelist = broadcast_pd["nsecode"].tolist()
#telegram message listener
client = TelegramClient('session_name', api_id, api_hash)

nsecodelist = [item.upper() for item in nsecodelist]
def cached(cached_file):
    cached_nsecode = read_cached(cached_file)
    cached_nsecode = list(set(cached_nsecode))
    update_nsecode = nsecodelist.copy()
    for nsecode in cached_nsecode:
         if nsecode in update_nsecode:
            update_nsecode.remove(nsecode)
    update_nsecode = cached_nsecode + update_nsecode
    with open(cached_file, "w") as file:
        file.writelines("\n".join(update_nsecode))

def read_cached(cached_file):
    try:
        with open(cached_file, "r") as file:
            lines = file.readlines()
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        print(f"File problem in {cached_file}", e)

def saved_recommendation(post_id,nsecode,saved_recommendation_list):
    broadcast_data = broadcast_pd.values.tolist()
    for row in broadcast_data:
        if nsecode != row[0].upper():
            continue
        nsecode_row = row[0].upper()
        price = row[4]  
        current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        saved_recommendation_list.append([str(post_id), nsecode_row, str(price), current_date_time, "empty", "no"])
    return saved_recommendation_list

async def scanner(broadcast_pd, nsecode):
    csv_filename = "csv/recommendation.csv"
    recommend_pd = pd.read_csv(csv_filename) 
    filtered_recommend_pd = recommend_pd[recommend_pd['nsecode'] == nsecode].sort_values(by='date').head(1)
    filtered_broadcast_pd = broadcast_pd[broadcast_pd['nsecode'] == nsecode]
    if(filtered_recommend_pd.empty and filtered_broadcast_pd.empty):
        return "both are empty"
    filtered_broadcast_pd = filtered_broadcast_pd[['nsecode', 'Current Price']]
    recommend_row = filtered_recommend_pd.values.tolist()[0]
    broadcast_row = filtered_broadcast_pd.values.tolist()[0]
    notify = False
    # 10% increase finder
    filtered_df = recommend_pd[recommend_pd['nsecode'] == nsecode]
    non_na_rows = filtered_df[filtered_df['returns'].astype(str).str.lower() != 'no']
    is10increased = non_na_rows.sort_values(by='date', ascending=False).head(1)
    if is10increased.empty:
        is10increased = recommend_row
    else:
        is10increased = is10increased.values.tolist()[0]
    if(broadcast_row[1] > is10increased[2]*(1+10/100)):
        percentage = ((broadcast_row[1]-recommend_row[2])/recommend_row[2])*100
        returns = f"{percentage:.2f}%"
        print(recommend_row)
        notify = True
        message = f"🚀 Our recommended stock ({recommend_row[1]}) is on {returns} increase, from {recommend_row[2]} to {int(broadcast_row[1])}!💹 "
        print(message)
        sent_message = await client.send_message(chat_id, message , reply_to=int(recommend_row[4]))
        message_id = sent_message.id
        print("pinning message")
        # await client.pin_message(chat_id, message=message_id, notify=False)
        username ='admin'
        password = secrets['admin']
        auth = requests.auth.HTTPBasicAuth(username, password)

        url = "http://127.0.0.1:5000/update/price_recommendation"
        data = {
                    "nsecode": recommend_row[1],
                    "price": broadcast_row[1],
                    "message_id": message_id,
                    "returns": returns
                }
        response = requests.post(url, json=data, auth=auth)
        if response.status_code == 200:
            print(response.text)
    
    if not notify:
        if(broadcast_row[1] > recommend_row[2]* (1+3/100)):
            username ='admin'
            password = secrets['admin']
            auth = requests.auth.HTTPBasicAuth(username, password)

            url = "http://127.0.0.1:5000/update/price_recommendation"
            data = {
                        "nsecode": recommend_row[1],
                        "price": broadcast_row[1],
                        "message_id": "empty",
                        "returns": "no"
                    }
            response = requests.post(url, json=data, auth=auth)
            if response.status_code == 200:
                print(response.text)

async def main():
    await client.connect()
    cached_stocks=list(set(read_cached(cached_file)))
    saved_recommendation_list = [["post_id", "nsecode", "price", "date","message_id","returns"]]
    saved_recommendation_file = read_cached(recommendation_file)

    try:
        if(len(saved_recommendation_file) == 0):
            post_id = 0
        elif(len(saved_recommendation_file) == 1):
            post_id = 1
        else:
            post_id = int(saved_recommendation_file[-1].split(",")[0]) + 1
    except Exception as e:
        print("Error in saved_recommendation_list", e)
    skiplist = []
    for nsecode in nsecodelist:
        nsecode = nsecode.replace("-", "_")
        if nsecode in cached_stocks:
            skiplist.append(nsecode)
            continue
        saved_recommendation_list = saved_recommendation(post_id,nsecode,saved_recommendation_list)
        post_id+=1
        print(f"running: {nsecode}")
        await client.send_message(bot_name, '/chart NSE:'+nsecode+' 1W')
    cached(cached_file)
    await client.send_message(bot_name, f"Skipped: {skiplist}")
    if(len(saved_recommendation_list) != 1):
        columns=["post_id,nsecode,price,date,message_id,returns"]
        saved_recommendation_list =[",".join(str(item) for item in sublist) for sublist in saved_recommendation_list]
        saved_recommendation_df=pd.DataFrame(saved_recommendation_file+saved_recommendation_list[1:], columns=columns)
        
        if len(saved_recommendation_file) == 0 or saved_recommendation_file[0] != columns[0]:
            saved_recommendation_df.to_csv('./csv/recommendation.csv',header=columns, index=False, quoting=csv.QUOTE_NONE,sep=';')
        else: 
            saved_recommendation_df.to_csv('./csv/recommendation.csv',header=None, index=False, quoting=csv.QUOTE_NONE,sep=';')
    # Optionally keep the client running for further events
    for nsecode in nsecodelist:
        nsecode = nsecode.replace("-", "_")  
        await scanner(broadcast_pd, nsecode)      
    await client.start()
    await client.disconnect()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
print(f"---------------Ended at: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}---------------")
