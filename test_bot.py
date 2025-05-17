#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import telegram
import time
import datetime

# 直接寫入文件以確保腳本執行
with open("bot_test_log.txt", "w", encoding="utf-8") as f:
    f.write(f"測試開始時間: {datetime.datetime.now()}\n")
    f.write(f"Python版本: {sys.version}\n")
    f.write(f"當前工作目錄: {os.getcwd()}\n")
    
    try:
        # 假設使用第一個機器人的Token
        TOKEN = "7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg"
        TARGET_GROUP_ID = "-1002557176274"
        
        f.write(f"正在嘗試連接到Telegram機器人 (Token: {TOKEN[:5]}...)\n")
        bot = telegram.Bot(token=TOKEN)
        f.write("成功初始化機器人對象\n")
        
        user = bot.get_me()
        f.write(f"機器人信息: {user.first_name} (@{user.username})\n")
        
        f.write(f"嘗試發送測試消息到群組 {TARGET_GROUP_ID}\n")
        message = bot.send_message(
            chat_id=TARGET_GROUP_ID,
            text="這是一條測試消息，確認機器人是否運行正常。"
        )
        f.write(f"消息已發送，ID: {message.message_id}\n")
        f.write("機器人測試成功!\n")
        
    except Exception as e:
        f.write(f"錯誤: {str(e)}\n")
        f.write(f"錯誤類型: {type(e)}\n")
        
    f.write("測試完成\n") 