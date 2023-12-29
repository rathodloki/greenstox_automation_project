import os, time
import subprocess

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
    file_paths = ["/home/ubuntu/python-scripts/chartlink_data.py", "/home/ubuntu/python-scripts/filtered_stocks_data.py", "/home/ubuntu/python-scripts/broadcast_data.py"]
    csv_paths = ["/home/ubuntu/python-scripts/csv/chartink_result.csv", "/home/ubuntu/python-scripts/csv/filtered_stocks.csv", "/var/www/html/broadcast.csv"]
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
