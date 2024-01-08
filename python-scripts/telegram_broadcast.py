from telethon import TelegramClient
from telethon.tl.functions.messages import SendMediaRequest
import subprocess, json, datetime, csv
import pandas as pd

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
        saved_recommendation_list.append([str(post_id), nsecode_row, str(price), current_date_time, "empty"])
    return saved_recommendation_list

async def scanner(broadcast_pd, nsecode):
    csv_filename = "csv/recommendation.csv"
    recommend_pd = pd.read_csv(csv_filename) 
    filtered_recommend_pd = recommend_pd[recommend_pd['nsecode'] == nsecode].sort_values(by='date', ascending=False).head(1)
    filtered_broadcast_pd = broadcast_pd[broadcast_pd['nsecode'] == nsecode]
    if(not(filtered_recommend_pd.empty and filtered_broadcast_pd.empty)):
        return "both are empty"
    filtered_broadcast_pd = filtered_broadcast_pd[['nsecode', 'Current Price']]
    recommend_row = filtered_recommend_pd.values.tolist()[0]
    broadcast_row = filtered_broadcast_pd.values.tolist()[0]
    if(broadcast_row[1] > recommend_row[2]* (1+10/100)):
        print(recommend_row)
        message = f"🚀 Our recommended stock ({recommend_row[1]}) are is 10% increase!"
        await client.send_message(chat_id, message , reply_to=recommend_row[4])

async def main():
    await client.connect()
    cached_stocks=list(set(read_cached(cached_file)))
    saved_recommendation_list = [["post_id", "nsecode", "price", "date","message_id"]]
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
        await scanner(broadcast_pd, nsecode)
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
        columns=["post_id,nsecode,price,date,message_id"]
        saved_recommendation_list =[",".join(str(item) for item in sublist) for sublist in saved_recommendation_list]
        saved_recommendation_df=pd.DataFrame(saved_recommendation_file+saved_recommendation_list[1:], columns=columns)
        
        if len(saved_recommendation_file) == 0 or saved_recommendation_file[0] != columns[0]:
            saved_recommendation_df.to_csv('./csv/recommendation.csv',header=columns, index=False, quoting=csv.QUOTE_NONE,sep=';')
        else: 
            saved_recommendation_df.to_csv('./csv/recommendation.csv',header=None, index=False, quoting=csv.QUOTE_NONE,sep=';')
    # Optionally keep the client running for further events
    await client.start()
    await client.disconnect()
    #await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
