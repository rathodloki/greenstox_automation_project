from flask import Flask, jsonify, request
import csv, json
from datetime import datetime

app = Flask(__name__)

json_data = None
recommendation_data = None
filename = "/home/ubuntu/python-scripts/csv/recommendation.csv"


def update_recommend_messageid(filename):
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
        recommendation_data = update_recommend_messageid(filename)
        for row in recommendation_data:
            if row[1] == nsecode:
                row_date = datetime.strptime(row[3].split(" ")[0], "%Y-%m-%d").strftime("%d/%b/%Y")
                if row_date == date:
                    row[4] = message_id
                    break
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(recommendation_data)
            return jsonify({"success":"ok"})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400
    

@app.route('/update/recommendation', methods=['POST'])
def update_recommendation():
    try:
        json_data = request.get_json()
        if not json_data or not set(json_data.keys()) == {'nsecode', 'price', 'date', 'message_id'}:
            return jsonify({'error': 'Invalid JSON format'}), 400
        status = append_messageid(json_data)
        return status
    except Exception as e:
        return jsonify({'error': 'Invalid JSON format'}), 400
    


@app.route('/health')
def get_data():
    data = {'status': 'OK'}
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)

