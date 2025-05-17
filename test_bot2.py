#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import telegram
import time
import datetime

# Write to file to ensure script execution
with open("bot_test_log.txt", "w") as f:
    f.write("Test started at: {}\n".format(datetime.datetime.now()))
    f.write("Python version: {}\n".format(sys.version))
    f.write("Current directory: {}\n".format(os.getcwd()))
    
    try:
        # Token for the first bot
        TOKEN = "7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg"
        TARGET_GROUP_ID = "-1002557176274"
        
        f.write("Connecting to Telegram bot (Token: {}...)\n".format(TOKEN[:5]))
        bot = telegram.Bot(token=TOKEN)
        f.write("Bot initialized successfully\n")
        
        user = bot.get_me()
        f.write("Bot info: {} (@{})\n".format(user.first_name, user.username))
        
        f.write("Sending test message to group {}\n".format(TARGET_GROUP_ID))
        message = bot.send_message(
            chat_id=TARGET_GROUP_ID,
            text="This is a test message to confirm the bot is running correctly."
        )
        f.write("Message sent, ID: {}\n".format(message.message_id))
        f.write("Bot test successful!\n")
        
    except Exception as e:
        f.write("Error: {}\n".format(str(e)))
        f.write("Error type: {}\n".format(type(e)))
        
    f.write("Test completed\n") 