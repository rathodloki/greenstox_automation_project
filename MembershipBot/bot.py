import json, time, re, validate_email_address, telegram, logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Loading secret file
secrets = {}
with open('secret.json', 'r') as file:
    secrets = json.load(file)


# Set up bot and group IDs
TOKEN = secrets['token']
group_id = secrets['group_id']
OWNER_ID = secrets['owner_id']
DATA_FILE = 'schedule.json' # Path to JSON that stores all data about memberships
CODES_FILE = 'codes.txt' # Path to TXT that stores all codes to be redeemed
upi_id = secrets['upi_id']
upi_qr_code = secrets['upi_qrcode_image']


bot = telegram.Bot(TOKEN)
updater = Updater(bot=bot, use_context=True)
plan_message_ids = {}
contact_ask = {'name':False,
               'email':False,
               'phone':False
               }
data = {}
contact_details = {}
contact_complete = False
def contact(update,contact):
    global contact_ask
    user_id = update.effective_user.id
    if(contact == "name"):
        bot.sendMessage(chat_id=user_id, text="To proceed, please provide your full name:")
        contact_ask[contact] = True
    elif(contact == "email"):
        bot.sendMessage(chat_id=user_id, text="kindly enter your email address:")
        contact_ask[contact] = True
    elif(contact == "phone"):
        bot.sendMessage(chat_id=user_id, text="please share your mobile number:")
        contact_ask[contact] = True

def handle_contact(update, context):
     global contact_ask
     global contact_details
     user_id = update.effective_user.id
     if contact_ask['name']:
        if not update.message.text.strip():
             bot.send_message(chat_id=user_id, text=message, parse_mode="HTML")
        else:
             if 2 <= len(update.message.text) <= 50:
                  if all(char.isalpha() or char.isspace() or char in ["-", "'"] for char in update.message.text):
                    names = update.message.text.split()
                    if len(names) >= 2:
                        if re.match("^[A-Za-z -']+$", update.message.text):  
                            contact_details['name'] = update.message.text
                            contact_ask['name'] = False
                            contact(update, 'email')
                        else:
                            bot.send_message(user_id, "Invalid Full name. Full name contains invalid characters.\n\nPlease re-enter Full name again",parse_mode= "HTML")
                    else:
                         bot.send_message(user_id, "Invalid Full name. Full name should have at least a first name and a last name.\n\nPlease re-enter Full name again",parse_mode= "HTML")
                  else:
                       bot.send_message(user_id, "Invalid characters in the full name.\n\nPlease re-enter Full name again",parse_mode= "HTML")
             else:  
                bot.send_message(user_id, "Invalid Full name. Full name must be between 2 and 50 characters.\n\nPlease re-enter Full name again",parse_mode= "HTML")
                            
     elif contact_ask['email']:
        is_valid_email = validate_email_address.validate_email(update.message.text)
        if is_valid_email: 
            contact_details['email'] = update.message.text
            contact_ask['email'] = False
            contact(update, 'phone')
        else:
             bot.send_message(user_id, "Invalid email address\n\nPlease re-enter email address again", parse_mode="HTML")
     elif contact_ask['phone']:
        is_valid_mobile_number = bool(re.match(re.compile(r'^\d{10}$'), update.message.text))
        if is_valid_mobile_number:
            contact_details['phone'] = update.message.text
            contact_ask['phone'] = False
            contact_complete = True
        else:
            bot.send_message(user_id, "Invalid mobile number. Please enter a 10-digit number without spaces or special characters.\n\nPlease re-enter Mobile number again", parse_mode="HTML")
        previous_data = read_data()
        data.update(previous_data)
        all_true = all(value for value in contact_ask.values())
        if not all_true:
            data[str(user_id)].update({'Fullname':contact_details['name'],
            'email':contact_details['email'],'phone':contact_details['phone']})
            write_data(data)
            plan = data[str(user_id)]['plan']
            message = (f"Please scan the QR code or use UPI id and complete your payment for {plan} access.⚡️")
            send_qr_code(update, context, message)
        
def send_qr_code(update, context, message):
    user_id = update.effective_user.id
    with open(upi_qr_code, 'rb') as image_file:
        bot.send_photo(chat_id=user_id, photo=image_file, caption=f"UPI ID: {upi_id}")
        bot.send_message(chat_id=user_id, text=message, parse_mode="HTML")
        bot.send_message(chat_id=user_id, text=f"We will review your payment and provide access to our channel!\nStay tuned for the update! 🌟", parse_mode="HTML")
     
def button_click_handler(update, context):
    query = update.callback_query
    option = query.data 
    user_id = update.effective_user.id

    
    if option == "1 Day":
        logging.info(f"User {user_id}: choosed Plan: {option}")
        subscription_plan(option, update, context)
    elif option == "7 Days":
        logging.info(f"User {user_id}: choosed Plan: {option}")
        subscription_plan(option, update, context)
    elif option == "1 Month":
        logging.info(f"User {user_id}: choosed Plan: {option}")
        subscription_plan(option, update, context)
    elif option == "3 Months":
        logging.info(f"User {user_id}: choosed Plan: {option}")
        subscription_plan(option, update, context)
    elif option == "6 Months":
        logging.info(f"User {user_id}: choosed Plan: {option}")
        subscription_plan(option, update, context)
    elif option == "1 Year":
        subscription_plan(option, update, context)
    elif option.split(",")[0] == "cancel":
        days = option.split(",")[2]
        date = option.split(",")[1]
        new_plan(days, date, update, context)
    elif option == "new_plan.nope":
        bot.send_message(chat_id=query.message.chat_id, text="Alright, have a nice day :)")
    else:
        bot.send_message(chat_id=query.message.chat_id, text="Invalid option selected.")


