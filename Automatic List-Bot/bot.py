#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import datetime
import pytz

# 嘗試從 dotenv 加載環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 調試輸出
print("腳本啟動 - 調試輸出")
print(f"當前路徑: {os.getcwd()}")

# 啟用日誌
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數獲取配置
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    TOKEN = "7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg"
    print("警告：未設置TELEGRAM_BOT_TOKEN環境變數，使用硬編碼的token")

PORT = int(os.environ.get("PORT", 8080))
TZ = os.environ.get("TZ", "Asia/Taipei")

print(f"TOKEN: {'已設置' if TOKEN else '未設置'}")
print(f"PORT: {PORT}")
print(f"TZ: {TZ}")

def start_command(update, context):
    """處理 /list_start 命令"""
    update.message.reply_text('格式化列表機器人已啟動！使用 /list_help 查看可用命令。')

def help_command(update, context):
    """處理 /list_help 命令"""
    help_text = """
格式化列表機器人指令清單:
/list_start - 啟動機器人
/list_help - 顯示此幫助信息
/list_status - 顯示機器人狀態
    """
    update.message.reply_text(help_text)

def status_command(update, context):
    """處理 /list_status 命令"""
    current_time = datetime.datetime.now(pytz.timezone(TZ))
    uptime = f"{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    status_text = f"機器人正在運行\n當前時間: {uptime}"
    update.message.reply_text(status_text)

def handle_message(update, context):
    """處理普通消息"""
    text = update.message.text
    # 僅處理特定前綴的消息
    if text.startswith("列表:") or text.startswith("格式:"):
        update.message.reply_text(f"收到消息：{text}")

def main():
    """啟動機器人"""
    if not TOKEN:
        logger.error("未設置 TELEGRAM_BOT_TOKEN 環境變數")
        print("錯誤: 未設置 TELEGRAM_BOT_TOKEN 環境變數")
        sys.exit(1)
        
    print("正在創建Updater...")
    # 創建更新器
    updater = Updater(TOKEN, use_context=True)
    
    print("正在配置處理器...")
    # 獲取調度器註冊處理器
    dp = updater.dispatcher
    
    # 註冊命令處理器
    dp.add_handler(CommandHandler("list_start", start_command))
    dp.add_handler(CommandHandler("list_help", help_command))
    dp.add_handler(CommandHandler("list_status", status_command))
    
    # 註冊消息處理器
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    print("正在啟動機器人...")
    # 啟動機器人
    if os.environ.get("RAILWAY_STATIC_URL"):
        # Railway 環境下使用 webhook
        print(f"以webhook模式啟動，PORT: {PORT}")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN,
                              webhook_url=f"{os.environ.get('RAILWAY_STATIC_URL')}/{TOKEN}")
    else:
        # 本地環境下使用輪詢
        print("以輪詢模式啟動")
        updater.start_polling()
    
    print("格式化列表機器人已啟動")
    logger.info("格式化列表機器人已啟動")
    
    # 運行機器人直到按Ctrl-C
    updater.idle()

if __name__ == '__main__':
    try:
        print("開始執行main函數")
        main()
    except Exception as e:
        print(f"發生異常: {e}")
        logger.error(f"發生異常: {e}")
        sys.exit(1) 