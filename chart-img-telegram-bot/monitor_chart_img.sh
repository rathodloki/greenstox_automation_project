#!/bin/bash

export PATH=/home/ubuntu/.local/bin:/home/ubuntu/.nvm/versions/node/v21.4.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
# Check if the first command is running
if ! ps aux | grep -v "grep" | grep "npm run server-local --ip 127.0.0.1 --port 8080" > /dev/null; then
    if lsof -i :8080 > /dev/null 2>&1; then
    pids=$(lsof -t -i :8080)
    for pid in $pids; do
    echo "Port: 8080 is not idle"
    echo "Killing process using 8080 with PID $pid"
    kill -9 $pid
    done
    fi
    echo "Command 1 (npm run server-local) is not running. Restarting..."
    nohup npm run server-local -- --ip 127.0.0.1 --port 8080 > /dev/null 2>&1 &
else
	echo "Already running (npm run server-local --ip 127.0.0.1 --port 8080)"
fi

# Check if the second command is running
if ! ps aux | grep -v "grep" | grep "npm run ngrok --port 8080 -t" > /dev/null; then
    token_session_uri=$(curl -s -H "Authorization: Bearer 2Zvr4WXK5lSqEROwWDEjZh0PBvO_6tinE8wB7toMr5DvRnsa6" -H "Ngrok-Version: 2" https://api.ngrok.com/tunnels | jq -r '.tunnels[].tunnel_session.uri' | sort -u)
    if [ -n "$token_session" ]; then
         echo "removing tunnel session"
         curl -X POST -H "Authorization: Bearer 2Zvr4WXK5lSqEROwWDEjZh0PBvO_6tinE8wB7toMr5DvRnsa6" -H "Content-Type: application/json"  -H "Ngrok-Version: 2" -d '{}'  "${token_session_uri}/stop"
    fi
    echo "Command 2 (npm run ngrok) is not running. Restarting..."
    nohup  npm run ngrok -- --port 8080 -t > /dev/null 2>&1  &
else
	echo "Already running (npm run ngrok -- --port 8080)"
fi
