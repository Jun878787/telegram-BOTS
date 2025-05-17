@echo off
echo 啟動所有機器人...

:: 啟動 Automatic List-Bot
start cmd /k "cd Automatic List-Bot && set TELEGRAM_BOT_TOKEN=7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg && python bot.py"

:: 啟動 Fleet SummAry-Bot
start cmd /k "cd Fleet SummAry-Bot && set TELEGRAM_BOT_TOKEN=7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw && python bot.py"

:: 啟動 Performance General List-Bot
start cmd /k "cd Performance General List-Bot && set TELEGRAM_BOT_TOKEN=7582678588:AAGrU4u06xT8qP-t0L4TZE0BmJf9N44L2Hg && python bot.py"

echo 所有機器人已啟動！
echo 關閉此窗口不會停止機器人。使用 stop_bots.bat 來停止所有機器人。 