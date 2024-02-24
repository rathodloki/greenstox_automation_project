import os, time, json
import subprocess

secrets = {}
secret_file = os.getenv("SECRET_FILE")
with open(secret_file, 'r') as file:
    secrets = json.load(file)

def run_file(file_path):
    subprocess.run(["python", file_path])

def check_csv_exists(csv_path):
    return os.path.exists(csv_path)

def remove_csv(csv_path):
    if os.path.exists(csv_path):
        os.remove(csv_path)
        time.sleep(1) 
        print(f"Removed existing CSV file: {csv_path}")

def main():
    file_paths = ["chartlink_data.py", "filtered_stocks_data.py", "broadcast_data.py"]
    csv_paths = ["csv/chartink_result.csv", "csv/filtered_stocks.csv", "csv/broadcast.csv"]
    # Remove existing CSV files
    for csv_path in csv_paths:
        remove_csv(csv_path)

    for file_path, csv_path in zip(file_paths, csv_paths):
        if not check_csv_exists(csv_path):
            run_file(file_path)
            if check_csv_exists(csv_path):
                print(f"{csv_path} created successfully.")
            else:
                print(f"Error: {csv_path} not created. Check {file_path} for errors.")
                break
        else:
            print(f"Skipping {file_path} as {csv_path} already exists.")

if __name__ == "__main__":
    main()
