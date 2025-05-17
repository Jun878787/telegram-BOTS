@echo off
echo 啟動所有 Telegram 機器人...

echo 啟動格式化列表機器人...
start cmd /k "cd Automatic List-Bot && python bot.py"

echo 啟動車隊總表機器人...
start cmd /k "cd Fleet SummAry-Bot && python bot.py"

echo 啟動群組別總表機器人...
start cmd /k "cd Performance General List-Bot && python bot.py"

echo 所有機器人已啟動！
echo 請檢查 Telegram 應用程序中的機器人是否正常響應。 