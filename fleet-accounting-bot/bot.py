#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
import time
import datetime
import pytz

try:
    # 嘗試導入 python-telegram-bot v20.x 的模塊
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram import Update
    
    # 檢查是否是 v20.x
    PTB_VERSION_20 = True
except ImportError:
    try:
        # 嘗試導入 python-telegram-bot v13.x 的模塊
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
        from telegram import Bot, Update
        
        # 設置版本標記
        PTB_VERSION_20 = False
    except ImportError as e:
        if "Filters" in str(e):
            print("錯誤：請安裝 python-telegram-bot 13.x 或 20.x 版本")
            print("執行：pip install python-telegram-bot==13.15")
            print("或： pip install python-telegram-bot==20.6")
            sys.exit(1)
        elif "imghdr" in str(e):
            print("錯誤：Python 3.13+ 不支援 imghdr 模塊")
            print("請使用 python-telegram-bot 20.x 版本")
            print("執行：pip install python-telegram-bot==20.6")
            sys.exit(1)
        else:
            raise e

# 載入環境變數
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass  # 不強制使用 dotenv

# 設置日誌記錄
if not os.path.exists('logs'):
    os.makedirs('logs')
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
log_file = f'logs/bot_log_{current_date}.txt'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 從環境變數獲取配置
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
TZ = os.environ.get("TZ", "Asia/Taipei")

# v20.x 版本的命令處理函數
async def start_command_v20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /acc_start 命令 (v20.x)"""
    await update.message.reply_text('車隊總帳機器人已啟動！使用 /acc_help 查看可用命令。')

async def help_command_v20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /acc_help 命令 (v20.x)"""
    help_text = """
車隊總帳機器人指令清單:
/acc_start - 啟動機器人
/acc_help - 顯示此幫助信息
/acc_status - 顯示機器人狀態
    """
    await update.message.reply_text(help_text)

async def status_command_v20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /acc_status 命令 (v20.x)"""
    current_time = datetime.datetime.now(pytz.timezone(TZ))
    uptime = f"{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    status_text = f"機器人正在運行\n當前時間: {uptime}"
    await update.message.reply_text(status_text)

async def handle_message_v20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理普通消息 (v20.x)"""
    text = update.message.text
    # 僅處理特定前綴的消息
    if text.startswith("車隊:") or text.startswith("總帳:"):
        await update.message.reply_text(f"收到消息：{text}")

# v13.x 版本的命令處理函數
def start_command_v13(update, context):
    """處理 /acc_start 命令 (v13.x)"""
    update.message.reply_text('車隊總帳機器人已啟動！使用 /acc_help 查看可用命令。')

def help_command_v13(update, context):
    """處理 /acc_help 命令 (v13.x)"""
    help_text = """
車隊總帳機器人指令清單:
/acc_start - 啟動機器人
/acc_help - 顯示此幫助信息
/acc_status - 顯示機器人狀態
    """
    update.message.reply_text(help_text)

def status_command_v13(update, context):
    """處理 /acc_status 命令 (v13.x)"""
    current_time = datetime.datetime.now(pytz.timezone(TZ))
    uptime = f"{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    status_text = f"機器人正在運行\n當前時間: {uptime}"
    update.message.reply_text(status_text)

def handle_message_v13(update, context):
    """處理普通消息 (v13.x)"""
    text = update.message.text
    # 僅處理特定前綴的消息
    if text.startswith("車隊:") or text.startswith("總帳:"):
        update.message.reply_text(f"收到消息：{text}")

async def main_v20():
    """啟動機器人 (v20.x)"""
    if not TOKEN:
        logger.error("未設置 TELEGRAM_BOT_TOKEN 環境變數")
        sys.exit(1)
        
    # 創建應用
    application = Application.builder().token(TOKEN).build()
    
    # 註冊命令處理器
    application.add_handler(CommandHandler("acc_start", start_command_v20))
    application.add_handler(CommandHandler("acc_help", help_command_v20))
    application.add_handler(CommandHandler("acc_status", status_command_v20))
    
    # 註冊消息處理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_v20))
    
    # 啟動機器人
    # 檢查是否在 Railway 環境中
    railway_env = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_env:
        # Railway 環境下使用 webhook
        # 包含獨特路徑以避免與其他機器人衝突
        webhook_path = f"fleet-acc-webhook-{TOKEN[-8:]}"
        webhook_url = f"{railway_env}/{webhook_path}"
        
        logger.info(f"在 Railway 環境使用 webhook 模式，webhook URL: {webhook_url}")
        await application.bot.set_webhook(url=webhook_url)
        await application.start()
    else:
        # 本地環境下使用輪詢
        logger.info("在本地環境使用輪詢模式")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
    
    logger.info("車隊總帳機器人已啟動")
    
    # 保持機器人運行
    await application.updater.idle()
 
def main_v13():
    """啟動機器人 (v13.x)"""
    if not TOKEN:
        logger.error("未設置 TELEGRAM_BOT_TOKEN 環境變數")
        sys.exit(1)
        
    # 創建更新器
    updater = Updater(TOKEN, use_context=True)
    
    # 獲取調度器註冊處理器
    dp = updater.dispatcher
    
    # 註冊命令處理器
    dp.add_handler(CommandHandler("acc_start", start_command_v13))
    dp.add_handler(CommandHandler("acc_help", help_command_v13))
    dp.add_handler(CommandHandler("acc_status", status_command_v13))
    
    # 註冊消息處理器
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message_v13))
    
    # 啟動機器人
    # 檢查是否在 Railway 環境中
    railway_env = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_env:
        # Railway 環境下使用 webhook
        # 包含獨特路徑以避免與其他機器人衝突
        webhook_path = f"fleet-acc-webhook-{TOKEN[-8:]}"
        webhook_url = f"{railway_env}/{webhook_path}"
        
        logger.info(f"在 Railway 環境使用 webhook 模式，webhook URL: {webhook_url}")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=webhook_path,
                              webhook_url=webhook_url)
    else:
        # 本地環境下使用輪詢
        logger.info("在本地環境使用輪詢模式")
        updater.start_polling(drop_pending_updates=True)
    
    logger.info("車隊總帳機器人已啟動")
    
    # 運行機器人直到按Ctrl-C
    updater.idle()

if __name__ == '__main__':
    print("====== 車隊總帳機器人啟動中 ======")
    
    if PTB_VERSION_20:
        logger.info("使用 python-telegram-bot v20.x")
        import asyncio
        asyncio.run(main_v20())
    else:
        logger.info("使用 python-telegram-bot v13.x")
        main_v13()
