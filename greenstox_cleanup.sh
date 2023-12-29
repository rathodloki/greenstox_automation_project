#!/bin/bash

# Directory containing lock files (adjust as needed)
membershipBot_lock_file="/home/ubuntu/MembershipBot/tmp/membership.lck"

if ! pgrep -if "membershipbot" > /dev/null; then
    pkill -if "membershipbot"
    echo "removing MembershipBot Lock Files"
    rm -rf ${membershipBot_lock_file}
fi


#weekend cleanuip
stock_cached_file="/home/ubuntu/python-scripts/stock.cache"
telegram_log_file="/home/ubuntu/python-scripts/logs/telegram_broadcast.log"
membership_bot_log_file="/home/ubuntu/MembershipBot/logs/membershipbot.log"
day=$(date +%u)
if [ "$day" -eq 6 ] || [ "$day" -eq 7 ]; then
	echo "cleaning stock cached at sat and sun"
	rm -rf ${stock_cached_file}
	rm -rf ${telegram_log_file}
	rm -rf ${membership_bot_log_file}
        touch ${stock_cached_file}
	rm -rf 
fi	
