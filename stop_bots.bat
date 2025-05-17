@echo off
echo 停止所有 Telegram 機器人...

taskkill /FI "WINDOWTITLE eq *bot.py*" /F
taskkill /FI "COMMANDLINE eq *bot.py*" /F

echo 所有機器人已停止。 