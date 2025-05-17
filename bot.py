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
BOT_TYPE = os.environ.get("BOT_TYPE", "fleet-accounting")  # 機器人類型：fleet-accounting, pm1, pm2

def start_command(update, context):
    """處理起始命令"""
    if BOT_TYPE == "fleet-accounting":
        update.message.reply_text('車隊總帳機器人已啟動！使用 /acc_help 查看可用命令。')
    elif BOT_TYPE == "pm1":
        update.message.reply_text('業績管家機器人1已啟動！使用 /pm1_help 查看可用命令。')
    elif BOT_TYPE == "pm2":
        update.message.reply_text('業績管家機器人2已啟動！使用 /pm2_help 查看可用命令。')

def help_command(update, context):
    """處理幫助命令"""
    if BOT_TYPE == "fleet-accounting":
        help_text = """
車隊總帳機器人指令清單:
/acc_start - 啟動機器人
/acc_help - 顯示此幫助信息
/acc_status - 顯示機器人狀態
        """
    elif BOT_TYPE == "pm1":
        help_text = """
業績管家機器人1指令清單:
/pm1_start - 啟動機器人
/pm1_help - 顯示此幫助信息
/pm1_status - 顯示機器人狀態
        """
    elif BOT_TYPE == "pm2":
        help_text = """
業績管家機器人2指令清單:
/pm2_start - 啟動機器人
/pm2_help - 顯示此幫助信息
/pm2_status - 顯示機器人狀態
        """
    else:
        help_text = "未知機器人類型，請檢查環境變數設置。"
    
    update.message.reply_text(help_text)

def status_command(update, context):
    """處理狀態命令"""
    current_time = datetime.datetime.now(pytz.timezone(TZ))
    uptime = f"{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    
    if BOT_TYPE == "fleet-accounting":
        status_text = f"車隊總帳機器人正在運行\n當前時間: {uptime}"
    elif BOT_TYPE == "pm1":
        status_text = f"業績管家機器人1正在運行\n當前時間: {uptime}"
    elif BOT_TYPE == "pm2":
        status_text = f"業績管家機器人2正在運行\n當前時間: {uptime}"
    else:
        status_text = f"未知機器人類型\n當前時間: {uptime}"
    
    update.message.reply_text(status_text)

def handle_message(update, context):
    """處理普通消息"""
    text = update.message.text
    
    # 根據機器人類型過濾消息
    if BOT_TYPE == "fleet-accounting" and (text.startswith("車隊:") or text.startswith("總帳:")):
        update.message.reply_text(f"收到消息：{text}")
    elif BOT_TYPE == "pm1" and (text.startswith("業績1:") or text.startswith("管家1:")):
        update.message.reply_text(f"收到消息：{text}")
    elif BOT_TYPE == "pm2" and (text.startswith("業績2:") or text.startswith("管家2:")):
        update.message.reply_text(f"收到消息：{text}")

def main():
    """啟動機器人"""
    if not TOKEN:
        logger.error("未設置 TELEGRAM_BOT_TOKEN 環境變數")
        sys.exit(1)
    
    # 日誌輸出機器人類型
    logger.info(f"啟動機器人類型: {BOT_TYPE}")
    
    # 創建更新器
    updater = Updater(TOKEN, use_context=True)
    
    # 獲取調度器註冊處理器
    dp = updater.dispatcher
    
    # 根據機器人類型註冊不同的命令處理器
    if BOT_TYPE == "fleet-accounting":
        dp.add_handler(CommandHandler("acc_start", start_command))
        dp.add_handler(CommandHandler("acc_help", help_command))
        dp.add_handler(CommandHandler("acc_status", status_command))
        logger.info("已註冊車隊總帳機器人命令")
    elif BOT_TYPE == "pm1":
        dp.add_handler(CommandHandler("pm1_start", start_command))
        dp.add_handler(CommandHandler("pm1_help", help_command))
        dp.add_handler(CommandHandler("pm1_status", status_command))
        logger.info("已註冊業績管家機器人1命令")
    elif BOT_TYPE == "pm2":
        dp.add_handler(CommandHandler("pm2_start", start_command))
        dp.add_handler(CommandHandler("pm2_help", help_command))
        dp.add_handler(CommandHandler("pm2_status", status_command))
        logger.info("已註冊業績管家機器人2命令")
    else:
        logger.warning(f"未知機器人類型: {BOT_TYPE}，將使用預設命令")
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("status", status_command))
    
    # 註冊消息處理器
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # 啟動機器人
    if os.environ.get("RAILWAY_STATIC_URL"):
        # Railway 環境下使用 webhook
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN,
                              webhook_url=f"{os.environ.get('RAILWAY_STATIC_URL')}/{TOKEN}")
        logger.info(f"機器人以webhook模式啟動在端口: {PORT}")
    else:
        # 本地環境下使用輪詢
        updater.start_polling()
        logger.info("機器人以輪詢模式啟動")
    
    logger.info(f"{BOT_TYPE} 機器人已完全啟動")
    
    # 運行機器人直到按Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main() 