def help(update, context):
            user_id = update.effective_user.id
            chat_info = bot.get_chat(chat_id=user_id)
            username = chat_info.username

            bot.send_message(chat_id=user_id, 
                 text=f"Help - To view and subscribe our plans, please click /subscribe", 
                 parse_mode="HTML")
            
def subscribe(update, context):
            user_id = update.effective_user.id
            chat_info = bot.get_chat(chat_id=user_id)
            username = chat_info.username
            keyboard = [
                        [InlineKeyboardButton("1 Day", callback_data="1 Day"), InlineKeyboardButton("7 Days", callback_data="7 Days"), InlineKeyboardButton("1 Month", callback_data="1 Month")],
                        [InlineKeyboardButton("3 Months", callback_data="3 Months"), InlineKeyboardButton("6 Months", callback_data="6 Months"), InlineKeyboardButton("1 Year", callback_data="1 Year")]
                    ]
            reply_markup = InlineKeyboardMarkup(keyboard, one_time_keyboard=True)
            bot.send_message(chat_id=user_id, text="Choose a Plan:", reply_markup=reply_markup)

                 

# Reads data from JSON
def read_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data

# Writes data on JSON
def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Process the ban/kick process.
def remove_user(context):
    user_id = context['user_id']
    try:
        bot.kick_chat_member(chat_id=group_id, user_id=user_id) # Change bot.ban_chat_member to bot.kick.chat_member in case you want to KICK instead of BAN
        logging.info(f"User {user_id} removed from group {group_id}")
        bot.send_message(chat_id=OWNER_ID, 
                 text=f"❌ <b>REMOVED</b>: <a href='tg://user?id={user_id}'>{user_id}</a> from group.", 
                 parse_mode="HTML")
        bot.send_message(chat_id=user_id, 
                 text=f"❌ <b>LICENSE EXPIRED</b>", 
                 parse_mode="HTML")
    except telegram.error.BadRequest:
        logging.error(f"Failed to remove user {user_id} from group {group_id}")
    data = read_data()
    if str(user_id) in data:
        del data[str(user_id)]
        write_data(data)

# Handles /redeem command
def new_plan(days, date, update, context):
     user_id = str(update.effective_user.id)
     data = read_data()
     data[str(user_id)].update({'removal_date': date,'plan':days})
     write_data(data)
     message = (f"Please scan the QR code or use UPI id and complete your payment for access.⚡️")
     send_qr_code(update, context, message)


def subscription_plan(option, update, context):
    user_id = str(update.effective_user.id)
    if option == "1 Day": 
        d = 1
    elif option == "7 Days": 
        d = 7
    elif option == "1 Month":
        d = 30
    elif option == "3 Months":
        d = 90
    elif option == "6 Months":
        d = 180
    elif option == "1 Year":
        d = 365
    data = read_data()

    if str(user_id) in data:
                    # Calculate date and time when user should be removed
                    job_data = data[user_id]
                    today = datetime.now()
                    removal_date = today + timedelta(days=d)
                    removal_date = removal_date.isoformat()
                    user_exist=True
    else:
        # Calculate date and time when user should be removed
        removal_date = datetime.now() + timedelta(days=d)
        user_exist=False
     # Store scheduling data in file
    chat_info = bot.get_chat(chat_id=user_id)
    username = chat_info.username
    global contact_details
    global contact_complete
    if not(user_exist):
        contact(update, "name")
        data[str(user_id)] = {
         'name':username,
         'removal_date': removal_date.isoformat(),
         'status':'hold', 'plan':option}
    else:
        if data[str(user_id)]['status'] == 'success':
            data[str(user_id)].update({'removal_date': removal_date.isoformat()})
        elif data[str(user_id)]['plan'] == option:
             message = f"You have already opted the *{data[str(user_id)]['plan']} Plan*!."
             
             bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN)
             if data[str(user_id)]['status'] == 'hold':
                bot.send_message(chat_id=user_id, text='Please wait as we will soon provide access', parse_mode=ParseMode.MARKDOWN)
             logging.info(f"user response: {message}")
        else:
             message = f"You have already opted the *{data[str(user_id)]['plan']} Plan*!\nDo you want to Cancel ❌ and Opt for new *{option} Plan*?"
             keyboard = [[InlineKeyboardButton(f"Choose {option} plan", callback_data=f"cancel,{removal_date},{option}"), InlineKeyboardButton(f"Nope", callback_data=f"new_plan.nope")]]
             reply_markup = InlineKeyboardMarkup(keyboard, one_time_keyboard=True)
             bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN,reply_markup=reply_markup)
             logging.info(f"user response: {message}")
    write_data(data)
    logging.info("Scheduled task saved to JSON file.")

# On start verifies expired memberships
def load_jobs():
    data = read_data()
    for user_id, job_data in data.items():
        removal_date = datetime.fromisoformat(job_data['removal_date'])
        if removal_date < datetime.now():
            job_data = {'user_id': int(user_id)}
            remove_user(context=job_data)

def main():
    
    # Set up dispatcher and job queue
    updater = telegram.ext.Updater(TOKEN, use_context=True)
    updater.dispatcher.add_handler(CallbackQueryHandler(button_click_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_contact))
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(telegram.ext.CommandHandler('help', help))
    dp.add_handler(telegram.ext.CommandHandler('subscribe', subscribe))
    # dp.add_handler(telegram.ext.CommandHandler('redeem', redeem))

    # Load scheduled removal jobs
    load_jobs()

    # Start the bot
    updater.start_polling()
    logging.info("Bot started")
    updater.idle()

if __name__ == '__main__':
    main()
