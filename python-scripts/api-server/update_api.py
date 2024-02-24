from flask import Flask, jsonify, request, Response
from flask_httpauth import HTTPBasicAuth
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater
import csv, json, telegram, os
from datetime import datetime, timedelta

app = Flask(__name__)
auth = HTTPBasicAuth()

json_data = None
recommendation_data = None
secret_file = os.getenv("SECRET_FILE")

with open(secret_file, 'r') as file:
    secret = json.load(file)

users_file = secret['home_dir']+"/MembershipBot/schedule.json"
bot_token = secret['membership_bot']['token']
group_id = secret['python_scripts']['chat_id']
recommendation_csv = secret['python_scripts']['csv_dir']+"/recommendation.csv"
bot = telegram.Bot(bot_token)
updater = Updater(bot=bot, use_context=True)
def channel_invite_button(user_id, plan):
            expire_date=datetime.now() + timedelta(hours=12)
            channel_link = bot.create_chat_invite_link(group_id, member_limit=1, expire_date=expire_date,)
            keyboard = [[InlineKeyboardButton('Join Channel', url=str(channel_link.invite_link))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"✅ Payment Processed!\n\nThank you for joining GreenStox, looking forward to deliver for your amazing trading journey with Us! ⚡\n\n⏳ Kindly join the Channel below within 12 hours! "
            print(text)
            bot.send_message(user_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN ,reply_markup=reply_markup)

@auth.verify_password
def verify_password(username, password):
    if username in secret['python_scripts'] and secret['python_scripts'][username] == password:
        return username
    return None

def json_file_reader(secret_file):
    try:
        with open(secret_file, 'r') as jsonfile:
            data = json.load(jsonfile)
            return data
    except Exception as e:
        print(f"File problem in {secret_file}", e)

def csv_file_reader(users_file):
    try:
        with open(users_file, 'r') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)
            return data
    except Exception as e:
        return jsonify({'error': 'get csv failed'}), 400

def write_data(data, users_file):
    with open(users_file, 'w') as f:
        json.dump(data, f)

def read_recommendation_file(recommendation_csv):
    try:
        print(recommendation_csv)
        with open(recommendation_csv, 'r') as csvfile:
            reader = csv.reader(csvfile)
            recommendation_data = list(reader)
            return recommendation_data
    except Exception as e:
        print(f"File problem in {recommendation_csv}", e)

def append_messageid(json_data):
    try:
        nsecode = json_data['nsecode']
        price = json_data['price']
        date = json_data['date'].split("T")[0]
        date = datetime.strptime(date, "%Y-%m-%d")
        date = date.strftime("%d/%b/%Y")
        message_id = json_data['message_id']
        recommendation_data = read_recommendation_file(recommendation_csv)
        is_nsecode_present = False
        
        for row in recommendation_data:
            if row[1] == nsecode:
                print(row[1])
                print("assa")
                row_date = datetime.strptime(row[3].split(" ")[0], "%Y-%m-%d").strftime("%d/%b/%Y")
                if row_date == date:
                    is_nsecode_present = True
                    row[4] = message_id
                    break
        if not(is_nsecode_present):
            return jsonify({"status":"Data not found"}), 404
        with open(secret_file, 'w', newline='') as csvfile:
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
        returns = json_data['returns']
        recommendation_data = read_recommendation_file(secret_file)
        if(len(recommendation_data) == 0):
            return jsonify({"status":"Data not found"}), 404
        post_id = int(recommendation_data[len(recommendation_data)-1][0]) + 1
        recommendation_data.append([post_id,nsecode,price,date,message_id,returns ])
        with open(secret_file, 'w', newline='') as csvfile:
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
        if not json_data or not set(json_data.keys()) == {'nsecode', 'price', 'date', 'message_id','returns'}:
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
        if not json_data or not set(json_data.keys()) == {'nsecode', 'price', 'message_id','returns'}:
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

@app.route("/get/recommendations", methods=['GET'])
@auth.login_required
def get_recommendations():
        try:
            users_file = "../csv/recommendation.csv"
            user_data = csv_file_reader(users_file)
            css_styles = """
                        table {
                            border-collapse: collapse;
                            width: 100%;
                            font-family: Arial, sans-serif;
                            background-color: #1f1f1f;
                            color: #fff;
                        }
                        th, td {
                            border: 1px solid #333;
                            padding: 8px;
                            text-align: left;
                        }
                        th {
                            background-color: #262626;
                        }
                        """
            table_html = f"<style>{css_styles}</style><table>\n<thead>\n<tr>"
            table_html += "".join([f"<th>{header}</th>" for header in user_data[0]])  # Add headers
            table_html += "</tr>\n</thead>\n<tbody>\n"
            for row in user_data[1:]:  # Skip the header row
                table_html += "<tr>"
                table_html += "".join([f"<td>{cell}</td>" for cell in row])
                table_html += "</tr>\n"
            table_html += "</tbody>\n</table>"
            return Response(table_html, mimetype='text/html')
        except Exception as e:
            return jsonify({'error': 'get csv failed',"error":str(e)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'unauthorized access'}), 401

@app.route("/razorpay/webhook", methods=['POST'])
def razorpay_webhook():
    data = request.json
    telegram_id = data['payload']['order']['entity']['notes']['telegram_user_id']
    print(telegram_id)
    update_channel_access_active(telegram_id)
    return jsonify(data), 200

@app.route('/health')
def get_data():
    data = {'status': 'OK'}
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
