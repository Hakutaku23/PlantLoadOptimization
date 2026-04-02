#!/bin/bash

source /etc/profile

restart_service() {
    echo "Restarting FastAPI service..."
    cd /app/server/
    nohup python3 main.py > /dev/null 2>&1 &
    echo "FastAPI service restarted"
    cd /app
}

stop_service() {
     if ps -ef | grep -v grep | grep -q "main.py"; then
        echo "Stopping FastAPI service..."
        pgrep -f "main.py" | xargs -r kill -9
        echo "FastAPI service stopped."
    else
        echo "FastAPI service is not running."
    fi
}

echo "Check FastAPI Server"
echo "© 2023-2024 PSELAB APP Restart Server Script"
echo "Powered By PSELAB CHONGQING CHINA"

check_service() {
    if ps -ef | grep -v grep | grep -q "main.py"; then
        echo "FastAPI service is running..."
    else
        echo "FastAPI service is not running"
        restart_service
    fi
}

stop_service
restart_service