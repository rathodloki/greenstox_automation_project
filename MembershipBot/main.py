# Code made by https://github.com/EduContin
# This script restarts bot.py every X amount of time to verify if memberships expired, and if so, user gets bannd/kicked.
# More often restarts = more often bot verifies expired memberships
# Recommended amount = 4-12 hours

import subprocess
import time, datetime
import fcntl

lock_file = '/home/ubuntu/MembershipBot/tmp/membership.lck'
current_time = datetime.datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
try:
    with open(lock_file, 'x') as f:
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Acquire exclusive lock
    print("[{formatted_time}] Lock file Generated")

except IOError:    
    print(f"[{formatted_time}] MembershipBot Script already running")
    exit()


while True:
    # Open the bot.py file using the subprocess module
    bot_process = subprocess.Popen(['python', '/home/ubuntu/MembershipBot/bot.py'])
    
    # Wait for given amount of seconds
    time.sleep(43200) # That's 12 hours
    
    # Terminate the bot.py process
    bot_process.terminate()
