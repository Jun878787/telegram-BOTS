#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import datetime
import pytz

# 啟用日誌
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數獲取配置
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
TZ = os.environ.get("TZ", "Asia/Taipei")

def start_command(update, context):
    """處理 /acc_start 命令"""
    update.message.reply_text('車隊總帳機器人已啟動！使用 /acc_help 查看可用命令。')

def help_command(update, context):
    """處理 /acc_help 命令"""
    help_text = """
車隊總帳機器人指令清單:
/acc_start - 啟動機器人
/acc_help - 顯示此幫助信息
/acc_status - 顯示機器人狀態
    """
    update.message.reply_text(help_text)

def status_command(update, context):
    """處理 /acc_status 命令"""
    current_time = datetime.datetime.now(pytz.timezone(TZ))
    uptime = f"{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    status_text = f"機器人正在運行\n當前時間: {uptime}"
    update.message.reply_text(status_text)

def handle_message(update, context):
    """處理普通消息"""
    text = update.message.text
    # 僅處理特定前綴的消息
    if text.startswith("車隊:") or text.startswith("總帳:"):
        update.message.reply_text(f"收到消息：{text}")

def main():
    """啟動機器人"""
    if not TOKEN:
        logger.error("未設置 TELEGRAM_BOT_TOKEN 環境變數")
        sys.exit(1)
        
    # 創建更新器
    updater = Updater(TOKEN, use_context=True)
    
    # 獲取調度器註冊處理器
    dp = updater.dispatcher
    
    # 註冊命令處理器
    dp.add_handler(CommandHandler("acc_start", start_command))
    dp.add_handler(CommandHandler("acc_help", help_command))
    dp.add_handler(CommandHandler("acc_status", status_command))
    
    # 註冊消息處理器
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # 啟動機器人
    if os.environ.get("RAILWAY_STATIC_URL"):
        # Railway 環境下使用 webhook
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN,
                              webhook_url=f"{os.environ.get('RAILWAY_STATIC_URL')}/{TOKEN}")
    else:
        # 本地環境下使用輪詢
        updater.start_polling()
    
    logger.info("車隊總帳機器人已啟動")
    
    # 運行機器人直到按Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main() 