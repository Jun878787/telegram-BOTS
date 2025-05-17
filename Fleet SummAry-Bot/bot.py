#!/usr/bin/env python
# -*- coding: utf-8 -*-


import telebot
import re
from datetime import datetime, timedelta
import json
import os
import logging

# 從環境變數獲取配置
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    # 如果環境變數沒有設置，可以使用默認值（僅用於測試）
    TOKEN = "7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw"
    print("警告：未設置TELEGRAM_BOT_TOKEN環境變數，使用硬編碼的token")

# 初始化機器人
bot = telebot.TeleBot(TOKEN)

# 簡化版本的 config 和 accounting 類
class Config:
    def __init__(self):
        self.data = {}
        
class Accounting:
    def __init__(self):
        self.data = {}

# 創建實例
config = Config()
accounting = Accounting()

# 設置日誌記錄
def setup_logging():
    """設置日誌記錄"""
    # 創建logs目錄（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 設置日誌文件名（使用當前日期）
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = f'logs/bot_log_{current_date}.txt'
    
    # 配置日誌記錄器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('BotLogger')

# 創建日誌記錄器
logger = setup_logging()

def log_message(message, action_type="一般消息"):
    """記錄消息到日誌"""
    try:
        # 獲取基本信息
        user_id = message.from_user.id
        username = message.from_user.username or "未知用戶名"
        chat_id = message.chat.id
        chat_title = message.chat.title if message.chat.title else "私聊"
        message_text = message.text or "無文字內容"
        
        # 格式化日誌消息
        log_text = f"""
操作類型: {action_type}
用戶ID: {user_id}
用戶名: {username}
群組ID: {chat_id}
群組名: {chat_title}
消息內容: {message_text}
------------------------"""
        
        # 記錄到日誌
        logger.info(log_text)
    except Exception as e:
        logger.error(f"記錄消息時發生錯誤：{str(e)}")

# 創建鍵盤按鈕
def create_keyboard():
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton('📜歷史帳單'),
        KeyboardButton('👀使用說明'),
        KeyboardButton('📝群組規章')
    )
    keyboard.row(
        KeyboardButton('🛠️修復機器人'),
        KeyboardButton('🔧群管功能')
    )
    return keyboard

# 基本命令處理
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "車隊總表機器人已啟動!")
    
@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.reply_to(message, "車隊總表機器人幫助指令")

# 啟動機器人
def main():
    print("啟動車隊總表機器人...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"發生錯誤: {e}")
        
if __name__ == "__main__":
    main()