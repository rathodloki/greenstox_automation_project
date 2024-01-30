import pandas as pd
import sys, json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from telethon import TelegramClient

with open('secret.json', 'r') as file:
    secrets = json.load(file)

api_id = secrets['api_id']
api_hash = secrets['api_hash']
chat_id = secrets['chat_id']
bot_name = '@chartbot_telegrambot'
df = pd.read_csv("csv/recommendation.csv")
current_month = datetime.today().month
df["day"] = pd.to_datetime(df["date"]).dt.day
filtered_df = df[pd.to_datetime(df["date"]).dt.month == current_month]
filtered_df["day"] = pd.to_datetime(filtered_df["date"]).dt.day
return_data = pd.DataFrame(columns=["stock", "returns", "duration"])

table_image_path = 'image/table_image.png'
template_path = 'image/stock_template.png'

def get_filtered_data(dataframe):
    grouped = dataframe.groupby("nsecode")
    sorted_groups = grouped.apply(lambda g: g.sort_values(by="post_id", ascending=True))
    sorted_groups = df.reset_index(drop=True)
    nsecode_counts = sorted_groups['nsecode'].value_counts()
    filtered_df = sorted_groups.groupby('nsecode').filter(lambda x: nsecode_counts[x.name] > 1)
    grouped = filtered_df.groupby("nsecode")
    sorted_groups = grouped.apply(lambda g: g.sort_values(by="post_id", ascending=True))
    return sorted_groups

def calculate_returns(data):
    global return_data
    for row in data.index.get_level_values('nsecode').unique():
        stock_data = data[data['nsecode'] == row]
        initial_data = stock_data[['price','date']].iloc[0]
        final_data = stock_data[['price','date']].iloc[-1]
        price_increase = final_data['price'] - initial_data['price']
        percentage_change = (price_increase / initial_data['price']) * 100
        initial_date = pd.to_datetime(initial_data['date'])
        final_date = pd.to_datetime(final_data['date'])
        duration = final_date - initial_date
        return_data = pd.concat([return_data, pd.DataFrame([[row, percentage_change, duration.days]], columns=["stock", "returns", "duration"])], ignore_index=True)

def create_dataframe_image(df, image_path=table_image_path):
    image_width = 1000
    cell_width = int(image_width / len(df.columns))
    cell_height = int(1000 / (len(df) + 1))  # Distribute the height evenly
    font_size = min(cell_width, cell_height) // 3  # Adjust font size based on cell size
    bold_font = ImageFont.truetype("fonts/Arial_Bold.ttf", 45)
    font = ImageFont.truetype("fonts/Arial.ttf", font_size)
    image_height = (len(df) + 1) * cell_height
    image = Image.new('RGB', (image_width, image_height), '#000')
    draw = ImageDraw.Draw(image)

    for i, column in enumerate(df.columns):
        draw.rectangle([(i * cell_width, 0), ((i + 1) * cell_width, cell_height)], outline='#D8D8D8', width=2)
        draw.text((i * cell_width + 50, 20), column, font=bold_font, fill='#F0F2F5')
        draw.text((910, 30), "(days)", font=font, fill='#F0F2F5')

    for i, (_, row) in enumerate(df.iterrows()):
        for j, value in enumerate(row):
            draw.rectangle([(j * cell_width, (i + 1) * cell_height),
                            ((j + 1) * cell_width, (i + 2) * cell_height)],
                           outline='#D8D8D8', width=2)
            if j == 1:
                if '+' in value and '+0.00' not in value:
                    draw.text((j * cell_width + 50, (i + 1) * cell_height + 50), str(value), font=font, fill='#4CAF50')
                elif '-' in value:
                    draw.text((j * cell_width + 50, (i + 1) * cell_height + 50), str(value), font=font, fill='#F44336')
                else:
                    if '0.00' in value :
                        value = '0.00'
                    draw.text((j * cell_width + 100, (i + 1) * cell_height + 50), str(value), font=font, fill='#F0F2F5')
            else:
             draw.text((j * cell_width + 50, (i + 1) * cell_height + 50), str(value), font=font, fill='#F0F2F5')
    image.save(image_path)

def add_to_template(template_path, data_type):
    template = Image.open(template_path)
    df_image_path = table_image_path
    df_image = Image.open(df_image_path)
    position = (94, 123)
    resize_factor = 0.8
    df_image = df_image.resize((int(df_image.width * resize_factor), int(df_image.height * resize_factor)))
    template.paste(df_image, position)
    draw = ImageDraw.Draw(template)
    current_date = datetime.now().strftime("%b %Y")
    if data_type == 'first_half':
        header_text = str(current_date + " 1st half Report").upper()
    else: 
        header_text = str(current_date + " 2nd half Report").upper()
    font_size = 50
    font = ImageFont.truetype("/Users/lokendar/Library/Fonts/Arial_Bold.ttf", font_size)
    draw.text((140,40), str(header_text), font=font, fill='#F0F2F5')
    result_image_path = 'image/top10stocks.png'
    template.save(result_image_path)

async def send_image_to_telegram():
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start()
    await client.send_file(chat_id, "image/top10stocks.png", caption='Price volume action based highly accurate recommendations 📈🔍💹.')
    await client.disconnect()
def process_data(data_type):
    if data_type == 'first_half':
        df_first_half = filtered_df[filtered_df["day"] <= 15]
        data = get_filtered_data(df_first_half)
        print("Processing first half data")
        calculate_returns(data)
        top_10_returns = (
                        return_data.nlargest(10, "returns")
                        .reset_index(drop=True)
                        .rename_axis(None, axis=1)
                        .rename(columns=lambda x: x.capitalize())
                        )   
        top_10_returns["Returns"] = top_10_returns["Returns"].astype(float).apply("{:+.2f}%".format)
        create_dataframe_image(top_10_returns, table_image_path)
        add_to_template(template_path, data_type)
    elif data_type == 'second_half':
        df_second_half = filtered_df[filtered_df["day"] > 15]
        data = get_filtered_data(df_second_half)
        print("Processing second half data")
        calculate_returns(data)
        top_10_returns = (
                        return_data.nlargest(10, "returns")
                        .reset_index(drop=True)
                        .rename_axis(None, axis=1)
                        .rename(columns=lambda x: x.capitalize())
                        )   
        top_10_returns["Returns"] = top_10_returns["Returns"].astype(float).apply("{:+.2f}%".format)
        create_dataframe_image(top_10_returns, table_image_path)
        add_to_template(template_path, data_type)
    else:
        print("Invalid data type. Please use 'first_half' or 'second_half'.")

    
async def main(): 
    if len(sys.argv) != 2:
        print("Usage: python main.py <data_type>")
    else:
        data_type = sys.argv[1]
        process_data(data_type)
        await send_image_to_telegram()  

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
