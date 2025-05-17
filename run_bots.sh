#!/bin/bash

# 啟動所有機器人
echo "正在啟動所有機器人..."

# 設置環境變數並啟動格式化列表機器人
cd "Automatic List-Bot"
export $(grep -v '^#' .env | xargs)
python bot.py &
BOT1_PID=$!
echo "格式化列表機器人已啟動，PID: $BOT1_PID"
cd ..

# 設置環境變數並啟動車隊總表機器人
cd "Fleet SummAry-Bot"
export $(grep -v '^#' .env | xargs)
python bot.py &
BOT2_PID=$!
echo "車隊總表機器人已啟動，PID: $BOT2_PID"
cd ..

# 設置環境變數並啟動組別總表機器人
cd "Performance General List-Bot"
export $(grep -v '^#' .env | xargs)
python bot.py &
BOT3_PID=$!
echo "組別總表機器人已啟動，PID: $BOT3_PID"
cd ..

# 保存進程ID
echo "$BOT1_PID,$BOT2_PID,$BOT3_PID" > bot_pids.txt
echo "所有機器人已啟動，PID已保存到 bot_pids.txt"

# 等待所有機器人進程
wait 