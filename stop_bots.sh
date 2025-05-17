#!/bin/bash

# 停止所有機器人
echo "正在停止所有機器人..."

# 從文件中讀取PID
if [ -f "bot_pids.txt" ]; then
  IFS=',' read -ra PIDS <<< $(cat bot_pids.txt)
  for pid in "${PIDS[@]}"; do
    if ps -p $pid > /dev/null; then
      kill -15 $pid
      echo "已停止進程 PID: $pid"
    else
      echo "進程 PID: $pid 已不存在"
    fi
  done
  rm bot_pids.txt
  echo "已刪除PID文件"
else
  echo "找不到PID文件，嘗試查找python進程..."
  pkill -f "python bot.py"
  echo "已嘗試停止所有python bot.py進程"
fi

echo "所有機器人已停止" 