import requests, json, logging, datetime, os
import telegram, pandas as pd
from telegram.ext import Updater
from telegram.utils.request import Request

logging.basicConfig(
    filename = "chart_image.log",
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s"))
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

secrets = {}
secret_file = os.getenv("SECRET_FILE")
with open(secret_file, 'r') as file:
    secrets = json.load(file)

bot_token = secrets['chart_image_bot']['bot_token']
group_id = secrets['chart_image_bot']['group_id']
owner_id = secrets['chart_image_bot']['owner_id']
allowed_accounts = {635834411, 6040970776}
request = Request(con_pool_size=8)
bot = telegram.Bot(bot_token, request=request)
updater = Updater(bot=bot, use_context=True)

def caption(nsecode):
    try:
        broadcast_csv = secrets['python_scripts']['csv_dir']+"/broadcast.csv"
        broadcast_pd = pd.read_csv(broadcast_csv)
        stock_details = broadcast_pd[broadcast_pd["nsecode"]== nsecode.split(":")[1]]
        if not stock_details.empty:
            stock_details = list(stock_details.iloc[0])
            message = f"📈 Stock name: {stock_details[1]} ({stock_details[0]})\n\n" \
            f"️️🎚️ Volume: {stock_details[3]}\n\n" \
            f"💹 Radar Price: ₹{stock_details[4]}\n\n" \
            f"⭐ Finstar Rating: {stock_details[5]}\n\n" \
            f"️️🎖️ Valuation Rating: {stock_details[6]}"
            json_body = {"nsecode":stock_details[0],
                        "price":stock_details[4],
                        "date":datetime.datetime.now().isoformat(),
                        "returns":"N/A"}
            return message, json_body

        else:
            return "","" 
    except Exception as e:
         logging.info(f"Broadcast file failed, {e}")
         return "",""

def send_chart_api(update, context):
    if update.effective_user.id not in allowed_accounts:
        update.message.reply_text("Access denied. You are not authorized to use this bot.")
        return
    log_updates(update)
    chart_url = secrets['chart_image_bot']['chart_img_api_url']
    chart_api_key = secrets['chart_image_bot']['chart_img_api_key']
    symbol = None
    interval = None
    user_id = update.effective_user.id
    try:
        if len(update.message.text.split(" ")) == 3:
            symbol = update.message.text.split(" ")[1].upper()
            interval = update.message.text.split(" ")[2].upper()
        else: 
            raise Exception
    except Exception as e:
         logging.info(f"Invalid request")
         bot.send_message(chat_id=user_id, text=f"Invalid command \nKnow more - /help", parse_mode="HTML")
         return "Failed"
         
    headers_list = {
        "x-api-key": chart_api_key,
        "Content-Type": "application/json"
    }
    body = {
        "symbol": symbol,
        "interval": interval,
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "override": {
            "showSymbolWatermark": True
        },
        "studies": [
            {
                "name": "Volume",
                "forceOverlay": False,
                "override": {
                    "Volume.color.0": "rgba(64,211,151,0.7)",
                    "Volume.color.1": "rgba(250,144,120,0.7)"
                }
            }
        ]
    }
    body_json = json.dumps(body)
    response = requests.post(chart_url, headers=headers_list, data=body_json)

    if response.status_code == 200:
        message, json_body = caption(symbol)
        message_data = bot.send_photo(chat_id=group_id, photo=response.content, caption=message)
        username ='admin'
        password = secrets['python_scripts']['admin']
        auth = requests.auth.HTTPBasicAuth(username, password)
        try:
            message_id = message_data.message_id
            json_body['message_id'] = message_id
            api_recommend_url = 'http://127.0.0.1:5000/update/recommendation'
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_recommend_url, json=json_body, auth=auth, headers=headers)
            response.raise_for_status()
        except Exception as e:
         logging.info(f"Message id not update for {symbol}, {e}")
    else:
        logging.error(f"chart_image_Failed_api,{response.status_code}")

def log_updates(update) -> None:
    message_text = update.message.text
    chat_id = update.message.chat_id
    fullname = update.message.from_user.full_name
    logging.info(f"Message from {fullname} ({chat_id}): {message_text}")

def help(update, context):
            if update.effective_user.id not in allowed_accounts:
                update.message.reply_text("Access denied. You are not authorized to use this bot.")
                return

            log_updates(update)
            user_id = update.effective_user.id
            chat_info = bot.get_chat(chat_id=user_id)
            message = "Follow below:\n\n/chart [exchange:symbol] [interval] - \nGenerates a chart image for the specified symbol and interval.\nExample: /chart NSE:GPPL 1W \n\n/help - Displays this help message."
            bot.send_message(chat_id=user_id, text=message)
            

def main():
    # Set up dispatcher and job queue
    updater = telegram.ext.Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(telegram.ext.CommandHandler('help', help))
    dp.add_handler(telegram.ext.CommandHandler('chart', send_chart_api))

    # Start the bot
    updater.start_polling()
    logging.info("Bot started")
    updater.idle()

if __name__ == '__main__':
    main()
