from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater
import csv, json
from datetime import datetime, timedelta

app = Flask(__name__)
auth = HTTPBasicAuth()

json_data = None
recommendation_data = None
filename = "/home/ubuntu/python-scripts/csv/recommendation.csv"
users_file = "/home/ubuntu/MembershipBot/schedule.json"

with open('/home/ubuntu/python-scripts/secret.json', 'r') as f:
    secret = json.load(f)
bot_token = secret['membership_bot_token']
group_id = secret['chat_id']
bot = telegram.Bot(bot_token)
updater = Updater(bot=bot, use_context=True)

def channel_invite_button(user_id, plan):
            expire_date=datetime.now() + timedelta(hours=12)
            channel_link = bot.create_chat_invite_link(group_id, member_limit=1, expire_date=expire_date,)
            keyboard = [[InlineKeyboardButton('Join Channel', url=str(channel_link.invite_link))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"🚀 Thank you for choosing our {plan} plan!\n\n⏳ Hurry, the channel link expires in 12 hours!"
            bot.send_message(user_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN ,reply_markup=reply_markup)

@auth.verify_password
def verify_password(username, password):
    if username in secret and secret[username] == password:
        return username
    return None

def json_file_reader(filename):
    try:
        with open(filename, 'r') as jsonfile:
            data = json.load(jsonfile)
            return data
    except Exception as e:
        print(f"File problem in {filename}", e)

def write_data(data, users_file):
    with open(users_file, 'w') as f:
        json.dump(data, f)

def read_recommendation_file(filename):
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            recommendation_data = list(reader)
            return recommendation_data
    except Exception as e:
        print(f"File problem in {filename}", e)

def append_messageid(json_data):
    try:
        nsecode = json_data['nsecode']
        price = json_data['price']
        date = json_data['date'].split("T")[0]
        date = datetime.strptime(date, "%Y-%m-%d")
        date = date.strftime("%d/%b/%Y")
        message_id = json_data['message_id']
        recommendation_data = read_recommendation_file(filename)
        is_nsecode_present = False
        for row in recommendation_data:
            if row[1] == nsecode:
                row_date = datetime.strptime(row[3].split(" ")[0], "%Y-%m-%d").strftime("%d/%b/%Y")
                if row_date == date:
                    is_nsecode_present = True
                    row[4] = message_id
                    break
        if not(is_nsecode_present):
            return jsonify({"status":"Data not found"}), 404
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(recommendation_data)
            return jsonify({"success":"ok"})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400
    
def append_list(json_data):
    try:
        nsecode = json_data['nsecode']
        price = json_data['price']
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        message_id = json_data['message_id']
        recommendation_data = read_recommendation_file(filename)
        if(len(recommendation_data) == 0):
            return jsonify({"status":"Data not found"}), 404
        post_id = int(recommendation_data[len(recommendation_data)-1][0]) + 1
        recommendation_data.append([post_id,nsecode,price,date,message_id ])
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(recommendation_data)
            return jsonify({"success":"ok"})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400
    
@app.route('/update/recommendation', methods=['POST'])
@auth.login_required 
def update_recommendation():
    try:
        json_data = request.get_json()
        if not json_data or not set(json_data.keys()) == {'nsecode', 'price', 'date', 'message_id'}:
            return jsonify({'error': 'Invalid JSON format'}), 400
        status = append_messageid(json_data)
        return status
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400
    
@app.route('/update/price_recommendation', methods=['POST'])
@auth.login_required 
def update_price_recommendation():
    try:
        json_data = request.get_json()
        if not json_data or not set(json_data.keys()) == {'nsecode', 'price', 'message_id'}:
            return jsonify({'error': 'Invalid JSON format'}), 400
        status = append_list(json_data)
        return status
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400

@app.route("/channel/getdetails", methods=['GET'])
@auth.login_required 
def get_channel_details():
    try:
        user_details = json_file_reader(users_file)
        return jsonify(user_details)
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400

@app.route("/channel/update/access/active/<user_id>", methods=['GET'])
@auth.login_required 
def update_channel_access_active(user_id):
        try:
            user_id = int(user_id)
            user_data = json_file_reader(users_file)
            user_data[str(user_id)].update({'status':'active'})
            write_data(user_data, users_file)
            plan = user_data[str(user_id)]['plan']
            channel_invite_button(user_id, plan)
            user_data = json_file_reader(users_file)
            return jsonify(user_data[str(user_id)])
        except:
            return jsonify({'error': 'Invalid user details'}), 400

@app.route("/channel/update/access/hold/<user_id>", methods=['GET'])
@auth.login_required 
def update_channel_access_hold(user_id):
        try:
            user_id = int(user_id)
            user_data = json_file_reader(users_file)
            user_data[str(user_id)].update({'status':'hold'})
            write_data(user_data, users_file)
            plan = user_data[str(user_id)]['plan']
            user_data = json_file_reader(users_file,plan)
            return jsonify(user_data[str(user_id)])
        except:
            return jsonify({'error': 'Invalid user details'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'unauthorized access'}), 401

@app.route('/health')
def get_data():
    data = {'status': 'OK'}
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
