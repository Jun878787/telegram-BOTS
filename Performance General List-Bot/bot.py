#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telebot
import logging
import os
import json
import re
import calendar
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sys
import subprocess
import threading
import time
import traceback
import signal
import psutil
import platform
import schedule
import logging.handlers
import requests
import uuid
from telebot import types, apihelper, util

# 定義目標群組ID（請替換成你自己的群組ID）
TARGET_GROUP_ID = -1002557176274  # 替換成你提供的ID

# 定義管理員ID列表
ADMIN_IDS = [7842840472]  # 這裡添加管理員的用戶ID，例如 [123456789, 987654321]

# 從環境變數獲取配置
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    # 如果環境變數沒有設置，可以使用默認值（僅用於測試）
    TOKEN = "7582678588:AAGrU4u06xT8qP-t0L4TZE0BmJf9N44L2Hg"
    print("警告：未設置TELEGRAM_BOT_TOKEN環境變數，使用硬編碼的token")

# 初始化機器人
bot = telebot.TeleBot(TOKEN)

# 檔案路徑
DATA_FILE = 'accounting_data.json'
USER_SETTINGS_FILE = 'user_settings.json'
EXCHANGE_RATES_FILE = 'exchange_rates.json'
PUBLIC_PRIVATE_FILE = 'funds.json'

PORT = int(os.environ.get("PORT", 8080))
TZ = os.environ.get("TZ", "Asia/Taipei")

def start_command(update, context):
    """處理 /pm1_start 命令"""
    update.message.reply_text('業績管家機器人1已啟動！使用 /pm1_help 查看可用命令。')

def help_command(update, context):
    """處理 /pm1_help 命令"""
    help_text = """
業績管家機器人1指令清單:
/pm1_start - 啟動機器人
/pm1_help - 顯示此幫助信息
/pm1_status - 顯示機器人狀態
    """
    update.message.reply_text(help_text)

def status_command(update, context):
    """處理 /pm1_status 命令"""
    current_time = datetime.datetime.now(pytz.timezone(TZ))
    uptime = f"{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    status_text = f"機器人正在運行\n當前時間: {uptime}"
    update.message.reply_text(status_text)

def handle_message(update, context):
    """處理普通消息"""
    text = update.message.text
    # 僅處理特定前綴的消息
    if text.startswith("業績1:") or text.startswith("管家1:"):
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
    dp.add_handler(CommandHandler("pm1_start", start_command))
    dp.add_handler(CommandHandler("pm1_help", help_command))
    dp.add_handler(CommandHandler("pm1_status", status_command))
    
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
    
    logger.info("業績管家機器人1已啟動")
    
    # 運行機器人直到按Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main() 



# 全局變量
RESTART_FLAG = False
BOT_START_TIME = datetime.now()
HEARTBEAT_INTERVAL = 60  # 心跳檢測間隔(秒)
MAX_ERROR_COUNT = 5  # 容許的最大連續錯誤數量
ERROR_RESET_TIME = 600  # 錯誤計數器重置時間(秒)
error_count = 0
last_error_time = None
heartbeat_thread = None

# 用户狀態字典，用於跟踪每個用户正在執行的操作
user_states = {}

# 設置日誌
def setup_logging():
    """設置日誌記錄"""
    logger = logging.getLogger('bot_logger')
    logger.setLevel(logging.INFO)
    
    # 確保日誌目錄存在
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 檔案處理器，設定每天輪替的日誌文件
    file_handler = logging.handlers.TimedRotatingFileHandler(
        'logs/bot.log',
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 同時輸出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 設定日誌格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加處理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 設定為全局 logger
    logging.root = logger
    
    print("日誌系統已設置 - 輸出到 logs/bot.log 和控制台")
    logging.info("機器人日誌系統初始化完成")
    return logger

logger = setup_logging()

# 初始化檔案
def init_files():
    try:
        logger.info("初始化檔案...")
        
        # 確保資料目錄存在
        data_dir = os.path.dirname(DATA_FILE)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"創建目錄: {data_dir}")
            
        # 創建會計資料文件
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            logger.info(f"創建檔案: {DATA_FILE}")
            
        # 創建用戶設置文件
        if not os.path.exists(USER_SETTINGS_FILE):
            with open(USER_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            logger.info(f"創建檔案: {USER_SETTINGS_FILE}")
            
        # 創建匯率文件
        if not os.path.exists(EXCHANGE_RATES_FILE):
            with open(EXCHANGE_RATES_FILE, 'w', encoding='utf-8') as f:
                json.dump({datetime.now().strftime('%Y-%m-%d'): 33.25}, f)
            logger.info(f"創建檔案: {EXCHANGE_RATES_FILE}")
            
        # 創建資金文件
        if not os.path.exists(PUBLIC_PRIVATE_FILE):
            with open(PUBLIC_PRIVATE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"public": 0, "private": 0}, f)
            logger.info(f"創建檔案: {PUBLIC_PRIVATE_FILE}")
            
        logger.info("初始化檔案完成")
    except Exception as e:
        logger.error(f"初始化檔案時發生錯誤: {str(e)}\n{traceback.format_exc()}")
        print(f"初始化檔案錯誤: {str(e)}")

# 資料操作函數
def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 使用者設定
def get_report_name(user_id):
    settings = load_data(USER_SETTINGS_FILE)
    return settings.get(str(user_id), {}).get('report_name', '總表')

def set_report_name(user_id, name):
    settings = load_data(USER_SETTINGS_FILE)
    if str(user_id) not in settings:
        settings[str(user_id)] = {}
    settings[str(user_id)]['report_name'] = name
    save_data(settings, USER_SETTINGS_FILE)

# 匯率操作
def get_rate(date=None):
    rates = load_data(EXCHANGE_RATES_FILE)
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    return rates.get(date, 33.25)

def set_rate(rate, date=None):
    rates = load_data(EXCHANGE_RATES_FILE)
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    rates[date] = float(rate)
    save_data(rates, EXCHANGE_RATES_FILE)

# 交易記錄操作
def add_transaction(user_id, date, type_currency, amount):
    data = load_data(DATA_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {}
    if date not in data[str(user_id)]:
        data[str(user_id)][date] = {"TW": 0, "CN": 0}
    
    currency = "TW" if type_currency.startswith("TW") else "CN"
    data[str(user_id)][date][currency] = amount
    save_data(data, DATA_FILE)

def delete_transaction(user_id, date, currency):
    data = load_data(DATA_FILE)
    if str(user_id) in data and date in data[str(user_id)]:
        data[str(user_id)][date][currency] = 0
        save_data(data, DATA_FILE)
        return True
    return False

# 公私桶資金操作
def update_fund(fund_type, amount):
    funds = load_data(PUBLIC_PRIVATE_FILE)
    funds[fund_type] += float(amount)
    save_data(funds, PUBLIC_PRIVATE_FILE)

# 日期解析
def parse_date(date_str):
    today = datetime.now()
    
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
        return date_str
    elif '/' in date_str:
        month, day = map(int, date_str.split('/'))
        return f"{today.year}-{month:02d}-{day:02d}"
    elif '-' in date_str and date_str.count('-') == 1:  # For MM-DD format
        month, day = map(int, date_str.split('-'))
        return f"{today.year}-{month:02d}-{day:02d}"
    elif '.' in date_str:  # For MM.DD format
        month, day = map(int, date_str.split('.'))
        return f"{today.year}-{month:02d}-{day:02d}"
    else:
        return today.strftime('%Y-%m-%d')

# 生成月報表
def generate_report(user_id, month=None, year=None):
    """生成指定月份的報表"""
    try:
        if month is None or year is None:
            now = datetime.now()
            month, year = now.month, now.year
        
        # 確保數據文件存在
        if not os.path.exists(DATA_FILE):
            logger.error(f"數據文件不存在: {DATA_FILE}")
            return "❌ 數據文件不存在，請先記錄一些交易"
            
        if not os.path.exists(EXCHANGE_RATES_FILE):
            logger.error(f"匯率文件不存在: {EXCHANGE_RATES_FILE}")
            return "❌ 匯率文件不存在，請先設置匯率"
            
        if not os.path.exists(PUBLIC_PRIVATE_FILE):
            logger.error(f"資金文件不存在: {PUBLIC_PRIVATE_FILE}")
            return "❌ 資金文件不存在，請先更新資金狀態"
        
        data = load_data(DATA_FILE)
        exchange_rates = load_data(EXCHANGE_RATES_FILE)
        funds = load_data(PUBLIC_PRIVATE_FILE)
        
        # 檢查該用戶是否有數據
        if str(user_id) not in data or not data[str(user_id)]:
            return f"📊 【{get_report_name(user_id)}】\n\n目前尚無交易記錄。\n請使用 TW+/- 或 CN+/- 指令記錄交易。"
            
        user_data = data.get(str(user_id), {})
        
        # 計算當月日期範圍
        _, last_day = calendar.monthrange(year, month)
        month_dates = [f"{year}-{month:02d}-{day:02d}" for day in range(1, last_day + 1)]
        
        # 計算總額及準備報表行
        tw_total, cn_total = 0, 0
        report_lines = []
        
        for date in month_dates:
            dt = datetime.strptime(date, '%Y-%m-%d')
            day_str = dt.strftime('%m/%d')
            weekday = dt.weekday()
            weekday_str = ('一', '二', '三', '四', '五', '六', '日')[weekday]
            
            day_data = user_data.get(date, {"TW": 0, "CN": 0})
            tw_amount = day_data.get("TW", 0)
            cn_amount = day_data.get("CN", 0)
            
            tw_total += tw_amount
            cn_total += cn_amount
            
            # 只有在有金額或是第1天/15日/末日時才顯示
            if tw_amount != 0 or cn_amount != 0 or dt.day == 1 or dt.day == 15 or dt.day == last_day:
                tw_display = f"{tw_amount:,.0f}" if tw_amount else "0"
                cn_display = f"{cn_amount:,.0f}" if cn_amount else "0"
                
                # 使用表格式格式，簡潔清晰
                line = f"<code>{day_str}({weekday_str})</code> "
                
                # 只有在有金額時才顯示金額
                if tw_amount != 0 or cn_amount != 0:
                    if tw_amount != 0:
                        line += f"<code>NT${tw_display}</code> "
                    if cn_amount != 0:
                        line += f"<code>CN¥{cn_display}</code>"
                
                report_lines.append(line.strip())
            
            # 每週末或月末添加分隔線
            if weekday == 6 or dt.day == last_day:
                report_lines.append("－－－－－－－－－－")
        
        # 更新 USDT 換算公式 - 乘以 0.01 (1%)
        tw_rate = get_rate()
        cn_rate = 4.75  # 人民幣固定匯率
        
        # 新的計算公式: 金額/匯率*0.01
        tw_usdt = (tw_total / tw_rate) * 0.01 if tw_rate else 0
        cn_usdt = (cn_total / cn_rate) * 0.01 if cn_rate else 0
        
        report_name = get_report_name(user_id)
        
        # 格式化數字
        tw_total_display = f"{tw_total:,.0f}"
        tw_usdt_display = f"{tw_usdt:.2f}"
        cn_total_display = f"{cn_total:,.0f}"
        cn_usdt_display = f"{cn_usdt:.2f}"
        
        # 公桶和私人資金顯示為整數
        public_funds = funds.get('public', 0)
        private_funds = funds.get('private', 0)
        public_funds_display = f"{public_funds:.0f}"
        private_funds_display = f"{private_funds:.0f}"
        
        # 報表頭部更新 - 使用更清晰的格式
        header = [
            f"<b>【{report_name}】</b>",
            f"<b>◉ 台幣業績</b>",
            f"<code>NT${tw_total_display}</code> → <code>USDT${tw_usdt_display}</code>",
            f"<b>◉ 人民幣業績</b>",
            f"<code>CN¥{cn_total_display}</code> → <code>USDT${cn_usdt_display}</code>",
            f"<b>◉ 資金狀態</b>",
            f"公桶: <code>USDT${public_funds_display}</code>",
            f"私人: <code>USDT${private_funds_display}</code>",
            "－－－－－－－－－－",
            f"<b>{year}年{month}月收支明細</b>"
        ]
        
        return "\n".join(header + report_lines)
    except Exception as e:
        logger.error(f"生成報表時發生錯誤: {str(e)}\n{traceback.format_exc()}")
        return f"❌ 生成報表時發生錯誤: {str(e)}"

# 清理舊數據（3個月前）
def clean_old_data():
    cutoff_date = datetime.now() - timedelta(days=90)
    
    # 清理會計資料
    data = load_data(DATA_FILE)
    for user_id in data:
        for date in list(data[user_id].keys()):
            try:
                if datetime.strptime(date, '%Y-%m-%d') < cutoff_date:
                    del data[user_id][date]
            except:
                pass
    save_data(data, DATA_FILE)
    
    # 清理匯率資料
    rates = load_data(EXCHANGE_RATES_FILE)
    for date in list(rates.keys()):
        try:
            if datetime.strptime(date, '%Y-%m-%d') < cutoff_date:
                del rates[date]
        except:
            pass
    save_data(rates, EXCHANGE_RATES_FILE)

# 創建改進後的鍵盤按鈕
def create_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton('📊查看本月報表'),
        KeyboardButton('📚歷史報表')
    )
    keyboard.row(
        KeyboardButton('💰TW'),
        KeyboardButton('💰CN'),
        KeyboardButton('📊總表')
    )
    keyboard.row(
        KeyboardButton('💵公桶'),
        KeyboardButton('💵私人'),
        KeyboardButton('⚙️群管設定')
    )
    keyboard.row(
        KeyboardButton('💱設置匯率'),
        KeyboardButton('🔧設定'),
        KeyboardButton('📋指令說明')
    )
    return keyboard

# 歷史報表鍵盤
def create_history_keyboard():
    now = datetime.now()
    keyboard = InlineKeyboardMarkup()
    
    for i in range(6):
        month_date = now.replace(day=1) - timedelta(days=1)
        month_date = month_date.replace(day=1)
        month_date = month_date.replace(month=now.month - i if now.month > i else 12 - (i - now.month))
        month_date = month_date.replace(year=now.year if now.month > i else now.year - 1)
        
        month_str = month_date.strftime('%Y-%m')
        display = month_date.strftime('%Y年%m月')
        keyboard.add(InlineKeyboardButton(display, callback_data=f"history_{month_str}"))
    
    return keyboard

# 獲取進程信息
def get_process_info():
    pid = os.getpid()
    process = psutil.Process(pid)
    
    # 獲取進程信息
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=0.1)
    
    return {
        "pid": pid,
        "cpu_percent": cpu_percent,
        "memory_usage": f"{memory_info.rss / (1024 * 1024):.2f} MB",
        "uptime": str(datetime.now() - BOT_START_TIME).split('.')[0]  # 去除微秒
    }

# 重啟機器人
def restart_bot():
    """重新啟動機器人進程"""
    global RESTART_FLAG
    RESTART_FLAG = True
    
    logger.info("準備重啟機器人...")
    print("準備重啟機器人...")
    
    # 根據操作系統選擇重啟方法
    if platform.system() == "Windows":
        logger.info("Windows系統下重啟機器人...")
        print("Windows系統下重啟機器人...")
        # 使用subprocess在Windows中啟動新進程
        subprocess.Popen([sys.executable, __file__], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        logger.info("Unix系統下重啟機器人...")
        print("Unix系統下重啟機器人...")
        # 在Unix系統中使用exec直接替換當前進程
        os.execv(sys.executable, ['python'] + sys.argv)
    
    # 設置延遲退出以確保新進程已啟動
    logger.info("延遲3秒後退出當前進程...")
    print("延遲3秒後退出當前進程...")
    timer = threading.Timer(3.0, lambda: os.kill(os.getpid(), signal.SIGTERM))
    timer.daemon = True
    timer.start()

# 心跳檢測函數
def heartbeat_task():
    """定期檢查機器人狀態，並在必要時自動重啟"""
    last_check_time = datetime.now()
    
    while True:
        try:
            current_time = datetime.now()
            # 檢查是否有發送消息的能力
            # 這裡可以嘗試向一個預設的安全頻道發送測試消息，或者只是檢查Telegram API連接
            
            # 獲取進程信息用於日誌記錄
            process_info = get_process_info()
            logger.info(f"心跳檢測: PID={process_info['pid']}, "
                       f"CPU={process_info['cpu_percent']}%, "
                       f"內存={process_info['memory_usage']}, "
                       f"運行時間={process_info['uptime']}")
            
            # 如果長時間無活動，可以考慮發送一個空的API請求以保持連接
            if (current_time - last_check_time).total_seconds() > 300:  # 每5分鐘
                try:
                    bot.get_me()  # 嘗試獲取機器人信息，檢測連接是否正常
                    last_check_time = current_time
                except Exception as e:
                    logger.error(f"心跳檢測API請求失敗: {str(e)}")
                    # 如果連續多次失敗，可以考慮重啟
                    restart_bot()
                    break
            
            # 檢查記憶體使用，如果過高則重啟
            if psutil.virtual_memory().percent > 90:  # 系統記憶體使用>90%
                logger.warning("系統記憶體使用率過高，準備重啟機器人")
                restart_bot()
                break
                
            # 檢查自身記憶體使用，如果過高則重啟
            memory_value = float(process_info['memory_usage'].split()[0])  # 轉換為浮點數
            if memory_value > 500:  # 如果使用>500MB
                logger.warning("機器人記憶體使用率過高，準備重啟機器人")
                restart_bot()
                break
            
            # 睡眠一段時間
            time.sleep(HEARTBEAT_INTERVAL)
            
        except Exception as e:
            logger.error(f"心跳檢測出錯: {str(e)}")
            time.sleep(HEARTBEAT_INTERVAL)  # 出錯也要繼續循環

# 啟動心跳檢測
def start_heartbeat():
    global heartbeat_thread
    heartbeat_thread = threading.Thread(target=heartbeat_task, daemon=True)
    heartbeat_thread.start()
    logger.info("心跳檢測線程已啟動")

# 錯誤處理裝飾器
def error_handler(func):
    """裝飾器：捕獲函數中的所有異常並執行適當處理"""
    def wrapper(*args, **kwargs):
        global error_count, last_error_time
        
        # 檢查是否需要重置錯誤計數器
        current_time = datetime.now()
        if last_error_time and (current_time - last_error_time).total_seconds() > ERROR_RESET_TIME:
            error_count = 0
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 增加錯誤計數
            error_count += 1
            last_error_time = current_time
            
            # 獲取詳細錯誤信息
            error_tb = traceback.format_exc()
            logger.error(f"錯誤 ({error_count}/{MAX_ERROR_COUNT}): {str(e)}\n{error_tb}")
            
            # 嘗試分析錯誤
            error_analysis = analyze_error(e, error_tb)
            logger.error(f"錯誤分析: {error_analysis}")
            
            # 如果是消息處理函數，嘗試回覆錯誤信息
            if len(args) > 0 and hasattr(args[0], 'chat') and hasattr(args[0], 'from_user'):
                try:
                    message = args[0]
                    error_msg = f"❌ 處理請求時發生錯誤: {str(e)}"
                    
                    # 如果是管理員，提供更詳細的錯誤信息
                    if is_admin(message.from_user.id, message.chat.id):
                        error_msg += f"\n\n🔧 錯誤分析: {error_analysis}"
                    
                    bot.reply_to(message, error_msg)
                except:
                    pass  # 如果回覆失敗，忽略
            
            # 檢查錯誤數量，如果超過閾值，重啟機器人
            if error_count >= MAX_ERROR_COUNT:
                logger.critical(f"連續錯誤次數達到{MAX_ERROR_COUNT}次，準備重啟機器人")
                try:
                    # 通知管理員
                    admin_ids = get_admin_ids()
                    for admin_id in admin_ids:
                        try:
                            bot.send_message(admin_id, 
                                            f"⚠️ 警告：機器人發生連續{MAX_ERROR_COUNT}次錯誤，即將自動重啟\n\n"
                                            f"最後錯誤: {str(e)}\n"
                                            f"錯誤分析: {error_analysis}")
                        except:
                            pass
                except:
                    pass
                
                # 重啟機器人
                restart_bot()
    
    return wrapper

# 錯誤分析函數
def analyze_error(error, traceback_text):
    """分析錯誤並提供可能的解決方案"""
    error_type = type(error).__name__
    error_msg = str(error).lower()
    
    # 網絡連接錯誤
    if error_type in ['ConnectionError', 'ReadTimeout', 'ConnectTimeout', 'HTTPError']:
        return "網絡連接問題。請檢查網絡連接或Telegram API伺服器狀態。"
    
    # API錯誤
    elif error_type == 'ApiTelegramException' or 'telegram' in error_msg:
        if 'blocked' in error_msg or 'kicked' in error_msg:
            return "機器人被用戶封鎖或踢出群組。"
        elif 'flood' in error_msg or 'too many requests' in error_msg:
            return "發送消息過於頻繁，觸發了Telegram限流機制。"
        elif 'not enough rights' in error_msg or 'permission' in error_msg:
            return "機器人缺少執行此操作的權限。"
        elif 'chat not found' in error_msg:
            return "找不到指定的聊天。用戶可能已刪除聊天或離開群組。"
        else:
            return f"Telegram API錯誤: {error_msg}"
    
    # JSON解析錯誤
    elif error_type in ['JSONDecodeError', 'ValueError'] and ('json' in error_msg or 'parsing' in error_msg):
        return "JSON解析錯誤，可能是數據文件格式錯誤。"
    
    # 文件IO錯誤
    elif error_type in ['FileNotFoundError', 'PermissionError', 'IOError']:
        return "文件操作錯誤，請檢查文件權限或磁盤空間。"
    
    # 類型錯誤
    elif error_type in ['TypeError', 'AttributeError']:
        return "程式邏輯錯誤，可能是資料結構不符合預期。"
    
    # 索引錯誤
    elif error_type in ['IndexError', 'KeyError']:
        return "訪問不存在的數據，可能是資料結構變化或資料不完整。"
    
    # 正則表達式錯誤
    elif error_type == 'RegexError' or 're' in error_msg:
        return "正則表達式匹配錯誤。"
    
    # 其他未知錯誤
    else:
        return f"未知錯誤類型: {error_type}。查看日誌獲取詳細信息。"

# 獲取所有管理員ID
def get_admin_ids():
    """獲取所有在配置裡記錄的管理員ID"""
    try:
        # 這裡應該從配置文件或數據庫中獲取管理員ID
        # 簡化起見，這裡使用一個硬編碼的列表，實際應從設置讀取
        admin_settings = load_data(USER_SETTINGS_FILE)
        admin_ids = []
        
        for user_id, settings in admin_settings.items():
            if settings.get('is_admin', False):
                admin_ids.append(int(user_id))
        
        # 如果沒有設置管理員，返回一個預設值
        if not admin_ids:
            # 使用創建者ID作為管理員（實際應從設置獲取）
            # 這個ID可以在初始設置過程中由創建者設定
            creator_id = admin_settings.get('creator_id', None)
            if creator_id:
                admin_ids.append(int(creator_id))
        
        return admin_ids
    except Exception as e:
        logger.error(f"獲取管理員ID失敗: {str(e)}")
        return []  # 返回空列表

# 處理重啟命令 - 確保這個處理器比其他處理器先註冊，提高優先級
@bot.message_handler(func=lambda message: message.text.strip() == '重啟', content_types=['text'])
@error_handler
def handle_restart_text_priority(message):
    """處理純文字「重啟」命令，功能與 /restart 相同，高優先級版本"""
    logger.info(f"收到重啟命令(高優先級處理)，發送者: {message.from_user.id}")
    print(f"收到重啟命令(高優先級處理)，發送者: {message.from_user.id}")
    
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此命令僅限管理員使用")
        return
    
    # 發送重啟提示
    restart_msg = bot.reply_to(message, "🔄 機器人即將重新啟動，請稍候...")
    
    # 發送重啟提示到目標群組（如果不是在目標群組中）
    if message.chat.id != TARGET_GROUP_ID:
        try:
            bot.send_message(TARGET_GROUP_ID, "🔄 機器人正在重新啟動，請稍候...")
        except Exception as e:
            logger.error(f"無法發送重啟通知到群組: {str(e)}")
    
    # 延遲一下確保消息發送成功
    time.sleep(2)
    
    # 記錄重啟事件
    logger.info(f"管理員 {message.from_user.id} 觸發機器人重啟")
    
    # 設置重啟標記
    with open("restart_flag.txt", "w") as f:
        f.write(str(datetime.now()))
    
    # 重啟機器人
    restart_bot()

# 獲取機器人狀態
@bot.message_handler(func=lambda message: message.text in ['狀態', '機器人狀態'])
@error_handler
def handle_status(message):
    """返回機器人當前運行狀態"""
    # 檢查是否為管理員（可選，也可以向所有用戶開放）
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此命令僅限管理員使用")
        return
    
    # 獲取進程信息
    process_info = get_process_info()
    
    # 獲取機器人版本（如果有設定）
    version = "1.0.0"  # 硬編碼的版本號，實際應從某處獲取
    
    # 格式化運行時間
    uptime = process_info['uptime']
    
    # 構建狀態消息
    status_msg = (
        f"🤖 機器人狀態報告\n\n"
        f"✅ 機器人運行中\n"
        f"📊 版本: {version}\n"
        f"⏱ 運行時間: {uptime}\n"
        f"💻 CPU使用率: {process_info['cpu_percent']}%\n"
        f"💾 記憶體使用: {process_info['memory_usage']}\n"
        f"🔢 PID: {process_info['pid']}\n"
        f"📅 啟動時間: {BOT_START_TIME.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    bot.reply_to(message, status_msg)

# 命令處理
@bot.message_handler(commands=['start'])
@error_handler
def send_welcome(message):
    init_files()
    bot.reply_to(message, "歡迎使用記帳機器人！", reply_markup=create_keyboard())
    logger.info(f"使用者 {message.from_user.username or message.from_user.id} 啟動了機器人")

# 新的按鈕處理函數
@bot.message_handler(func=lambda message: message.text in ['💰TW', '💰CN', '💵公桶', '💵私人'], content_types=['text'])
@error_handler
def handle_button_click_priority(message):
    """處理按鈕點擊，優先級版本"""
    # 原有的處理邏輯保持不變
    button_text = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 設置用户狀態，記錄當前操作類型
    operation_type = button_text.replace('💰', '').replace('💵', '')
    user_states[user_id] = {'operation': operation_type, 'chat_id': chat_id}
    
    # 根據按鈕類型提供不同的說明和提示
    if 'TW' in button_text:
        prompt = (
            "📝 <b>台幣記帳</b>\n\n"
            "請<b>回覆此訊息</b>並輸入金額：\n\n"
            "<b>今日收入格式</b>：+金額\n"
            "例如：<code>+1000</code> 或 <code>+1234.56</code>\n\n"
            "<b>今日支出格式</b>：-金額\n"
            "例如：<code>-1000</code> 或 <code>-1234.56</code>\n\n"
            "<b>指定日期格式</b>：日期 [+/-]金額\n"
            "例如：<code>5/01 +350000</code> 或 <code>5-01 -1000</code>\n\n"
            "系統會根據符號判斷這筆記錄為收入或支出。\n"
            "日期格式支援：MM/DD、MM-DD、YYYY-MM-DD"
        )
    elif 'CN' in button_text:
        prompt = (
            "📝 <b>人民幣記帳</b>\n\n"
            "請<b>回覆此訊息</b>並輸入金額：\n\n"
            "<b>收入格式</b>：+金額\n"
            "例如：<code>+1000</code> 或 <code>+1234.56</code>\n\n"
            "<b>支出格式</b>：-金額\n"
            "例如：<code>-1000</code> 或 <code>-1234.56</code>\n\n"
            "系統會根據符號判斷這筆記錄為收入或支出。"
        )
    elif '公桶' in button_text:
        prompt = (
            "📝 <b>公桶資金記帳</b>\n\n"
            "請<b>回覆此訊息</b>並輸入金額：\n\n"
            "<b>增加格式</b>：+金額\n"
            "例如：<code>+100</code> 或 <code>+123.45</code>\n\n"
            "<b>減少格式</b>：-金額\n"
            "例如：<code>-100</code> 或 <code>-123.45</code>\n\n"
            "系統會根據符號判斷是增加或減少公桶資金。"
        )
    elif '私人' in button_text:
        prompt = (
            "📝 <b>私人資金記帳</b>\n\n"
            "請<b>回覆此訊息</b>並輸入金額：\n\n"
            "<b>增加格式</b>：+金額\n"
            "例如：<code>+100</code> 或 <code>+123.45</code>\n\n"
            "<b>減少格式</b>：-金額\n"
            "例如：<code>-100</code> 或 <code>-123.45</code>\n\n"
            "系統會根據符號判斷是增加或減少私人資金。"
        )
    
    # 發送提示訊息，使用HTML格式增強可讀性
    # 儲存此訊息ID以便後續檢查是否為對此訊息的回覆
    sent_msg = bot.send_message(chat_id, prompt, parse_mode='HTML')
    user_states[user_id]['prompt_msg_id'] = sent_msg.message_id

# 處理回覆中的金額輸入
@bot.message_handler(func=lambda message: message.reply_to_message is not None and 
                                          message.from_user.id in user_states and 
                                          user_states[message.from_user.id].get('prompt_msg_id') == message.reply_to_message.message_id and
                                          (re.match(r'^[+\-]\d+(\.\d+)?$', message.text) or 
                                           re.match(r'^([0-9/\-\.]+)\s+[+\-]\d+(\.\d+)?$', message.text)))
@error_handler
def handle_reply_amount_input(message):
    """處理用戶在回覆中輸入的金額"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 檢查用戶是否處於輸入金額的狀態
    if user_id not in user_states:
        return
    
    # 獲取操作類型
    operation = user_states[user_id].get('operation')
    
    # 檢查是否為日期加金額格式
    date_amount_match = re.match(r'^([0-9/\-\.]+)\s+([+\-])(\d+(\.\d+)?)$', message.text)
    
    if date_amount_match and operation in ['TW', 'CN']:
        # 處理日期 +/-金額 格式
        date_str = date_amount_match.group(1)
        is_positive = date_amount_match.group(2) == '+'
        amount = float(date_amount_match.group(3))
        
        # 如果是負數，使金額為負
        if not is_positive:
            amount = -amount
        
        # 轉換日期格式
        date = parse_date(date_str)
        date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
        
        # 根據操作類型記錄交易
        try:
            if operation == 'TW':
                add_transaction(user_id, date, 'TW', amount)
                if amount > 0:
                    response = f"✅ 已記錄 {date_display} 的台幣收入：NT${amount:,.0f}"
                else:
                    response = f"✅ 已記錄 {date_display} 的台幣支出：NT${-amount:,.0f}"
            elif operation == 'CN':
                add_transaction(user_id, date, 'CN', amount)
                if amount > 0:
                    response = f"✅ 已記錄 {date_display} 的人民幣收入：¥{amount:,.0f}"
                else:
                    response = f"✅ 已記錄 {date_display} 的人民幣支出：¥{-amount:,.0f}"
            
            # 發送回覆
            bot.reply_to(message, response)
            
            # 操作完成後，清除用戶狀態
            del user_states[user_id]
            
            # 記錄操作日誌
            logger.info(f"用戶 {message.from_user.username or user_id} 執行 {operation} 操作，日期：{date_display}，金額：{amount}")
            
            return
        except Exception as e:
            bot.reply_to(message, f"❌ 處理日期與金額時出錯：{str(e)}")
            logger.error(f"處理日期與金額輸入出錯: {str(e)}")
            # 出錯時也清除用戶狀態
            del user_states[user_id]
            return
    
    # 處理純金額格式（原有功能）
    try:
        # 判斷是收入還是支出
        is_positive = message.text.startswith('+')
        # 提取純數字金額
        amount = float(message.text[1:])  # 去掉正負號
        # 如果是負數，使金額為負
        if not is_positive:
            amount = -amount
        
        # 根據操作類型處理金額
        date = datetime.now().strftime('%Y-%m-%d')
        
        if operation == 'TW':
            add_transaction(user_id, date, 'TW', amount)
            if amount > 0:
                response = f"✅ 已記錄今日台幣收入：NT${amount:,.0f}"
            else:
                response = f"✅ 已記錄今日台幣支出：NT${-amount:,.0f}"
        elif operation == 'CN':
            add_transaction(user_id, date, 'CN', amount)
            if amount > 0:
                response = f"✅ 已記錄今日人民幣收入：¥{amount:,.0f}"
            else:
                response = f"✅ 已記錄今日人民幣支出：¥{-amount:,.0f}"
        elif operation == '公桶':
            update_fund("public", amount)
            if amount > 0:
                response = f"✅ 已添加公桶資金：USDT${amount:.2f}"
            else:
                response = f"✅ 已從公桶資金中扣除：USDT${-amount:.2f}"
        elif operation == '私人':
            update_fund("private", amount)
            if amount > 0:
                response = f"✅ 已添加私人資金：USDT${amount:.2f}"
            else:
                response = f"✅ 已從私人資金中扣除：USDT${-amount:.2f}"
        else:
            response = "❌ 無效的操作類型"
            
        # 發送回覆
        bot.reply_to(message, response)
        
        # 操作完成後，清除用戶狀態
        del user_states[user_id]
        
        # 記錄操作日誌
        logger.info(f"用戶 {message.from_user.username or user_id} 執行 {operation} 操作，金額：{amount}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ 處理金額時出錯：{str(e)}")
        logger.error(f"處理金額輸入出錯: {str(e)}")
        # 出錯時也清除用戶狀態
        del user_states[user_id]

# 提示未回覆訊息的錯誤
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                                          (re.match(r'^[+\-]\d+(\.\d+)?$', message.text) or 
                                           re.match(r'^([0-9/\-\.]+)\s+[+\-]\d+(\.\d+)?$', message.text)) and
                                          (message.reply_to_message is None or 
                                           user_states[message.from_user.id].get('prompt_msg_id') != message.reply_to_message.message_id))
@error_handler
def handle_non_reply_amount(message):
    """提醒用戶需要回覆訊息輸入金額"""
    bot.reply_to(message, "❌ 請<b>回覆</b>之前的提示訊息輸入金額，而不是直接發送。", parse_mode='HTML')

# 設置匯率處理
@bot.message_handler(regexp=r'^設置今日匯率(\d+(\.\d+)?)$')
@error_handler
def handle_set_today_rate(message):
    # 檢查是否為管理員或操作員
    if not is_admin(message.from_user.id, message.chat.id, check_operator=True):
        bot.reply_to(message, "❌ 此功能僅限管理員或操作員使用")
        return
        
    match = re.match(r'^設置今日匯率(\d+(\.\d+)?)$', message.text)
    rate = float(match.group(1))
    
    set_rate(rate)
    
    bot.reply_to(message, f"✅ 已設置今日匯率為：{rate}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 設置今日匯率為 {rate}")

@bot.message_handler(regexp=r'^設置"([0-9/\-]+)"匯率(\d+(\.\d+)?)$')
@error_handler
def handle_set_date_rate(message):
    # 檢查是否為管理員或操作員
    if not is_admin(message.from_user.id, message.chat.id, check_operator=True):
        bot.reply_to(message, "❌ 此功能僅限管理員或操作員使用")
        return
        
    match = re.match(r'^設置"([0-9/\-]+)"匯率(\d+(\.\d+)?)$', message.text)
    date_str = match.group(1)
    rate = float(match.group(2))
    
    date = parse_date(date_str)
    
    set_rate(rate, date)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已設置 {date_display} 匯率為：{rate}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 設置 {date_display} 匯率為 {rate}")

# 刪除交易處理
@bot.message_handler(regexp=r'^刪除"([0-9/\-]+)"NTD金額$')
@error_handler
def handle_delete_ntd(message):
    match = re.match(r'^刪除"([0-9/\-]+)"NTD金額$', message.text)
    date_str = match.group(1)
    
    date = parse_date(date_str)
    
    if delete_transaction(message.from_user.id, date, "TW"):
        date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
        bot.reply_to(message, f"✅ 已刪除 {date_display} 的臺幣金額")
    else:
        bot.reply_to(message, "❌ 找不到該日期的交易記錄")

@bot.message_handler(regexp=r'^刪除"([0-9/\-]+)"CNY金額$')
@error_handler
def handle_delete_cny(message):
    match = re.match(r'^刪除"([0-9/\-]+)"CNY金額$', message.text)
    date_str = match.group(1)
    
    date = parse_date(date_str)
    
    if delete_transaction(message.from_user.id, date, "CN"):
        date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
        bot.reply_to(message, f"✅ 已刪除 {date_display} 的人民幣金額")
    else:
        bot.reply_to(message, "❌ 找不到該日期的交易記錄")

# 設定報表名稱
@bot.message_handler(regexp=r'^報表使用者設定\s+(.+)$')
@error_handler
def handle_set_report_name(message):
    match = re.match(r'^報表使用者設定\s+(.+)$', message.text)
    report_name = match.group(1)
    
    set_report_name(message.from_user.id, report_name)
    
    bot.reply_to(message, f"✅ 已設定報表名稱為：【{report_name}】")

# 查看本月報表
@bot.message_handler(func=lambda message: message.text == '📊查看本月報表')
@error_handler
def handle_show_report(message):
    try:
        # 添加日誌
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 嘗試查看月報表")
        
        # 先發送一個處理中的訊息
        processing_msg = bot.reply_to(message, "⏳ 正在生成報表，請稍候...")
        
        # 檢查數據文件是否存在
        if not os.path.exists(DATA_FILE):
            bot.edit_message_text("❌ 數據文件不存在，請先記錄一些交易", 
                                 message.chat.id, processing_msg.message_id)
            logger.error(f"數據文件不存在: {DATA_FILE}")
            return
            
        # 獲取報表
        report = generate_report(message.from_user.id)
        
        # 發送報表
        bot.edit_message_text(report, message.chat.id, processing_msg.message_id, parse_mode='HTML')
        logger.info(f"成功為用戶 {message.from_user.username or message.from_user.id} 生成報表")
    except Exception as e:
        error_msg = f"❌ 生成報表時發生錯誤：{str(e)}"
        logger.error(f"生成報表錯誤: {str(e)}\n{traceback.format_exc()}")
        
        try:
            bot.reply_to(message, error_msg)
        except:
            bot.send_message(message.chat.id, error_msg)

# 查看歷史報表
@bot.message_handler(func=lambda message: message.text == '📚歷史報表')
@error_handler
def handle_history_reports(message):
    try:
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 請求歷史報表選單")
        
        # 檢查是否有數據
        if not os.path.exists(DATA_FILE):
            bot.reply_to(message, "❌ 尚無歷史數據，請先記錄一些交易")
            return
            
        # 檢查該用戶是否有數據記錄
        data = load_data(DATA_FILE)
        if str(message.from_user.id) not in data or not data[str(message.from_user.id)]:
            bot.reply_to(message, "❌ 您尚未記錄任何交易，請先使用 TW+/- 或 CN+/- 指令記錄交易。")
            return
        
        keyboard = create_history_keyboard()
        bot.reply_to(message, "📚 請選擇要查看的月份：", reply_markup=keyboard)
        logger.info(f"已顯示歷史報表選單給用戶 {message.from_user.username or message.from_user.id}")
    except Exception as e:
        error_msg = f"❌ 顯示歷史報表選單時發生錯誤：{str(e)}"
        logger.error(f"顯示歷史報表選單錯誤: {str(e)}\n{traceback.format_exc()}")
        bot.reply_to(message, error_msg)

# 處理回調查詢
@bot.callback_query_handler(func=lambda call: call.data.startswith('history_'))
@error_handler
def handle_history_callback(call):
    try:
        logger.info(f"用戶 {call.from_user.username or call.from_user.id} 選擇了歷史報表: {call.data}")
        
        # 通知用戶處理中
        bot.answer_callback_query(call.id, "⏳ 正在生成報表...")
        
        month_year = call.data.replace('history_', '')
        year, month = map(int, month_year.split('-'))
        
        # 檢查數據文件
        if not os.path.exists(DATA_FILE):
            bot.edit_message_text("❌ 數據文件不存在，請先記錄一些交易", 
                               call.message.chat.id, call.message.message_id)
            return
            
        # 檢查用戶數據
        data = load_data(DATA_FILE)
        if str(call.from_user.id) not in data or not data[str(call.from_user.id)]:
            bot.edit_message_text("❌ 您尚未記錄任何交易，請先使用 TW+/- 或 CN+/- 指令記錄交易。", 
                               call.message.chat.id, call.message.message_id)
            return
            
        # 檢查該月是否有數據
        user_data = data[str(call.from_user.id)]
        has_data = False
        month_prefix = f"{year}-{month:02d}-"
        
        for date in user_data:
            if date.startswith(month_prefix):
                has_data = True
                break
                
        if not has_data:
            bot.edit_message_text(f"📅 {year}年{month}月沒有交易記錄。", 
                               call.message.chat.id, call.message.message_id)
            return
        
        report = generate_report(call.from_user.id, month, year)
        bot.send_message(call.message.chat.id, report, parse_mode='HTML')
        bot.answer_callback_query(call.id, "✅ 報表已生成")
        logger.info(f"成功為用戶 {call.from_user.username or call.from_user.id} 生成 {year}年{month}月 的歷史報表")
    except Exception as e:
        error_msg = f"❌ 生成歷史報表時發生錯誤：{str(e)}"
        logger.error(f"處理歷史報表回調出錯：{str(e)}\n{traceback.format_exc()}")
        try:
            bot.answer_callback_query(call.id, "發生錯誤，請稍後再試")
            bot.send_message(call.message.chat.id, error_msg)
        except:
            pass

# 完成@使用者功能
@bot.message_handler(regexp=r'^@(\w+)\s+([0-9/\-]+)\s+TW\+(\d+(\.\d+)?)$')
@error_handler
def handle_user_date_tw_add(message):
    match = re.match(r'^@(\w+)\s+([0-9/\-]+)\s+TW\+(\d+(\.\d+)?)$', message.text)
    username = match.group(1)
    date_str = match.group(2)
    amount = float(match.group(3))
    
    date = parse_date(date_str)
    
    # 查找使用者ID
    target_user_id = None
    try:
        chat_members = bot.get_chat_administrators(message.chat.id)
        for member in chat_members:
            if member.user.username == username:
                target_user_id = member.user.id
                break
    except Exception as e:
        logger.error(f"獲取群組成員失敗：{str(e)}")
    
    if target_user_id is None:
        bot.reply_to(message, f"❌ 找不到使用者 @{username}")
        return
    
    add_transaction(target_user_id, date, 'TW', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已為 @{username} 記錄 {date_display} 的臺幣收入：NT${amount:,.0f}")

@bot.message_handler(regexp=r'^@(\w+)\s+([0-9/\-]+)\s+TW-(\d+(\.\d+)?)$')
@error_handler
def handle_user_date_tw_subtract(message):
    match = re.match(r'^@(\w+)\s+([0-9/\-]+)\s+TW-(\d+(\.\d+)?)$', message.text)
    username = match.group(1)
    date_str = match.group(2)
    amount = -float(match.group(3))
    
    date = parse_date(date_str)
    
    # 查找使用者ID
    target_user_id = None
    try:
        chat_members = bot.get_chat_administrators(message.chat.id)
        for member in chat_members:
            if member.user.username == username:
                target_user_id = member.user.id
                break
    except Exception as e:
        logger.error(f"獲取群組成員失敗：{str(e)}")
    
    if target_user_id is None:
        bot.reply_to(message, f"❌ 找不到使用者 @{username}")
        return
    
    add_transaction(target_user_id, date, 'TW', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已為 @{username} 記錄 {date_display} 的臺幣支出：NT${-amount:,.0f}")

@bot.message_handler(regexp=r'^@(\w+)\s+([0-9/\-]+)\s+CN\+(\d+(\.\d+)?)$')
@error_handler
def handle_user_date_cn_add(message):
    match = re.match(r'^@(\w+)\s+([0-9/\-]+)\s+CN\+(\d+(\.\d+)?)$', message.text)
    username = match.group(1)
    date_str = match.group(2)
    amount = float(match.group(3))
    
    date = parse_date(date_str)
    
    # 查找使用者ID
    target_user_id = None
    try:
        chat_members = bot.get_chat_administrators(message.chat.id)
        for member in chat_members:
            if member.user.username == username:
                target_user_id = member.user.id
                break
    except Exception as e:
        logger.error(f"獲取群組成員失敗：{str(e)}")
    
    if target_user_id is None:
        bot.reply_to(message, f"❌ 找不到使用者 @{username}")
        return
    
    add_transaction(target_user_id, date, 'CN', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已為 @{username} 記錄 {date_display} 的人民幣收入：¥{amount:,.0f}")

@bot.message_handler(regexp=r'^@(\w+)\s+([0-9/\-]+)\s+CN-(\d+(\.\d+)?)$')
@error_handler
def handle_user_date_cn_subtract(message):
    match = re.match(r'^@(\w+)\s+([0-9/\-]+)\s+CN-(\d+(\.\d+)?)$', message.text)
    username = match.group(1)
    date_str = match.group(2)
    amount = -float(match.group(3))
    
    date = parse_date(date_str)
    
    # 查找使用者ID
    target_user_id = None
    try:
        chat_members = bot.get_chat_administrators(message.chat.id)
        for member in chat_members:
            if member.user.username == username:
                target_user_id = member.user.id
                break
    except Exception as e:
        logger.error(f"獲取群組成員失敗：{str(e)}")
    
    if target_user_id is None:
        bot.reply_to(message, f"❌ 找不到使用者 @{username}")
        return
    
    add_transaction(target_user_id, date, 'CN', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已為 @{username} 記錄 {date_display} 的人民幣支出：¥{-amount:,.0f}")

# 設置匯率按鈕處理
@bot.message_handler(func=lambda message: message.text == '💱設置匯率')
@error_handler
def handle_rate_setting(message):
    try:
        current_rate = get_rate()
        bot.reply_to(message, 
            f"🔹 當前匯率：{current_rate}\n\n"
            f"修改匯率請使用以下格式：\n"
            f"- 設置今日匯率33.25\n"
            f"- 設置\"MM/DD\"匯率33.44"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ 錯誤：{str(e)}")

# 設定按鈕處理
@bot.message_handler(func=lambda message: message.text == '🔧設定')
@error_handler
def handle_settings(message):
    try:
        settings_text = (
            "⚙️ 設定選項：\n\n"
            "🔹 報表使用者設定 [名稱]\n"
            "    例如：報表使用者設定 北區業績\n\n"
            "🔸 目前報表名稱：" + get_report_name(message.from_user.id)
        )
        bot.reply_to(message, settings_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 錯誤：{str(e)}")

# 設定定期清理任務
def schedule_cleaning():
    import threading
    import time
    
    def cleaning_task():
        while True:
            try:
                logger.info("開始執行定期清理任務...")
                clean_old_data()
                logger.info("定期清理任務完成")
                # 每天執行一次
                time.sleep(86400)  # 24小時 = 86400秒
            except Exception as e:
                logger.error(f"定期清理任務出錯：{str(e)}")
                time.sleep(3600)  # 出錯后等待1小時再試
    
    # 啟動清理線程
    cleaning_thread = threading.Thread(target=cleaning_task, daemon=True)
    cleaning_thread.start()
    logger.info("定期清理線程已啟動")

# 處理查詢命令
@bot.message_handler(func=lambda message: message.text.lower() == 'help' or message.text == '幫助')
@error_handler
def handle_help(message):
    help_text = """<b>📋 指令說明</b>

<b>🔸 基本指令</b>
/start - 啟動機器人，顯示主選單
/help - 顯示此幫助信息
/restart - 重新啟動機器人（僅管理員）

<b>🔸 報表指令</b>
📊查看本月報表 - 顯示當月收支報表
總表 - 顯示所有人的收支總計
📚歷史報表 - 查看過去月份的報表
初始化報表 - 清空所有個人報表數據

<b>🔸 記帳指令 (多種格式輸入方式)</b>
<code>TW+數字</code> - 記錄台幣收入
<code>TW-數字</code> - 記錄台幣支出
<code>CN+數字</code> - 記錄人民幣收入
<code>CN-數字</code> - 記錄人民幣支出
<code>台幣+數字</code> - 記錄台幣收入 (新增)
<code>人民幣-數字</code> - 記錄人民幣支出 (新增)

<b>🔸 日期記帳</b>
<code>日期 TW+數字</code> - 記錄特定日期台幣收入
<code>日期 TW-數字</code> - 記錄特定日期台幣支出
<code>日期 CN+數字</code> - 記錄特定日期人民幣收入
<code>日期 CN-數字</code> - 記錄特定日期人民幣支出
<code>日期 台幣+數字</code> - 記錄特定日期台幣收入 (新增)
<code>日期 人民幣-數字</code> - 記錄特定日期人民幣支出 (新增)

<b>🔸 為其他用戶記帳</b>
<code>@用戶名 日期 TW+數字</code> - 為指定用戶記錄台幣收入
<code>@用戶名 日期 TW-數字</code> - 為指定用戶記錄台幣支出
<code>@用戶名 日期 CN+數字</code> - 為指定用戶記錄人民幣收入
<code>@用戶名 日期 CN-數字</code> - 為指定用戶記錄人民幣支出

<b>🔸 資金管理</b>
<code>公桶+數字</code> - 增加公桶資金
<code>公桶-數字</code> - 減少公桶資金
<code>私人+數字</code> - 增加私人資金
<code>私人-數字</code> - 減少私人資金
<code>公共資金+數字</code> - 增加公桶資金 (新增)
<code>私人資金-數字</code> - 減少私人資金 (新增)

<b>🔸 匯率設置</b>
<code>設置今日匯率數字</code> - 設置今日匯率
<code>設置"日期"匯率數字</code> - 設置指定日期匯率

<b>🔸 刪除記錄</b>
<code>刪除"日期"NTD金額</code> - 刪除指定日期台幣記錄
<code>刪除"日期"CNY金額</code> - 刪除指定日期人民幣記錄
<code>刪除"月份"NTD報表</code> - 刪除整個月份的台幣記錄 (格式: YYYY-MM 或 MM/YYYY)
<code>刪除"月份"CNY報表</code> - 刪除整個月份的人民幣記錄 (格式: YYYY-MM 或 MM/YYYY)

<b>🔸 其他設置</b>
<code>報表使用者設定 名稱</code> - 設置報表標題名稱

<b>🔸 機器人運行狀態</b>
每日早上 7:00 機器人會自動開機，並發送開機通知
每日凌晨 2:00 機器人會自動休眠，並發送休眠通知
您可以隨時使用 <code>/start</code> 喚醒機器人

<b>🔸 群組管理</b>
⚙️群管設定 - 開啟群組管理選單"""

    bot.reply_to(message, help_text, parse_mode='HTML')
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 查看了指令說明")

# 創建群管設定鍵盤
def create_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton('👋 歡迎詞設定'),
        KeyboardButton('🔕 靜音設定')
    )
    keyboard.row(
        KeyboardButton('🧹 清理訊息'),
        KeyboardButton('🔒 權限管理')
    )
    keyboard.row(
        KeyboardButton('👤 成員管理'),
        KeyboardButton('⚠️ 警告系統')
    )
    keyboard.row(
        KeyboardButton('🔙 返回主選單')
    )
    return keyboard

# 群管設定處理函數
@bot.message_handler(func=lambda message: message.text == '⚙️群管設定')
@error_handler
def handle_admin_settings(message):
    """處理群管設定請求"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    admin_help_text = """<b>⚙️ 群組管理設定</b>

請選擇要管理的功能：

<b>👋 歡迎詞設定</b>
設置新成員加入群組時的歡迎訊息。

<b>🔕 靜音設定</b>
管理用戶禁言設置，可臨時或永久禁言。

<b>🧹 清理訊息</b>
批量刪除群組訊息，可刪除全部或特定時間段。

<b>🔒 權限管理</b>
設置用戶權限，管理操作員名單。

<b>👤 成員管理</b>
踢出成員、邀請用戶等成員管理功能。

<b>⚠️ 警告系統</b>
對違規用戶發出警告，達到上限自動禁言。

使用方式：點擊相應按鈕進入對應設定頁面。"""

    bot.reply_to(message, admin_help_text, parse_mode='HTML', reply_markup=create_admin_keyboard())
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 進入群組管理設定")

# 處理返回主選單
@bot.message_handler(func=lambda message: message.text == '🔙 返回主選單')
@error_handler
def handle_return_to_main(message):
    """處理返回主選單請求"""
    bot.reply_to(message, "✅ 已返回主選單", reply_markup=create_keyboard())
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 返回主選單")

# 歡迎詞設定
@bot.message_handler(func=lambda message: message.text == '👋 歡迎詞設定')
@error_handler
def handle_welcome_settings(message):
    """處理歡迎詞設定請求"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 獲取當前歡迎詞
    settings = load_data(USER_SETTINGS_FILE)
    chat_id = str(message.chat.id)
    
    # 從配置中獲取當前歡迎詞，如果沒有則使用預設值
    current_welcome = "歡迎 {USERNAME} 加入 {GROUPNAME}！"
    if chat_id in settings and 'welcome_message' in settings[chat_id]:
        current_welcome = settings[chat_id]['welcome_message']
    
    welcome_help_text = f"""<b>👋 歡迎詞設定</b>

當前歡迎詞：
<pre>{current_welcome}</pre>

可用變數：
<code>{{USERNAME}}</code> - 新成員的用戶名
<code>{{FULLNAME}}</code> - 新成員的完整名稱
<code>{{FIRSTNAME}}</code> - 新成員的名字
<code>{{GROUPNAME}}</code> - 群組名稱

設定方式：
直接回覆此訊息，輸入新的歡迎詞內容即可。"""

    # 儲存用戶狀態
    sent_msg = bot.reply_to(message, welcome_help_text, parse_mode='HTML')
    user_states[message.from_user.id] = {
        'state': 'waiting_welcome_message', 
        'chat_id': message.chat.id,
        'prompt_msg_id': sent_msg.message_id
    }
    
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看歡迎詞設定")

# 處理歡迎詞設定回覆
@bot.message_handler(func=lambda message: message.reply_to_message is not None and 
                                          message.from_user.id in user_states and 
                                          user_states[message.from_user.id].get('state') == 'waiting_welcome_message' and
                                          user_states[message.from_user.id].get('prompt_msg_id') == message.reply_to_message.message_id)
@error_handler
def handle_welcome_message_reply(message):
    """處理用戶對歡迎詞設定的回覆"""
    user_id = message.from_user.id
    chat_id = user_states[user_id]['chat_id']
    
    # 獲取歡迎詞內容
    welcome_message = message.text.strip()
    
    try:
        # 保存歡迎詞設定
        settings = load_data(USER_SETTINGS_FILE)
        
        # 使用聊天ID作為鍵，以便群組特定設定
        chat_id_str = str(chat_id)
        if chat_id_str not in settings:
            settings[chat_id_str] = {}
        
        settings[chat_id_str]['welcome_message'] = welcome_message
        save_data(settings, USER_SETTINGS_FILE)
        
        # 回覆成功訊息
        bot.reply_to(message, f"✅ 歡迎詞已成功設定為：\n\n<pre>{welcome_message}</pre>", parse_mode='HTML')
        logger.info(f"管理員 {message.from_user.username or user_id} 設定了新的歡迎詞")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定歡迎詞時出錯：{str(e)}")
        logger.error(f"設定歡迎詞出錯: {str(e)}")
    
    # 清除用戶狀態
    if user_id in user_states:
        del user_states[user_id]

# 靜音設定
@bot.message_handler(func=lambda message: message.text == '🔕 靜音設定')
@error_handler
def handle_mute_settings(message):
    """處理靜音設定請求"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    mute_help_text = """<b>🔕 靜音設定</b>

禁言用戶的指令：
<code>/ban @用戶名 [時間] [原因]</code>
例如：<code>/ban @user 24h 違反規定</code>

時間格式：
- <code>1h</code>：1小時
- <code>1d</code>：1天
- <code>1w</code>：1週
不指定時間則為永久禁言

解除禁言：
<code>/unban @用戶名</code>

注意：
1. 只有管理員可以使用此功能
2. 無法禁言其他管理員
3. 只有群主可以禁言管理員"""

    bot.reply_to(message, mute_help_text, parse_mode='HTML')
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看靜音設定")

# 清理訊息
@bot.message_handler(func=lambda message: message.text == '🧹 清理訊息')
@error_handler
def handle_clear_messages(message):
    """處理清理訊息請求"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    clear_help_text = """<b>🧹 清理訊息</b>

清理訊息的指令：

<code>/del</code> - 回覆要刪除的訊息以刪除單一訊息
<code>刪除所有聊天室訊息</code> - 刪除所有訊息（慎用）
<code>刪除所有非置頂訊息</code> - 保留置頂訊息，刪除其他訊息

注意：
1. 只有管理員可以使用此功能
2. 一次大量刪除可能耗時較長
3. 機器人需要擁有刪除訊息的權限"""

    bot.reply_to(message, clear_help_text, parse_mode='HTML')
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看清理訊息設定")

# 權限管理
@bot.message_handler(func=lambda message: message.text == '🔒 權限管理')
@error_handler
def handle_permission_settings(message):
    """處理權限管理請求"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    permission_help_text = """<b>🔒 權限管理</b>

操作員管理指令：

<code>設定操作員 @用戶名1 @用戶名2 ...</code> - 設定操作員
<code>查看操作員</code> - 列出所有操作員
<code>刪除操作員 @用戶名1 @用戶名2 ...</code> - 移除操作員

查看權限指令：
<code>/info @用戶名</code> - 查看用戶在群組中的權限狀態

注意：
1. 操作員可以使用記帳和設定匯率功能
2. 只有管理員可以設定操作員
3. 操作員不具備群組管理權限"""

    bot.reply_to(message, permission_help_text, parse_mode='HTML')
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看權限管理設定")

# 成員管理
@bot.message_handler(func=lambda message: message.text == '👤 成員管理')
@error_handler
def handle_member_management(message):
    """處理成員管理請求"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    member_help_text = """<b>👤 成員管理</b>

成員管理指令：

<code>/kick @用戶名 [原因]</code> - 踢出用戶
例如：<code>/kick @user 違反規定</code>

<code>/admin</code> - 查看管理員命令列表

<code>📋查看管理員</code> - 列出所有群組管理員

注意：
1. 只有管理員可以使用此功能
2. 無法踢出其他管理員
3. 被踢出的用戶依然可以透過邀請連結重新加入"""

    bot.reply_to(message, member_help_text, parse_mode='HTML')
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看成員管理設定")

# 警告系統
@bot.message_handler(func=lambda message: message.text == '⚠️ 警告系統')
@error_handler
def handle_warning_system(message):
    """處理警告系統請求"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    warning_help_text = """<b>⚠️ 警告系統</b>

警告系統指令：

<code>/warn @用戶名 [原因]</code> - 警告用戶
例如：<code>/warn @user 違反規定</code>

<code>/unwarn @用戶名</code> - 移除用戶警告

<code>/warns @用戶名</code> - 查看用戶警告次數

注意：
1. 只有管理員可以使用此功能
2. 無法警告其他管理員
3. 警告達到3次將自動禁言24小時
4. 禁言後警告次數會被重置"""

    bot.reply_to(message, warning_help_text, parse_mode='HTML')
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看警告系統設定")

# 刪除指定月份的NTD報表記錄
@bot.message_handler(regexp=r'^刪除"([0-9/\-]+)"NTD報表$')
@error_handler
def handle_delete_month_ntd(message):
    """刪除指定月份的台幣記錄"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限管理員使用")
        return
    
    match = re.match(r'^刪除"([0-9/\-]+)"NTD報表$', message.text)
    month_str = match.group(1)
    
    try:
        # 處理不同的日期格式
        if '/' in month_str:
            parts = month_str.split('/')
            if len(parts) == 2:
                month, year = int(parts[0]), int(parts[1])
            else:
                raise ValueError("月份格式不正確")
        elif '-' in month_str:
            parts = month_str.split('-')
            if len(parts) == 2:
                year, month = int(parts[0]), int(parts[1])
            else:
                raise ValueError("月份格式不正確")
        else:
            raise ValueError("月份格式不正確")
        
        # 計算月份的日期範圍
        _, last_day = calendar.monthrange(year, month)
        month_dates = [f"{year}-{month:02d}-{day:02d}" for day in range(1, last_day + 1)]
        
        # 刪除該月份的所有台幣記錄
        data = load_data(DATA_FILE)
        user_id = str(message.from_user.id)
        
        if user_id not in data:
            bot.reply_to(message, "❌ 您還沒有任何記錄")
            return
        
        deleted_count = 0
        for date in month_dates:
            if date in data[user_id] and "TW" in data[user_id][date]:
                data[user_id][date]["TW"] = 0
                deleted_count += 1
        
        save_data(data, DATA_FILE)
        
        bot.reply_to(message, f"✅ 已刪除 {year}年{month}月 的 {deleted_count} 筆台幣記錄")
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 刪除了 {year}年{month}月 的台幣記錄")
    
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除失敗: {str(e)}\n格式應為 MM/YYYY 或 YYYY-MM")
        logger.error(f"刪除月份資料失敗: {str(e)}")

# 刪除指定月份的CNY報表記錄
@bot.message_handler(regexp=r'^刪除"([0-9/\-]+)"CNY報表$')
@error_handler
def handle_delete_month_cny(message):
    """刪除指定月份的人民幣記錄"""
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限管理員使用")
        return
    
    match = re.match(r'^刪除"([0-9/\-]+)"CNY報表$', message.text)
    month_str = match.group(1)
    
    try:
        # 處理不同的日期格式
        if '/' in month_str:
            parts = month_str.split('/')
            if len(parts) == 2:
                month, year = int(parts[0]), int(parts[1])
            else:
                raise ValueError("月份格式不正確")
        elif '-' in month_str:
            parts = month_str.split('-')
            if len(parts) == 2:
                year, month = int(parts[0]), int(parts[1])
            else:
                raise ValueError("月份格式不正確")
        else:
            raise ValueError("月份格式不正確")
        
        # 計算月份的日期範圍
        _, last_day = calendar.monthrange(year, month)
        month_dates = [f"{year}-{month:02d}-{day:02d}" for day in range(1, last_day + 1)]
        
        # 刪除該月份的所有人民幣記錄
        data = load_data(DATA_FILE)
        user_id = str(message.from_user.id)
        
        if user_id not in data:
            bot.reply_to(message, "❌ 您還沒有任何記錄")
            return
        
        deleted_count = 0
        for date in month_dates:
            if date in data[user_id] and "CN" in data[user_id][date]:
                data[user_id][date]["CN"] = 0
                deleted_count += 1
        
        save_data(data, DATA_FILE)
        
        bot.reply_to(message, f"✅ 已刪除 {year}年{month}月 的 {deleted_count} 筆人民幣記錄")
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 刪除了 {year}年{month}月 的人民幣記錄")
    
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除失敗: {str(e)}\n格式應為 MM/YYYY 或 YYYY-MM")
        logger.error(f"刪除月份資料失敗: {str(e)}")

# 初始化報表功能
@bot.message_handler(func=lambda message: message.text == '初始化報表')
@error_handler
def handle_initialize_report(message):
    """初始化用戶的報表數據"""
    user_id = message.from_user.id
    
    # 記錄請求
    logger.info(f"用戶 {message.from_user.username or user_id} 請求初始化報表")
    
    try:
        # 檢查用戶是否已有狀態，如果有則清除
        if user_id in user_states:
            logger.info(f"清除用戶 {user_id} 之前的狀態: {user_states[user_id]}")
            del user_states[user_id]
        
        # 確認操作
        msg = bot.reply_to(message, "⚠️ 此操作將刪除您的所有記帳資料，確定要初始化嗎？\n\n請回覆「確認初始化」來繼續，或回覆其他內容取消。")
        
        # 儲存用戶狀態
        user_states[user_id] = {
            'state': 'waiting_init_confirmation',
            'prompt_msg_id': msg.message_id
        }
        
        logger.info(f"已設置用戶 {user_id} 的狀態: {user_states[user_id]}")
    except Exception as e:
        error_msg = f"處理初始化報表請求時出錯: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, f"❌ 處理初始化報表請求時出錯: {str(e)}")

# 處理初始化確認
@bot.message_handler(func=lambda message: message.reply_to_message is not None and 
                                          message.from_user.id in user_states and 
                                          user_states[message.from_user.id].get('state') == 'waiting_init_confirmation' and
                                          user_states[message.from_user.id].get('prompt_msg_id') == message.reply_to_message.message_id)
@error_handler
def handle_init_confirmation(message):
    """處理用戶對初始化報表的確認"""
    user_id = message.from_user.id
    str_user_id = str(user_id)
    
    # 記錄用戶的回覆，便於調試
    logger.info(f"收到用戶 {message.from_user.username or user_id} 的初始化確認回覆: '{message.text}'")
    
    try:
        if message.text == "確認初始化":
            # 從數據中移除用戶資料
            data = load_data(DATA_FILE)
            logger.info(f"嘗試初始化用戶 {str_user_id} 的報表數據")
            
            if str_user_id in data:
                data[str_user_id] = {}
                save_data(data, DATA_FILE)
                logger.info(f"已清空用戶 {str_user_id} 的報表數據")
            else:
                logger.info(f"用戶 {str_user_id} 在數據文件中沒有記錄")
            
            # 重置報表名稱
            settings = load_data(USER_SETTINGS_FILE)
            if str_user_id in settings:
                if 'report_name' in settings[str_user_id]:
                    settings[str_user_id]['report_name'] = "總表"
                save_data(settings, USER_SETTINGS_FILE)
                logger.info(f"已重置用戶 {str_user_id} 的報表名稱")
            
            bot.reply_to(message, "✅ 報表已成功初始化！所有記帳數據已清空。")
            logger.info(f"用戶 {message.from_user.username or user_id} 已初始化報表")
        else:
            bot.reply_to(message, "❌ 初始化已取消。")
            logger.info(f"用戶 {message.from_user.username or user_id} 取消了初始化報表")
    except Exception as e:
        error_msg = f"初始化報表時出錯: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, f"❌ 初始化報表時出錯: {str(e)}")
    finally:
        # 確保無論如何都清除用戶狀態
        if user_id in user_states:
            del user_states[user_id]
            logger.info(f"已清除用戶 {user_id} 的狀態")

# 群管功能按鈕實現
# 創建群管功能鍵盤
def create_admin_function_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👋 設置歡迎詞", callback_data="admin_welcome"),
        InlineKeyboardButton("🔕 禁言管理", callback_data="admin_mute")
    )
    keyboard.add(
        InlineKeyboardButton("🧹 清理消息", callback_data="admin_clean"),
        InlineKeyboardButton("🔒 權限設置", callback_data="admin_perm")
    )
    keyboard.add(
        InlineKeyboardButton("👤 成員管理", callback_data="admin_member"),
        InlineKeyboardButton("⚠️ 警告系統", callback_data="admin_warn")
    )
    keyboard.add(
        InlineKeyboardButton("🔙 返回主選單", callback_data="admin_back")
    )
    return keyboard

# 更新群管設定處理函數
@bot.message_handler(func=lambda message: message.text == '⚙️群管設定')
@error_handler
def handle_admin_settings(message):
    """處理群管設定請求"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    admin_help_text = """<b>⚙️ 群組管理設定</b>

請選擇要管理的功能：

<b>👋 歡迎詞設定</b>
設置新成員加入群組時的歡迎訊息。

<b>🔕 靜音設定</b>
管理用戶禁言設置，可臨時或永久禁言。

<b>🧹 清理訊息</b>
批量刪除群組訊息，可刪除全部或特定時間段。

<b>🔒 權限管理</b>
設置用戶權限，管理操作員名單。

<b>👤 成員管理</b>
踢出成員、邀請用戶等成員管理功能。

<b>⚠️ 警告系統</b>
對違規用戶發出警告，達到上限自動禁言。

使用方式：點擊相應按鈕進入對應設定頁面。"""

    bot.reply_to(message, admin_help_text, parse_mode='HTML', reply_markup=create_admin_function_keyboard())
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 進入群組管理設定")

# 處理群管功能按鈕回調
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
@error_handler
def handle_admin_callback(call):
    """處理群管按鈕回調"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # 檢查是否為管理員
    if not is_admin(user_id, chat_id):
        bot.answer_callback_query(call.id, "❌ 此功能僅限群組管理員使用", show_alert=True)
        return
    
    action = call.data[6:]  # 移除 'admin_' 前綴
    
    if action == "welcome":
        # 歡迎詞設定
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""<b>👋 歡迎詞設定</b>

當前歡迎詞：
<pre>歡迎 {{USERNAME}} 加入 {{GROUPNAME}}！</pre>

可用變數：
<code>{{USERNAME}}</code> - 新成員的用戶名
<code>{{FULLNAME}}</code> - 新成員的完整名稱
<code>{{FIRSTNAME}}</code> - 新成員的名字
<code>{{GROUPNAME}}</code> - 群組名稱

設定方式：
請在群組中直接發送：
<code>設定歡迎詞：您要設定的歡迎詞內容</code>""",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            )
        )
    
    elif action == "mute":
        # 禁言管理
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""<b>🔕 靜音設定</b>

禁言用戶的指令：
<code>/ban @用戶名 [時間] [原因]</code>
例如：<code>/ban @user 24h 違反規定</code>

時間格式：
- <code>1h</code>：1小時
- <code>1d</code>：1天
- <code>1w</code>：1週
不指定時間則為永久禁言

解除禁言：
<code>/unban @用戶名</code>""",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            )
        )
    
    elif action == "clean":
        # 清理消息
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""<b>🧹 清理訊息</b>

清理訊息的指令：

<code>/del</code> - 回覆要刪除的訊息以刪除單一訊息
<code>刪除所有聊天室訊息</code> - 刪除所有訊息（慎用）
<code>刪除所有非置頂訊息</code> - 保留置頂訊息，刪除其他訊息""",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            )
        )
    
    elif action == "perm":
        # 權限設置
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""<b>🔒 權限管理</b>

操作員管理指令：

<code>設定操作員 @用戶名1 @用戶名2 ...</code> - 設定操作員
<code>查看操作員</code> - 列出所有操作員
<code>刪除操作員 @用戶名1 @用戶名2 ...</code> - 移除操作員

查看權限指令：
<code>/info @用戶名</code> - 查看用戶在群組中的權限狀態""",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            )
        )
    
    elif action == "member":
        # 成員管理
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""<b>👤 成員管理</b>

成員管理指令：

<code>/kick @用戶名 [原因]</code> - 踢出用戶
例如：<code>/kick @user 違反規定</code>

<code>/admin</code> - 查看管理員命令列表

<code>📋查看管理員</code> - 列出所有群組管理員""",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            )
        )
    
    elif action == "warn":
        # 警告系統
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""<b>⚠️ 警告系統</b>

警告系統指令：

<code>/warn @用戶名 [原因]</code> - 警告用戶
例如：<code>/warn @user 違反規定</code>

<code>/unwarn @用戶名</code> - 移除用戶警告

<code>/warns @用戶名</code> - 查看用戶警告次數""",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            )
        )
    
    elif action == "back":
        # 返回主選單
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "✅ 已返回主選單", reply_markup=create_keyboard())
    
    # 回答回調查詢
    bot.answer_callback_query(call.id)

# 啟動時啟動定期清理任務
if __name__ == '__main__':
    try:
        logger.info("機器人啟動中...")
        BOT_START_TIME = datetime.now()
        
        # 初始化數據文件
        init_files()
        
        # 檢查是重啟還是新啟動
        is_restart = False
        if os.path.exists("restart_flag.txt"):
            is_restart = True
            os.remove("restart_flag.txt")  # 移除標記文件
        
        # 清理舊數據
        clean_old_data()
        
        # 啟動心跳檢測
        start_heartbeat()
        
        # 發送啟動/重啟通知到群組
        if is_restart:
            # 重啟通知
            try:
                bot.send_message(TARGET_GROUP_ID, "✅ 機器人已重新啟動完成，可以繼續使用！")
                logger.info(f"已發送重啟完成通知到群組 {TARGET_GROUP_ID}")
            except Exception as e:
                logger.error(f"發送重啟完成通知失敗: {str(e)}")
        else:
            # 新啟動通知
            send_startup_notification()
        
        # 啟動機器人
        logger.info("機器人開始監聽消息...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.critical(f"機器人啟動失敗: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1) 

# 處理新成員加入
@bot.message_handler(content_types=['new_chat_members'])
@error_handler
def handle_new_members(message):
    """處理新成員加入群組事件"""
    chat_id = message.chat.id
    
    # 獲取設定的歡迎詞
    settings = load_data(USER_SETTINGS_FILE)
    chat_id_str = str(chat_id)
    
    # 默認歡迎詞
    welcome_message = "歡迎 {USERNAME} 加入 {GROUPNAME}！"
    
    # 如果有設定的歡迎詞，使用設定的
    if chat_id_str in settings and 'welcome_message' in settings[chat_id_str]:
        welcome_message = settings[chat_id_str]['welcome_message']
    
    # 獲取群組名稱
    group_name = message.chat.title
    
    # 處理每個新成員
    for new_member in message.new_chat_members:
        # 跳過機器人自己
        if new_member.id == bot.get_me().id:
            continue
        
        # 使用變數替換歡迎詞中的佔位符
        username = new_member.username if new_member.username else new_member.first_name
        formatted_message = welcome_message.format(
            USERNAME=f"@{username}" if new_member.username else username,
            FULLNAME=f"{new_member.first_name} {new_member.last_name if new_member.last_name else ''}",
            FIRSTNAME=new_member.first_name,
            GROUPNAME=group_name
        )
        
        # 發送歡迎訊息
        bot.send_message(chat_id, formatted_message, parse_mode='HTML')
        
        # 記錄日誌
        logger.info(f"歡迎新成員 {username} 加入群組 {group_name}")

# 刪除所有聊天室訊息
@bot.message_handler(func=lambda message: message.text == '刪除所有聊天室訊息')
@error_handler
def handle_delete_all_messages(message):
    """處理刪除所有聊天室訊息的請求"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 發送確認訊息，避免誤操作
    confirm_msg = bot.reply_to(
        message, 
        "⚠️ <b>警告</b>：此操作將刪除聊天中的<b>所有訊息</b>，確定要執行嗎？\n\n"
        "請回覆「確認刪除所有訊息」來確認此操作。",
        parse_mode='HTML'
    )
    
    # 儲存用戶狀態
    user_states[message.from_user.id] = {
        'state': 'waiting_delete_all_confirmation',
        'chat_id': message.chat.id,
        'prompt_msg_id': confirm_msg.message_id
    }
    
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 請求刪除所有聊天室訊息")

# 刪除所有非置頂訊息
@bot.message_handler(func=lambda message: message.text == '刪除所有非置頂訊息')
@error_handler
def handle_delete_non_pinned_messages(message):
    """處理刪除所有非置頂訊息的請求"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 發送確認訊息，避免誤操作
    confirm_msg = bot.reply_to(
        message, 
        "⚠️ <b>警告</b>：此操作將刪除聊天中的<b>所有非置頂訊息</b>，確定要執行嗎？\n\n"
        "請回覆「確認刪除非置頂訊息」來確認此操作。",
        parse_mode='HTML'
    )
    
    # 儲存用戶狀態
    user_states[message.from_user.id] = {
        'state': 'waiting_delete_non_pinned_confirmation',
        'chat_id': message.chat.id,
        'prompt_msg_id': confirm_msg.message_id
    }
    
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 請求刪除所有非置頂訊息")

# 刪除單一訊息
@bot.message_handler(commands=['del'])
@error_handler
def handle_delete_single_message(message):
    """處理刪除單一訊息的請求"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 檢查是否回覆了訊息
    if not message.reply_to_message:
        bot.reply_to(message, "❌ 請回覆要刪除的訊息使用此命令")
        return
    
    try:
        # 刪除被回覆的訊息
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        # 刪除命令訊息
        bot.delete_message(message.chat.id, message.message_id)
        logger.info(f"管理員 {message.from_user.username or message.from_user.id} 刪除了一條訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除訊息失敗：{str(e)}")
        logger.error(f"刪除訊息失敗: {str(e)}")

# 處理刪除所有訊息確認
@bot.message_handler(func=lambda message: message.reply_to_message is not None and 
                                          message.from_user.id in user_states and 
                                          user_states[message.from_user.id].get('state') == 'waiting_delete_all_confirmation' and
                                          user_states[message.from_user.id].get('prompt_msg_id') == message.reply_to_message.message_id)
@error_handler
def handle_delete_all_confirmation(message):
    """處理用戶對刪除所有訊息的確認"""
    user_id = message.from_user.id
    chat_id = user_states[user_id]['chat_id']
    
    if message.text.strip() == '確認刪除所有訊息':
        # 發送開始刪除的通知
        status_msg = bot.reply_to(message, "🔄 開始刪除所有訊息，這可能需要一些時間...")
        
        try:
            # 獲取群組中的所有訊息（實際上需要使用API，這裡是簡化示例）
            # 由於API限制，實際操作可能需要更複雜的方法
            messages_deleted = 0
            
            # 刪除最近的訊息
            # 這裡只能示意性刪除，因為Telegram API不允許批量刪除所有訊息
            # 實際應用需要獲取訊息ID列表並逐一刪除
            for i in range(message.message_id, message.message_id - 100, -1):
                try:
                    bot.delete_message(chat_id, i)
                    messages_deleted += 1
                except:
                    pass
            
            # 更新狀態訊息
            bot.edit_message_text(
                f"✅ 操作完成，已嘗試刪除 {messages_deleted} 條訊息。\n"
                f"注意：由於Telegram限制，僅能刪除最近的訊息。",
                chat_id=chat_id,
                message_id=status_msg.message_id
            )
            
            logger.info(f"管理員 {message.from_user.username or user_id} 刪除了 {messages_deleted} 條訊息")
            
        except Exception as e:
            bot.reply_to(message, f"❌ 刪除訊息時出錯：{str(e)}")
            logger.error(f"批量刪除訊息出錯: {str(e)}")
    else:
        bot.reply_to(message, "❌ 操作已取消")
        logger.info(f"管理員 {message.from_user.username or user_id} 取消了刪除所有訊息")
    
    # 清除用戶狀態
    if user_id in user_states:
        del user_states[user_id]

# 處理刪除非置頂訊息確認
@bot.message_handler(func=lambda message: message.reply_to_message is not None and 
                                          message.from_user.id in user_states and 
                                          user_states[message.from_user.id].get('state') == 'waiting_delete_non_pinned_confirmation' and
                                          user_states[message.from_user.id].get('prompt_msg_id') == message.reply_to_message.message_id)
@error_handler
def handle_delete_non_pinned_confirmation(message):
    """處理用戶對刪除非置頂訊息的確認"""
    user_id = message.from_user.id
    chat_id = user_states[user_id]['chat_id']
    
    if message.text.strip() == '確認刪除非置頂訊息':
        # 發送開始刪除的通知
        status_msg = bot.reply_to(message, "🔄 開始刪除所有非置頂訊息，這可能需要一些時間...")
        
        try:
            # 獲取置頂訊息ID
            pinned_message = None
            try:
                pinned_message = bot.get_chat(chat_id).pinned_message
            except:
                pass
            
            pinned_id = pinned_message.message_id if pinned_message else -1
            
            # 刪除最近的非置頂訊息
            messages_deleted = 0
            
            for i in range(message.message_id, message.message_id - 100, -1):
                if i != pinned_id:
                    try:
                        bot.delete_message(chat_id, i)
                        messages_deleted += 1
                    except:
                        pass
            
            # 更新狀態訊息
            bot.edit_message_text(
                f"✅ 操作完成，已嘗試刪除 {messages_deleted} 條非置頂訊息。\n"
                f"注意：由於Telegram限制，僅能刪除最近的訊息。",
                chat_id=chat_id,
                message_id=status_msg.message_id
            )
            
            logger.info(f"管理員 {message.from_user.username or user_id} 刪除了 {messages_deleted} 條非置頂訊息")
            
        except Exception as e:
            bot.reply_to(message, f"❌ 刪除訊息時出錯：{str(e)}")
            logger.error(f"批量刪除非置頂訊息出錯: {str(e)}")
    else:
        bot.reply_to(message, "❌ 操作已取消")
        logger.info(f"管理員 {message.from_user.username or user_id} 取消了刪除非置頂訊息")
    
    # 清除用戶狀態
    if user_id in user_states:
        del user_states[user_id]

# 處理 /ban 指令
@bot.message_handler(commands=['ban'])
@error_handler
def handle_ban_command(message):
    """處理禁言用戶的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args:
        bot.reply_to(message, "❌ 使用方式: /ban @用戶名 [時間] [原因]\n例如: /ban @user 24h 違反規定")
        return
    
    # 解析目標用戶
    target_username = command_args[0].replace('@', '')
    
    # 尋找目標用戶ID
    target_user_id = None
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or f"ID:{target_user_id}"
        else:
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == target_username:
                    target_user_id = member.user.id
                    break
            
            # 如果未找到，嘗試使用正則表達式解析數字ID
            if not target_user_id and command_args[0].isdigit():
                target_user_id = int(command_args[0])
    except Exception as e:
        bot.reply_to(message, f"❌ 尋找目標用戶時出錯: {str(e)}")
        logger.error(f"尋找目標用戶出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, f"❌ 找不到用戶 '{target_username}'")
        return
    
    # 檢查目標用戶是否為管理員
    if is_admin(target_user_id, message.chat.id):
        # 如果目標是管理員，檢查操作者是否為群主
        try:
            chat_creator = None
            chat_info = bot.get_chat(message.chat.id)
            if hasattr(chat_info, 'owner_id'):
                chat_creator = chat_info.owner_id
            
            # 如果操作者不是群主，禁止禁言其他管理員
            if message.from_user.id != chat_creator:
                bot.reply_to(message, "❌ 您無法禁言其他管理員，只有群主可以進行此操作")
                return
        except:
            bot.reply_to(message, "❌ 無法禁言其他管理員")
            return
    
    # 解析禁言時間
    ban_time = None
    reason = "未指定原因"
    
    if len(command_args) > 1:
        time_arg = command_args[1].lower()
        
        # 解析時間格式
        if time_arg.endswith('h'):
            try:
                hours = int(time_arg[:-1])
                ban_time = timedelta(hours=hours)
            except:
                pass
        elif time_arg.endswith('d'):
            try:
                days = int(time_arg[:-1])
                ban_time = timedelta(days=days)
            except:
                pass
        elif time_arg.endswith('w'):
            try:
                weeks = int(time_arg[:-1])
                ban_time = timedelta(weeks=weeks)
            except:
                pass
    
    # 解析禁言原因
    if len(command_args) > 2:
        reason = ' '.join(command_args[2:])
    
    # 執行禁言
    try:
        # 計算禁言結束時間
        until_date = None
        if ban_time:
            until_date = int((datetime.now() + ban_time).timestamp())
        
        # 設置禁言權限
        bot.restrict_chat_member(
            message.chat.id, 
            target_user_id,
            permissions=telebot.types.ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            ),
            until_date=until_date
        )
        
        # 發送成功訊息
        if ban_time:
            time_str = f"{ban_time.days}天" if ban_time.days > 0 else f"{ban_time.seconds//3600}小時"
            bot.reply_to(message, f"✅ 已禁言用戶 {target_username} {time_str}\n原因: {reason}")
        else:
            bot.reply_to(message, f"✅ 已永久禁言用戶 {target_username}\n原因: {reason}")
        
        logger.info(f"管理員 {message.from_user.username or message.from_user.id} 禁言了用戶 {target_username}")
    
    except Exception as e:
        bot.reply_to(message, f"❌ 禁言用戶時出錯: {str(e)}")
        logger.error(f"禁言用戶出錯: {str(e)}")

# 處理 /unban 指令
@bot.message_handler(commands=['unban'])
@error_handler
def handle_unban_command(message):
    """處理解除禁言用戶的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args:
        bot.reply_to(message, "❌ 使用方式: /unban @用戶名\n例如: /unban @user")
        return
    
    # 解析目標用戶
    target_username = command_args[0].replace('@', '')
    
    # 尋找目標用戶ID
    target_user_id = None
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or f"ID:{target_user_id}"
        else:
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == target_username:
                    target_user_id = member.user.id
                    break
            
            # 如果未找到，嘗試使用正則表達式解析數字ID
            if not target_user_id and command_args[0].isdigit():
                target_user_id = int(command_args[0])
    except Exception as e:
        bot.reply_to(message, f"❌ 尋找目標用戶時出錯: {str(e)}")
        logger.error(f"尋找目標用戶出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, f"❌ 找不到用戶 '{target_username}'")
        return
    
    # 執行解除禁言
    try:
        # 設置完整權限
        bot.restrict_chat_member(
            message.chat.id, 
            target_user_id,
            permissions=telebot.types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        
        # 發送成功訊息
        bot.reply_to(message, f"✅ 已解除禁言用戶 {target_username}")
        logger.info(f"管理員 {message.from_user.username or message.from_user.id} 解除了用戶 {target_username} 的禁言")
    except Exception as e:
        bot.reply_to(message, f"❌ 解除禁言用戶時出錯: {str(e)}")
        logger.error(f"解除禁言用戶出錯: {str(e)}")

# 處理設定操作員指令
@bot.message_handler(regexp=r'^設定操作員\s+(.+)$')
@error_handler
def handle_set_operators(message):
    """處理設定操作員的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析指令參數
    match = re.match(r'^設定操作員\s+(.+)$', message.text)
    if not match:
        bot.reply_to(message, "❌ 使用方式: 設定操作員 @用戶名1 @用戶名2 ...")
        return
    
    operators_text = match.group(1).strip()
    usernames = re.findall(r'@(\w+)', operators_text)
    
    if not usernames:
        bot.reply_to(message, "❌ 未指定任何用戶名。使用方式: 設定操作員 @用戶名1 @用戶名2 ...")
        return
    
    # 加載當前設定
    settings = load_data(USER_SETTINGS_FILE)
    
    # 獲取或創建群組設定
    chat_id_str = str(message.chat.id)
    if chat_id_str not in settings:
        settings[chat_id_str] = {}
    
    if 'operators' not in settings[chat_id_str]:
        settings[chat_id_str]['operators'] = {}
    
    # 查找用戶ID
    added_users = []
    not_found_users = []
    
    for username in usernames:
        user_id = None
        try:
            # 嘗試從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == username:
                    user_id = member.user.id
                    break
            
            # 如果找到用戶，添加到操作員列表
            if user_id:
                settings[chat_id_str]['operators'][str(user_id)] = {
                    'username': username,
                    'added_by': message.from_user.id,
                    'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                added_users.append(f"@{username}")
            else:
                not_found_users.append(f"@{username}")
        except Exception as e:
            logger.error(f"查找用戶 {username} 時出錯: {str(e)}")
            not_found_users.append(f"@{username}")
    
    # 保存設定
    save_data(settings, USER_SETTINGS_FILE)
    
    # 構建回覆訊息
    reply = ""
    if added_users:
        reply += f"✅ 已添加以下操作員:\n{', '.join(added_users)}\n"
    
    if not_found_users:
        reply += f"❌ 找不到以下用戶:\n{', '.join(not_found_users)}"
    
    bot.reply_to(message, reply.strip())
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 設定了操作員: {', '.join(added_users)}")

# 處理查看操作員指令
@bot.message_handler(func=lambda message: message.text == '查看操作員')
@error_handler
def handle_list_operators(message):
    """處理查看操作員的指令"""
    # 加載當前設定
    settings = load_data(USER_SETTINGS_FILE)
    
    # 獲取群組設定
    chat_id_str = str(message.chat.id)
    
    # 檢查是否有操作員設定
    if chat_id_str not in settings or 'operators' not in settings[chat_id_str] or not settings[chat_id_str]['operators']:
        bot.reply_to(message, "📝 當前沒有設定任何操作員")
        return
    
    # 構建操作員列表
    operators = settings[chat_id_str]['operators']
    operator_list = []
    
    for user_id, info in operators.items():
        username = info.get('username', '未知')
        added_time = info.get('added_time', '未知時間')
        operator_list.append(f"@{username} (ID: {user_id})\n添加時間: {added_time}")
    
    # 發送操作員列表
    reply = "📋 當前操作員列表:\n\n" + "\n\n".join(operator_list)
    bot.reply_to(message, reply)
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 查看了操作員列表")

# 處理刪除操作員指令
@bot.message_handler(regexp=r'^刪除操作員\s+(.+)$')
@error_handler
def handle_delete_operators(message):
    """處理刪除操作員的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析指令參數
    match = re.match(r'^刪除操作員\s+(.+)$', message.text)
    if not match:
        bot.reply_to(message, "❌ 使用方式: 刪除操作員 @用戶名1 @用戶名2 ...")
        return
    
    operators_text = match.group(1).strip()
    usernames = re.findall(r'@(\w+)', operators_text)
    
    if not usernames:
        bot.reply_to(message, "❌ 未指定任何用戶名。使用方式: 刪除操作員 @用戶名1 @用戶名2 ...")
        return
    
    # 加載當前設定
    settings = load_data(USER_SETTINGS_FILE)
    
    # 獲取群組設定
    chat_id_str = str(message.chat.id)
    
    # 檢查是否有操作員設定
    if chat_id_str not in settings or 'operators' not in settings[chat_id_str] or not settings[chat_id_str]['operators']:
        bot.reply_to(message, "📝 當前沒有設定任何操作員")
        return
    
    # 刪除指定的操作員
    operators = settings[chat_id_str]['operators']
    deleted_users = []
    not_found_users = []
    
    for username in usernames:
        found = False
        for user_id, info in list(operators.items()):
            if info.get('username') == username:
                del operators[user_id]
                deleted_users.append(f"@{username}")
                found = True
                break
        
        if not found:
            not_found_users.append(f"@{username}")
    
    # 保存設定
    save_data(settings, USER_SETTINGS_FILE)
    
    # 構建回覆訊息
    reply = ""
    if deleted_users:
        reply += f"✅ 已刪除以下操作員:\n{', '.join(deleted_users)}\n"
    
    if not_found_users:
        reply += f"❌ 找不到以下操作員:\n{', '.join(not_found_users)}"
    
    bot.reply_to(message, reply.strip())
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 刪除了操作員: {', '.join(deleted_users)}")

# 處理查看用戶權限指令
@bot.message_handler(commands=['info'])
@error_handler
def handle_user_info(message):
    """處理查看用戶權限的指令"""
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args and not message.reply_to_message:
        bot.reply_to(message, "❌ 使用方式: /info @用戶名 或回覆要查詢的用戶")
        return
    
    # 獲取目標用戶ID
    target_user_id = None
    target_username = None
    
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or str(target_user_id)
        # 如果有指定用戶名
        elif command_args:
            username = command_args[0].replace('@', '')
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == username:
                    target_user_id = member.user.id
                    target_username = username
                    break
    except Exception as e:
        bot.reply_to(message, f"❌ 查找用戶時出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, "❌ 找不到指定的用戶")
        return
    
    # 獲取用戶在群組中的權限狀態
    try:
        user_status = "普通成員"
        user_is_admin = False
        user_is_operator = False
        
        # 檢查是否為管理員
        if is_admin(target_user_id, message.chat.id):
            user_status = "管理員"
            user_is_admin = True
        
        # 檢查是否為操作員
        settings = load_data(USER_SETTINGS_FILE)
        chat_id_str = str(message.chat.id)
        if (chat_id_str in settings and 'operators' in settings[chat_id_str] and 
            str(target_user_id) in settings[chat_id_str]['operators']):
            user_status = "操作員" if not user_is_admin else f"{user_status}、操作員"
            user_is_operator = True
        
        # 獲取用戶詳細資訊
        chat_member = bot.get_chat_member(message.chat.id, target_user_id)
        
        # 構建回覆訊息
        reply = f"👤 用戶資訊: {'@' + target_username if target_username else '未知'}\n"
        reply += f"🆔 用戶ID: {target_user_id}\n"
        reply += f"🏷️ 狀態: {user_status}\n"
        
        if hasattr(chat_member, 'status'):
            reply += f"📊 Telegram狀態: {chat_member.status}\n"
        
        # 如果是操作員，顯示添加時間
        if user_is_operator:
            added_time = settings[chat_id_str]['operators'][str(target_user_id)].get('added_time', '未知時間')
            added_by = settings[chat_id_str]['operators'][str(target_user_id)].get('added_by', '未知')
            reply += f"⏱️ 添加為操作員時間: {added_time}\n"
            reply += f"👤 添加者ID: {added_by}\n"
        
        bot.reply_to(message, reply)
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 查看了用戶 {target_username or target_user_id} 的權限狀態")
    
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取用戶信息時出錯: {str(e)}")
        logger.error(f"獲取用戶信息出錯: {str(e)}")

# 處理踢出用戶指令
@bot.message_handler(commands=['kick'])
@error_handler
def handle_kick_command(message):
    """處理踢出用戶的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args and not message.reply_to_message:
        bot.reply_to(message, "❌ 使用方式: /kick @用戶名 [原因] 或回覆要踢出的用戶")
        return
    
    # 獲取目標用戶ID
    target_user_id = None
    target_username = None
    
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or str(target_user_id)
        # 如果有指定用戶名
        elif command_args:
            username = command_args[0].replace('@', '')
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == username:
                    target_user_id = member.user.id
                    target_username = username
                    break
            
            # 如果未找到，嘗試使用正則表達式解析數字ID
            if not target_user_id and command_args[0].isdigit():
                target_user_id = int(command_args[0])
                target_username = str(target_user_id)
    except Exception as e:
        bot.reply_to(message, f"❌ 查找用戶時出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, "❌ 找不到指定的用戶")
        return
    
    # 解析踢出原因
    reason = "未指定原因"
    if len(command_args) > 1:
        reason = ' '.join(command_args[1:])
    
    # 檢查目標用戶是否為管理員
    if is_admin(target_user_id, message.chat.id):
        bot.reply_to(message, "❌ 無法踢出管理員")
        return
    
    # 執行踢出操作
    try:
        bot.kick_chat_member(message.chat.id, target_user_id)
        bot.unban_chat_member(message.chat.id, target_user_id)  # 立即解除封禁，使用戶可以再次加入
        
        # 發送成功訊息
        bot.reply_to(message, f"✅ 已踢出用戶 {target_username}\n原因: {reason}")
        logger.info(f"管理員 {message.from_user.username or message.from_user.id} 踢出了用戶 {target_username}，原因: {reason}")
    except Exception as e:
        bot.reply_to(message, f"❌ 踢出用戶時出錯: {str(e)}")
        logger.error(f"踢出用戶出錯: {str(e)}")

# 處理查看管理員命令列表
@bot.message_handler(commands=['admin'])
@error_handler
def handle_admin_commands(message):
    """處理查看管理員命令列表的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    admin_commands = """<b>🛠️ 管理員命令列表</b>

<b>👤 成員管理</b>
/kick - 踢出用戶
/ban - 禁言用戶
/unban - 解除禁言

<b>⚠️ 警告系統</b>
/warn - 警告用戶
/unwarn - 移除警告
/warns - 查看用戶警告次數

<b>🧹 清理訊息</b>
/del - 刪除單一訊息

<b>📋 其他</b>
/info - 查看用戶權限
/restart - 重啟機器人
"""
    
    bot.reply_to(message, admin_commands, parse_mode='HTML')
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 查看了管理員命令列表")

# 處理查看管理員名單
@bot.message_handler(func=lambda message: message.text == '📋查看管理員')
@error_handler
def handle_list_admins(message):
    """處理查看群組管理員的請求"""
    try:
        # 獲取群組管理員列表
        admins = bot.get_chat_administrators(message.chat.id)
        
        # 構建管理員列表訊息
        admin_list = []
        for admin in admins:
            status = "👑 群主" if admin.status == "creator" else "👮 管理員"
            username = f"@{admin.user.username}" if admin.user.username else admin.user.first_name
            admin_list.append(f"{status}: {username} (ID: {admin.user.id})")
        
        # 發送管理員列表
        reply = "<b>📋 群組管理員列表</b>\n\n" + "\n".join(admin_list)
        bot.reply_to(message, reply, parse_mode='HTML')
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 查看了群組管理員列表")
    
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取管理員列表時出錯: {str(e)}")
        logger.error(f"獲取管理員列表出錯: {str(e)}")

# 警告系統 - 警告用戶
@bot.message_handler(commands=['warn'])
@error_handler
def handle_warn_command(message):
    """處理警告用戶的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args and not message.reply_to_message:
        bot.reply_to(message, "❌ 使用方式: /warn @用戶名 [原因] 或回覆要警告的用戶")
        return
    
    # 獲取目標用戶ID
    target_user_id = None
    target_username = None
    
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or str(target_user_id)
        # 如果有指定用戶名
        elif command_args:
            username = command_args[0].replace('@', '')
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == username:
                    target_user_id = member.user.id
                    target_username = username
                    break
            
            # 如果未找到，嘗試使用正則表達式解析數字ID
            if not target_user_id and command_args[0].isdigit():
                target_user_id = int(command_args[0])
                target_username = str(target_user_id)
    except Exception as e:
        bot.reply_to(message, f"❌ 查找用戶時出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, "❌ 找不到指定的用戶")
        return
    
    # 解析警告原因
    reason = "未指定原因"
    if len(command_args) > 1:
        reason = ' '.join(command_args[1:])
    
    # 檢查目標用戶是否為管理員
    if is_admin(target_user_id, message.chat.id):
        bot.reply_to(message, "❌ 無法警告管理員")
        return
    
    # 加載警告系統設定
    settings = load_data(USER_SETTINGS_FILE)
    chat_id_str = str(message.chat.id)
    
    # 初始化群組警告系統設定
    if chat_id_str not in settings:
        settings[chat_id_str] = {}
    if 'warnings' not in settings[chat_id_str]:
        settings[chat_id_str]['warnings'] = {}
    
    # 獲取或初始化用戶警告數
    user_id_str = str(target_user_id)
    if user_id_str not in settings[chat_id_str]['warnings']:
        settings[chat_id_str]['warnings'][user_id_str] = {
            'count': 0,
            'reasons': [],
            'warned_by': [],
            'timestamps': []
        }
    
    # 增加警告次數
    settings[chat_id_str]['warnings'][user_id_str]['count'] += 1
    settings[chat_id_str]['warnings'][user_id_str]['reasons'].append(reason)
    settings[chat_id_str]['warnings'][user_id_str]['warned_by'].append(message.from_user.id)
    settings[chat_id_str]['warnings'][user_id_str]['timestamps'].append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 獲取當前警告次數
    warn_count = settings[chat_id_str]['warnings'][user_id_str]['count']
    
    # 檢查是否達到禁言閾值
    if warn_count >= 3:
        try:
            # 設置24小時禁言
            until_date = int((datetime.now() + timedelta(hours=24)).timestamp())
            
            bot.restrict_chat_member(
                message.chat.id, 
                target_user_id,
                permissions=telebot.types.ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                ),
                until_date=until_date
            )
            
            # 重置警告次數
            settings[chat_id_str]['warnings'][user_id_str]['count'] = 0
            settings[chat_id_str]['warnings'][user_id_str]['banned_history'] = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'banned_by': message.from_user.id,
                'reason': f"達到警告上限 ({warn_count}次)"
            }
            
            # 發送禁言通知
            bot.reply_to(message, f"⚠️ 用戶 {target_username} 已收到第 {warn_count} 次警告，已自動禁言24小時。\n原因: {reason}")
        except Exception as e:
            bot.reply_to(message, f"⚠️ 用戶已收到第 {warn_count} 次警告，但禁言失敗: {str(e)}")
    else:
        # 發送警告通知
        bot.reply_to(message, f"⚠️ 已警告用戶 {target_username} ({warn_count}/3)\n原因: {reason}")
    
    # 保存設定
    save_data(settings, USER_SETTINGS_FILE)
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 警告了用戶 {target_username}，原因: {reason}，當前警告: {warn_count}/3")

# 警告系統 - 移除警告
@bot.message_handler(commands=['unwarn'])
@error_handler
def handle_unwarn_command(message):
    """處理移除用戶警告的指令"""
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此功能僅限群組管理員使用")
        return
    
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args and not message.reply_to_message:
        bot.reply_to(message, "❌ 使用方式: /unwarn @用戶名 或回覆要移除警告的用戶")
        return
    
    # 獲取目標用戶ID
    target_user_id = None
    target_username = None
    
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or str(target_user_id)
        # 如果有指定用戶名
        elif command_args:
            username = command_args[0].replace('@', '')
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == username:
                    target_user_id = member.user.id
                    target_username = username
                    break
            
            # 如果未找到，嘗試使用正則表達式解析數字ID
            if not target_user_id and command_args[0].isdigit():
                target_user_id = int(command_args[0])
                target_username = str(target_user_id)
    except Exception as e:
        bot.reply_to(message, f"❌ 查找用戶時出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, "❌ 找不到指定的用戶")
        return
    
    # 加載警告系統設定
    settings = load_data(USER_SETTINGS_FILE)
    chat_id_str = str(message.chat.id)
    
    # 檢查是否有警告記錄
    if (chat_id_str not in settings or 
        'warnings' not in settings[chat_id_str] or 
        str(target_user_id) not in settings[chat_id_str]['warnings'] or
        settings[chat_id_str]['warnings'][str(target_user_id)]['count'] <= 0):
        bot.reply_to(message, f"⚠️ 用戶 {target_username} 目前沒有警告記錄")
        return
    
    # 減少警告次數
    user_id_str = str(target_user_id)
    settings[chat_id_str]['warnings'][user_id_str]['count'] -= 1
    warn_count = settings[chat_id_str]['warnings'][user_id_str]['count']
    
    # 如果有警告記錄，移除最後一條
    if len(settings[chat_id_str]['warnings'][user_id_str]['reasons']) > 0:
        settings[chat_id_str]['warnings'][user_id_str]['reasons'].pop()
    if len(settings[chat_id_str]['warnings'][user_id_str]['warned_by']) > 0:
        settings[chat_id_str]['warnings'][user_id_str]['warned_by'].pop()
    if len(settings[chat_id_str]['warnings'][user_id_str]['timestamps']) > 0:
        settings[chat_id_str]['warnings'][user_id_str]['timestamps'].pop()
    
    # 保存設定
    save_data(settings, USER_SETTINGS_FILE)
    
    # 發送通知
    bot.reply_to(message, f"✅ 已移除用戶 {target_username} 的一次警告，當前警告次數: {warn_count}/3")
    logger.info(f"管理員 {message.from_user.username or message.from_user.id} 移除了用戶 {target_username} 的一次警告，當前警告: {warn_count}/3")

# 警告系統 - 查看警告
@bot.message_handler(commands=['warns'])
@error_handler
def handle_warns_command(message):
    """處理查看用戶警告次數的指令"""
    # 解析命令參數
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not command_args and not message.reply_to_message:
        bot.reply_to(message, "❌ 使用方式: /warns @用戶名 或回覆要查看警告的用戶")
        return
    
    # 獲取目標用戶ID
    target_user_id = None
    target_username = None
    
    try:
        # 如果是回覆某人的訊息
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username or str(target_user_id)
        # 如果有指定用戶名
        elif command_args:
            username = command_args[0].replace('@', '')
            # 從群組成員中尋找
            chat_members = bot.get_chat_administrators(message.chat.id)
            for member in chat_members:
                if member.user.username == username:
                    target_user_id = member.user.id
                    target_username = username
                    break
            
            # 如果未找到，嘗試使用正則表達式解析數字ID
            if not target_user_id and command_args[0].isdigit():
                target_user_id = int(command_args[0])
                target_username = str(target_user_id)
    except Exception as e:
        bot.reply_to(message, f"❌ 查找用戶時出錯: {str(e)}")
        return
    
    if not target_user_id:
        bot.reply_to(message, "❌ 找不到指定的用戶")
        return
    
    # 加載警告系統設定
    settings = load_data(USER_SETTINGS_FILE)
    chat_id_str = str(message.chat.id)
    
    # 檢查是否有警告記錄
    if (chat_id_str not in settings or 
        'warnings' not in settings[chat_id_str] or 
        str(target_user_id) not in settings[chat_id_str]['warnings']):
        bot.reply_to(message, f"⚠️ 用戶 {target_username} 目前沒有警告記錄")
        return
    
    # 獲取警告記錄
    user_id_str = str(target_user_id)
    warn_data = settings[chat_id_str]['warnings'][user_id_str]
    warn_count = warn_data.get('count', 0)
    reasons = warn_data.get('reasons', [])
    timestamps = warn_data.get('timestamps', [])
    
    # 構建回覆訊息
    reply = f"⚠️ 用戶 {target_username} 的警告記錄: {warn_count}/3\n\n"
    
    if warn_count > 0 and len(reasons) > 0:
        for i in range(min(warn_count, len(reasons))):
            timestamp = timestamps[i] if i < len(timestamps) else "未知時間"
            reason = reasons[i]
            reply += f"{i+1}. [{timestamp}] 原因: {reason}\n"
    
    # 檢查是否有禁言歷史
    if 'banned_history' in warn_data:
        ban_info = warn_data['banned_history']
        reply += f"\n上次禁言時間: {ban_info.get('time', '未知')}\n"
        reply += f"原因: {ban_info.get('reason', '未知')}"
    
    bot.reply_to(message, reply)
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 查看了用戶 {target_username} 的警告記錄")

# 處理 "日期 TW+金額" 格式的訊息
@bot.message_handler(regexp=r'^\s*([0-9/\-\.]+)\s+TW\+\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_date_tw_add(message):
    """處理特定日期台幣收入記帳"""
    match = re.match(r'^\s*([0-9/\-\.]+)\s+TW\+\s*(\d+(\.\d+)?)\s*$', message.text)
    date_str = match.group(1)
    amount = float(match.group(2))
    
    date = parse_date(date_str)
    
    add_transaction(message.from_user.id, date, 'TW', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄 {date_display} 的台幣收入：NT${amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了 {date_display} 的台幣收入 {amount}")

# 處理 "日期 TW-金額" 格式的訊息
@bot.message_handler(regexp=r'^\s*([0-9/\-\.]+)\s+TW\-\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_date_tw_subtract(message):
    """處理特定日期台幣支出記帳"""
    match = re.match(r'^\s*([0-9/\-\.]+)\s+TW\-\s*(\d+(\.\d+)?)\s*$', message.text)
    date_str = match.group(1)
    amount = -float(match.group(2))
    
    date = parse_date(date_str)
    
    add_transaction(message.from_user.id, date, 'TW', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄 {date_display} 的台幣支出：NT${-amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了 {date_display} 的台幣支出 {-amount}")

# 處理 "日期 CN+金額" 格式的訊息
@bot.message_handler(regexp=r'^\s*([0-9/\-\.]+)\s+CN\+\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_date_cn_add(message):
    """處理特定日期人民幣收入記帳"""
    match = re.match(r'^\s*([0-9/\-\.]+)\s+CN\+\s*(\d+(\.\d+)?)\s*$', message.text)
    date_str = match.group(1)
    amount = float(match.group(2))
    
    date = parse_date(date_str)
    
    add_transaction(message.from_user.id, date, 'CN', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄 {date_display} 的人民幣收入：CN¥{amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了 {date_display} 的人民幣收入 {amount}")

# 處理 "日期 CN-金額" 格式的訊息
@bot.message_handler(regexp=r'^\s*([0-9/\-\.]+)\s+CN\-\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_date_cn_subtract(message):
    """處理特定日期人民幣支出記帳"""
    match = re.match(r'^\s*([0-9/\-\.]+)\s+CN\-\s*(\d+(\.\d+)?)\s*$', message.text)
    date_str = match.group(1)
    amount = -float(match.group(2))
    
    date = parse_date(date_str)
    
    add_transaction(message.from_user.id, date, 'CN', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄 {date_display} 的人民幣支出：CN¥{-amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了 {date_display} 的人民幣支出 {-amount}")

# 處理直接輸入的 "TW+金額" 格式
@bot.message_handler(regexp=r'^\s*TW\+\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_direct_tw_add(message):
    """處理直接輸入的台幣收入記帳"""
    match = re.match(r'^\s*TW\+\s*(\d+(\.\d+)?)\s*$', message.text)
    amount = float(match.group(1))
    
    # 使用當前日期
    date = datetime.now().strftime('%Y-%m-%d')
    
    add_transaction(message.from_user.id, date, 'TW', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄今日({date_display})的台幣收入：NT${amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了今日的台幣收入 {amount}")

# 處理直接輸入的 "TW-金額" 格式
@bot.message_handler(regexp=r'^\s*TW\-\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_direct_tw_subtract(message):
    """處理直接輸入的台幣支出記帳"""
    match = re.match(r'^\s*TW\-\s*(\d+(\.\d+)?)\s*$', message.text)
    amount = -float(match.group(1))
    
    # 使用當前日期
    date = datetime.now().strftime('%Y-%m-%d')
    
    add_transaction(message.from_user.id, date, 'TW', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄今日({date_display})的台幣支出：NT${-amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了今日的台幣支出 {-amount}")

# 處理直接輸入的 "CN+金額" 格式
@bot.message_handler(regexp=r'^\s*CN\+\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_direct_cn_add(message):
    """處理直接輸入的人民幣收入記帳"""
    match = re.match(r'^\s*CN\+\s*(\d+(\.\d+)?)\s*$', message.text)
    amount = float(match.group(1))
    
    # 使用當前日期
    date = datetime.now().strftime('%Y-%m-%d')
    
    add_transaction(message.from_user.id, date, 'CN', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄今日({date_display})的人民幣收入：CN¥{amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了今日的人民幣收入 {amount}")

# 處理直接輸入的 "CN-金額" 格式
@bot.message_handler(regexp=r'^\s*CN\-\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_direct_cn_subtract(message):
    """處理直接輸入的人民幣支出記帳"""
    match = re.match(r'^\s*CN\-\s*(\d+(\.\d+)?)\s*$', message.text)
    amount = -float(match.group(1))
    
    # 使用當前日期
    date = datetime.now().strftime('%Y-%m-%d')
    
    add_transaction(message.from_user.id, date, 'CN', amount)
    
    date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
    bot.reply_to(message, f"✅ 已記錄今日({date_display})的人民幣支出：CN¥{-amount:,.0f}")
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了今日的人民幣支出 {-amount}")

# 移除既有的處理函數
# 處理直接輸入的記帳格式 - 同時處理多種格式
@bot.message_handler(func=lambda message: (re.match(r'^\s*(?:TW|CN)[+\-]\s*\d+(?:\.\d+)?\s*$', message.text) or 
                                         re.match(r'^\s*(?:[0-9/\-\.]+)\s+(?:TW|CN)[+\-]\s*\d+(?:\.\d+)?\s*$', message.text)) and
                                         not re.match(r'^\s*(總表)?\s*TW\+\?\?\s*CN\+\?\?\s*公桶\+\?\?\s*私人\+\?\?\s*$', message.text, re.IGNORECASE),
                     content_types=['text'])
@error_handler
def handle_accounting_input(message):
    """通用記帳處理函數，支持多種格式
    
    這個函數處理直接在聊天中輸入的記帳指令，不需要透過按鈕點擊。
    支持格式：
    1. 日期 TW+金額 (如 5/01 TW+350000)
    2. 日期 TW-金額 (如 5/01 TW-100)
    3. 日期 CN+金額 (如 5/01 CN+350000)
    4. 日期 CN-金額 (如 5/01 CN-100)
    5. TW+金額 (如 TW+1000)
    6. TW-金額 (如 TW-100)
    7. CN+金額 (如 CN+1000)
    8. CN-金額 (如 CN-100)
    
    注意：此功能與按鈕功能並行，用戶可以直接輸入或使用按鈕回覆。
    """
    text = message.text.strip()
    
    # 檢查是否為帶日期的格式（如 5/01 TW+350000）
    date_match = re.match(r'^\s*([0-9/\-\.]+)\s+(TW|CN)([+\-])\s*(\d+(?:\.\d+)?)\s*$', text)
    if date_match:
        date_str = date_match.group(1)
        currency = date_match.group(2)
        op = date_match.group(3)
        amount = float(date_match.group(4))
        
        # 轉換日期格式
        date = parse_date(date_str)
        date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
        
        # 設置金額
        if op == '-':
            amount = -amount
        
        # 記錄交易
        add_transaction(message.from_user.id, date, currency, amount)
        
        # 回覆確認訊息
        if currency == 'TW':
            currency_symbol = 'NT$'
            if amount > 0:
                reply = f"✅ 已記錄 {date_display} 的台幣收入：{currency_symbol}{abs(amount):,.0f}"
            else:
                reply = f"✅ 已記錄 {date_display} 的台幣支出：{currency_symbol}{abs(amount):,.0f}"
        else:  # CN
            currency_symbol = 'CN¥'
            if amount > 0:
                reply = f"✅ 已記錄 {date_display} 的人民幣收入：{currency_symbol}{abs(amount):,.0f}"
            else:
                reply = f"✅ 已記錄 {date_display} 的人民幣支出：{currency_symbol}{abs(amount):,.0f}"
        
        bot.reply_to(message, reply)
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了 {date_display} 的 {currency} {'收入' if amount > 0 else '支出'} {abs(amount)}")
        return
    
    # 處理不帶日期的格式（如 TW+1000）
    direct_match = re.match(r'^\s*(TW|CN)([+\-])\s*(\d+(?:\.\d+)?)\s*$', text)
    if direct_match:
        currency = direct_match.group(1)
        op = direct_match.group(2)
        amount = float(direct_match.group(3))
        
        # 使用當前日期
        date = datetime.now().strftime('%Y-%m-%d')
        date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
        
        # 設置金額
        if op == '-':
            amount = -amount
        
        # 記錄交易
        add_transaction(message.from_user.id, date, currency, amount)
        
        # 回覆確認訊息
        if currency == 'TW':
            currency_symbol = 'NT$'
            if amount > 0:
                reply = f"✅ 已記錄今日({date_display})的台幣收入：{currency_symbol}{abs(amount):,.0f}"
            else:
                reply = f"✅ 已記錄今日({date_display})的台幣支出：{currency_symbol}{abs(amount):,.0f}"
        else:  # CN
            currency_symbol = 'CN¥'
            if amount > 0:
                reply = f"✅ 已記錄今日({date_display})的人民幣收入：{currency_symbol}{abs(amount):,.0f}"
            else:
                reply = f"✅ 已記錄今日({date_display})的人民幣支出：{currency_symbol}{abs(amount):,.0f}"
        
        bot.reply_to(message, reply)
        logger.info(f"用戶 {message.from_user.username or message.from_user.id} 記錄了今日的 {currency} {'收入' if amount > 0 else '支出'} {abs(amount)}")
        return

# 處理公桶資金管理命令
@bot.message_handler(regexp=r'^\s*公桶([+\-])\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_public_fund(message):
    """處理公桶資金增減指令"""
    # 檢查用戶是否為管理員或操作員
    if not is_admin(message.from_user.id, message.chat.id, check_operator=True):
        bot.reply_to(message, "❌ 此功能僅限管理員或操作員使用")
        return
        
    match = re.match(r'^\s*公桶([+\-])\s*(\d+(\.\d+)?)\s*$', message.text)
    op = match.group(1)
    amount = float(match.group(2))
    
    # 設置金額
    if op == '-':
        amount = -amount
    
    # 更新資金
    update_fund("public", amount)
    
    # 回覆確認訊息
    if amount > 0:
        reply = f"✅ 已添加公桶資金：USDT${amount:.2f}"
    else:
        reply = f"✅ 已從公桶資金中扣除：USDT${-amount:.2f}"
    
    bot.reply_to(message, reply)
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} {'增加' if amount > 0 else '減少'}了公桶資金 {abs(amount)}")

# 處理私人資金管理命令
@bot.message_handler(regexp=r'^\s*私人([+\-])\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_private_fund(message):
    """處理私人資金增減指令"""
    # 檢查用戶是否為管理員或操作員
    if not is_admin(message.from_user.id, message.chat.id, check_operator=True):
        bot.reply_to(message, "❌ 此功能僅限管理員或操作員使用")
        return
        
    match = re.match(r'^\s*私人([+\-])\s*(\d+(\.\d+)?)\s*$', message.text)
    op = match.group(1)
    amount = float(match.group(2))
    
    # 設置金額
    if op == '-':
        amount = -amount
    
    # 更新資金
    update_fund("private", amount)
    
    # 回覆確認訊息
    if amount > 0:
        reply = f"✅ 已添加私人資金：USDT${amount:.2f}"
    else:
        reply = f"✅ 已從私人資金中扣除：USDT${-amount:.2f}"
    
    bot.reply_to(message, reply)
    logger.info(f"用戶 {message.from_user.username or message.from_user.id} {'增加' if amount > 0 else '減少'}了私人資金 {abs(amount)}")

# 關閉機器人
def shutdown_bot():
    """完全關閉機器人進程"""
    global RESTART_FLAG
    RESTART_FLAG = False
    
    logger.info("準備關閉機器人...")
    print("準備關閉機器人...")
    
    # 記錄關閉操作
    logger.info("機器人即將關閉所有進程")
    
    # 立即終止進程
    pid = os.getpid()
    logger.info(f"終止進程 PID={pid}")
    
    # 使用 os.kill 立即終止進程
    os.kill(pid, signal.SIGTERM)

# 處理關閉所有進程命令
@bot.message_handler(func=lambda message: message.text.strip() == '關閉所有進程', content_types=['text'])
@error_handler
def handle_shutdown(message):
    """處理關閉所有進程命令"""
    logger.info(f"收到關閉所有進程命令，發送者: {message.from_user.id}")
    print(f"收到關閉所有進程命令，發送者: {message.from_user.id}")
    
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此命令僅限管理員使用")
        return
    
    # 發送關閉提示
    shutdown_msg = bot.reply_to(message, "⚠️ 機器人即將關閉所有進程...")
    
    # 發送關閉提示到目標群組（如果不是在目標群組中）
    if message.chat.id != TARGET_GROUP_ID:
        try:
            bot.send_message(TARGET_GROUP_ID, "⚠️ 機器人即將關閉所有進程...")
        except Exception as e:
            logger.error(f"無法發送關閉通知到群組: {str(e)}")
    
    # 延遲一下確保消息發送成功
    time.sleep(2)
    
    # 記錄關閉事件
    logger.info(f"管理員 {message.from_user.id} 觸發機器人關閉")
    
    # 關閉機器人
    shutdown_bot()

# 生成總表報告
def generate_total_report(month=None, year=None):
    """生成所有用戶的總表報告，當月業績總計和當日業績"""
    data = load_data(DATA_FILE)
    now = datetime.now()
    
    # 如果未指定月份和年份，使用當前月份和年份
    if month is None:
        month = now.month
    if year is None:
        year = now.year
    
    # 當前日期（用於計算當日業績）
    today = now.strftime('%Y-%m-%d')
    
    # 格式化月份顯示
    month_display = f"{year}年{month}月"
    
    # 初始化結果
    tw_month_total = 0  # 台幣月度總額
    cn_month_total = 0  # 人民幣月度總額
    tw_today_total = 0  # 台幣今日總額
    cn_today_total = 0  # 人民幣今日總額
    
    # 按用戶分類的結果
    users_data = {}
    
    # 遍歷所有用戶數據
    for user_id, user_data in data.items():
        # 獲取用戶名稱
        user_name = get_report_name(user_id)
        
        # 初始化該用戶的數據
        user_tw_month = 0
        user_cn_month = 0
        user_tw_today = 0
        user_cn_today = 0
        
        # 遍歷用戶的所有交易
        for date, currencies in user_data.items():
            # 解析日期
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                
                # 檢查是否為指定的年月
                if date_obj.year == year and date_obj.month == month:
                    # 加入月度總計
                    user_tw_month += currencies.get('TW', 0)
                    user_cn_month += currencies.get('CN', 0)
                    
                    # 如果是今天，也加入今日總計
                    if date == today:
                        user_tw_today += currencies.get('TW', 0)
                        user_cn_today += currencies.get('CN', 0)
            except ValueError:
                continue  # 跳過無效日期
        
        # 加入總計
        tw_month_total += user_tw_month
        cn_month_total += user_cn_month
        tw_today_total += user_tw_today
        cn_today_total += user_cn_today
        
        # 儲存用戶數據
        if user_tw_month != 0 or user_cn_month != 0 or user_tw_today != 0 or user_cn_today != 0:
            users_data[user_name] = {
                'tw_month': user_tw_month,
                'cn_month': user_cn_month,
                'tw_today': user_tw_today,
                'cn_today': user_cn_today
            }
    
    # 計算人民幣轉換為台幣的總額（使用當前匯率）
    current_rate = get_rate()
    cn_to_tw_month = cn_month_total * current_rate
    cn_to_tw_today = cn_today_total * current_rate
    
    # 總計（台幣+人民幣轉台幣）
    total_month_in_tw = tw_month_total + cn_to_tw_month
    total_today_in_tw = tw_today_total + cn_to_tw_today
    
    # 格式化報表
    report = f"📊 <b>總表報告 - {month_display}</b>\n\n"
    
    # 顯示當日總計
    today_date = now.strftime('%m/%d')
    report += f"🗓 <b>今日 ({today_date}) 業績總計</b>\n"
    report += f"————————————————\n"
    report += f"🇹🇼 台幣(TW): NT${tw_today_total:,.0f}\n"
    report += f"🇨🇳 人民幣(CN): CN¥{cn_today_total:,.0f}\n"
    report += f"💹 合計: NT${total_today_in_tw:,.0f}\n\n"
    
    # 顯示當月總計
    report += f"📆 <b>本月業績總計</b>\n"
    report += f"————————————————\n"
    report += f"🇹🇼 台幣(TW): NT${tw_month_total:,.0f}\n"
    report += f"🇨🇳 人民幣(CN): CN¥{cn_month_total:,.0f}\n"
    report += f"💹 合計: NT${total_month_in_tw:,.0f}\n\n"
    
    # 顯示匯率信息
    report += f"💱 當前匯率: {current_rate} (1 CN¥ = {current_rate} NT$)\n\n"
    
    # 顯示各用戶的業績明細
    report += f"👥 <b>個人業績明細</b>\n"
    report += f"————————————————\n"
    
    # 按總業績排序（台幣+人民幣轉台幣）
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: (x[1]['tw_month'] + x[1]['cn_month'] * current_rate),
        reverse=True
    )
    
    for user_name, user_data in sorted_users:
        # 計算該用戶的總業績（轉換為台幣）
        user_total_in_tw = user_data['tw_month'] + (user_data['cn_month'] * current_rate)
        
        # 只顯示當月有業績的用戶
        if user_total_in_tw > 0:
            report += f"\n<b>{user_name}</b>\n"
            
            # 顯示當日業績（如果有）
            if user_data['tw_today'] != 0 or user_data['cn_today'] != 0:
                report += f"今日業績: "
                if user_data['tw_today'] != 0:
                    report += f"NT${user_data['tw_today']:,.0f} "
                if user_data['cn_today'] != 0:
                    report += f"CN¥{user_data['cn_today']:,.0f}"
                report += "\n"
            
            # 顯示當月業績
            report += f"當月業績: "
            if user_data['tw_month'] != 0:
                report += f"NT${user_data['tw_month']:,.0f} "
            if user_data['cn_month'] != 0:
                report += f"CN¥{user_data['cn_month']:,.0f}"
            report += f" (約 NT${user_total_in_tw:,.0f})\n"
    
    return report

# 定義是否運行的標誌
bot_should_run = True

# 定義啟動和關閉機器人的函數
def start_bot_schedule():
    global bot_should_run
    bot_should_run = True
    logging.info("排程任務: 機器人已啟動")
    
    # 向目標群組發送開機通知
    try:
        bot.send_message(TARGET_GROUP_ID, "🟢 機器人已開機，可以正常使用所有功能。")
    except Exception as e:
        logging.error(f"無法發送開機通知到目標群組: {e}")
    
    # 通知管理員
    try:
        admin_ids = get_admin_ids()
        for admin_id in admin_ids:
            try:
                bot.send_message(admin_id, "⏰ 排程任務: 機器人已啟動")
            except Exception as e:
                logging.error(f"無法發送啟動通知給管理員 {admin_id}: {e}")
    except Exception as e:
        logging.error(f"啟動通知錯誤: {e}")

def stop_bot_schedule():
    global bot_should_run
    bot_should_run = False
    logging.info("排程任務: 機器人已停止")
    
    # 向目標群組發送休眠通知
    try:
        bot.send_message(TARGET_GROUP_ID, "🔴 機器人準備休眠，將暫停服務。明天早上將自動開機。")
    except Exception as e:
        logging.error(f"無法發送休眠通知到目標群組: {e}")
    
    # 通知管理員
    try:
        admin_ids = get_admin_ids()
        for admin_id in admin_ids:
            try:
                bot.send_message(admin_id, "⏰ 排程任務: 機器人已停止服務")
            except Exception as e:
                logging.error(f"無法發送停止通知給管理員 {admin_id}: {e}")
    except Exception as e:
        logging.error(f"停止通知錯誤: {e}")

# 設置排程任務
def setup_schedule():
    schedule.every().day.at("07:00").do(start_bot_schedule)
    schedule.every().day.at("02:00").do(stop_bot_schedule)
    
    # 啟動排程檢查線程
    def schedule_checker():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
    
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logging.info("排程系統已啟動")

# 處理直接輸入的 MM/DD 格式 (例如：5/01 TW+10000)
@bot.message_handler(regexp=r'^\s*(\d{1,2}[/\-\.]\d{1,2})\s+(TW|CN)([+\-])\s*(\d+(\.\d+)?)\s*$')
@error_handler
def handle_mmdd_currency_amount(message):
    """處理直接輸入的 MM/DD 貨幣格式 金額 (例如：5/01 TW+10000)"""
    logger.info(f"收到 MM/DD 格式記帳訊息: {message.text} 來自用戶 {message.from_user.username or message.from_user.id}")
    print(f"收到 MM/DD 格式記帳訊息: {message.text}")  # 添加終端輸出便於調試
    
    try:
        match = re.match(r'^\s*(\d{1,2}[/\-\.]\d{1,2})\s+(TW|CN)([+\-])\s*(\d+(\.\d+)?)\s*$', message.text)
        date_str = match.group(1)
        currency = match.group(2)
        op = match.group(3)
        amount = float(match.group(4))
        
        if op == '-':
            amount = -amount
        
        date = parse_date(date_str)
        date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
        
        add_transaction(message.from_user.id, date, currency, amount)
        
        if currency == 'TW':
            currency_display = 'NT$'
            if amount > 0:
                action = '收入'
            else:
                action = '支出'
        else:  # CN
            currency_display = 'CN¥'
            if amount > 0:
                action = '收入'
            else:
                action = '支出'
        
        bot.reply_to(message, f"✅ 已記錄 {date_display} 的{currency}幣{action}：{currency_display}{abs(amount):,.0f}")
        logger.info(f"成功記錄 {date_display} 的{currency}幣{action}：{abs(amount)}")
        
    except Exception as e:
        logger.error(f"處理 MM/DD 格式記帳出錯: {str(e)}\n{traceback.format_exc()}")
        bot.reply_to(message, f"❌ 處理記帳指令時出錯：{str(e)}")

# 處理更靈活的記帳格式
@bot.message_handler(func=lambda message: 
    (re.match(r'^\s*(?:tw|TW|台幣)\s*[+＋-－]\s*\d+(?:\.\d+)?\s*$', message.text, re.IGNORECASE) or 
    re.match(r'^\s*(?:cn|CN|人民幣)\s*[+＋-－]\s*\d+(?:\.\d+)?\s*$', message.text, re.IGNORECASE) or
    re.match(r'^\s*(?:[0-9]+[/\-\.][0-9]+)\s+(?:tw|TW|台幣|cn|CN|人民幣)\s*[+＋-－]\s*\d+(?:\.\d+)?\s*$', message.text, re.IGNORECASE)) and
    not re.match(r'^\s*(總表)?\s*TW\+\?\?\s*CN\+\?\?\s*公桶\+\?\?\s*私人\+\?\?\s*$', message.text, re.IGNORECASE),
    content_types=['text'])
@error_handler
def handle_flexible_accounting(message):
    """處理更靈活的記帳格式，支援多種輸入方式"""
    try:
        text = message.text.strip()
        logger.info(f"收到靈活記帳指令: {text}")
        
        # 處理日期 + 貨幣 + 金額格式 (如 "5/1 tw+100")
        date_match = re.match(
            r'^\s*([0-9]+[/\-\.][0-9]+)\s+(tw|TW|台幣|cn|CN|人民幣)\s*([+＋-－])\s*(\d+(?:\.\d+)?)\s*$', 
            text, 
            re.IGNORECASE
        )
        
        if date_match:
            date_str = date_match.group(1)
            currency_raw = date_match.group(2).upper()
            op_raw = date_match.group(3)
            amount = float(date_match.group(4))
            
            # 標準化貨幣類型
            currency = 'TW' if currency_raw.upper() in ['TW', '台幣'] else 'CN'
            
            # 標準化操作符號
            op = '+' if op_raw in ['+', '＋'] else '-'
            
            # 如果是減號，金額轉為負數
            if op == '-':
                amount = -amount
                
            # 處理日期
            date = parse_date(date_str)
            date_display = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d')
            
            # 記錄交易
            add_transaction(message.from_user.id, date, currency, amount)
            
            # 回覆確認
            currency_display = 'NT$' if currency == 'TW' else 'CN¥'
            action = '收入' if amount > 0 else '支出'
            
            bot.reply_to(
                message, 
                f"✅ 已記錄 {date_display} 的{currency}幣{action}：{currency_display}{abs(amount):,.0f}"
            )
            return
        
        # 處理貨幣 + 金額格式 (如 "tw+100", "CN-200")
        direct_match = re.match(
            r'^\s*(tw|TW|台幣|cn|CN|人民幣)\s*([+＋-－])\s*(\d+(?:\.\d+)?)\s*$', 
            text, 
            re.IGNORECASE
        )
        
        if direct_match:
            currency_raw = direct_match.group(1).upper()
            op_raw = direct_match.group(2)
            amount = float(direct_match.group(3))
            
            # 標準化貨幣類型
            currency = 'TW' if currency_raw.upper() in ['TW', '台幣'] else 'CN'
            
            # 標準化操作符號
            op = '+' if op_raw in ['+', '＋'] else '-'
            
            # 如果是減號，金額轉為負數
            if op == '-':
                amount = -amount
                
            # 今日日期
            date = datetime.now().strftime('%Y-%m-%d')
            
            # 記錄交易
            add_transaction(message.from_user.id, date, currency, amount)
            
            # 回覆確認
            currency_display = 'NT$' if currency == 'TW' else 'CN¥'
            action = '收入' if amount > 0 else '支出'
            
            bot.reply_to(
                message, 
                f"✅ 已記錄今日{currency}幣{action}：{currency_display}{abs(amount):,.0f}"
            )
            return
        
    except Exception as e:
        bot.reply_to(message, f"❌ 處理指令時出錯：{str(e)}")
        logger.error(f"處理靈活記帳指令出錯: {str(e)}\n{traceback.format_exc()}")

# 處理更靈活的資金操作格式
@bot.message_handler(func=lambda message: 
    (re.match(r'^\s*(?:公桶|公共|公共資金)\s*[+＋-－]\s*\d+(?:\.\d+)?\s*$', message.text, re.IGNORECASE) or 
    re.match(r'^\s*(?:私人|私人資金)\s*[+＋-－]\s*\d+(?:\.\d+)?\s*$', message.text, re.IGNORECASE)) and
    not re.match(r'^\s*(總表)?\s*TW\+\?\?\s*CN\+\?\?\s*公桶\+\?\?\s*私人\+\?\?\s*$', message.text, re.IGNORECASE),
    content_types=['text'])
@error_handler
def handle_flexible_fund(message):
    """處理更靈活的資金操作格式"""
    try:
        # 檢查用戶是否為管理員或操作員
        if not is_admin(message.from_user.id, message.chat.id, check_operator=True):
            bot.reply_to(message, "❌ 此功能僅限管理員或操作員使用")
            return
            
        text = message.text.strip()
        logger.info(f"收到靈活資金操作指令: {text}")
        
        # 公桶資金操作
        public_match = re.match(
            r'^\s*(?:公桶|公共|公共資金)\s*([+＋-－])\s*(\d+(?:\.\d+)?)\s*$', 
            text, 
            re.IGNORECASE
        )
        
        if public_match:
            op_raw = public_match.group(1)
            amount = float(public_match.group(2))
            
            # 標準化操作符號
            op = '+' if op_raw in ['+', '＋'] else '-'
            
            # 如果是減號，金額轉為負數
            if op == '-':
                amount = -amount
                
            # 更新資金
            update_fund("public", amount)
            
            # 回覆確認
            if amount > 0:
                reply = f"✅ 已添加公桶資金：USDT${amount:.2f}"
            else:
                reply = f"✅ 已從公桶資金中扣除：USDT${-amount:.2f}"
                
            bot.reply_to(message, reply)
            return
            
        # 私人資金操作
        private_match = re.match(
            r'^\s*(?:私人|私人資金)\s*([+＋-－])\s*(\d+(?:\.\d+)?)\s*$', 
            text, 
            re.IGNORECASE
        )
        
        if private_match:
            op_raw = private_match.group(1)
            amount = float(private_match.group(2))
            
            # 標準化操作符號
            op = '+' if op_raw in ['+', '＋'] else '-'
            
            # 如果是減號，金額轉為負數
            if op == '-':
                amount = -amount
                
            # 更新資金
            update_fund("private", amount)
            
            # 回覆確認
            if amount > 0:
                reply = f"✅ 已添加私人資金：USDT${amount:.2f}"
            else:
                reply = f"✅ 已從私人資金中扣除：USDT${-amount:.2f}"
                
            bot.reply_to(message, reply)
            return
        
    except Exception as e:
        bot.reply_to(message, f"❌ 處理指令時出錯：{str(e)}")
        logger.error(f"處理靈活資金操作指令出錯: {str(e)}\n{traceback.format_exc()}")

@bot.message_handler(commands=['help'])
@error_handler
def handle_help_command(message):
    handle_help(message)

# 優先處理總表請求 - 置於前方以確保優先級
@bot.message_handler(func=lambda message: 
    message.text in ['📊總表', '總表', '📊 總表'] or 
    message.text.strip().startswith('總表') or
    re.match(r'^\s*(總表)?\s*TW\+\?\?\s*CN\+\?\?\s*公桶\+\?\?\s*私人\+\?\?\s*$', message.text, re.IGNORECASE),
    content_types=['text'])
@error_handler
def handle_total_report_priority(message):
    """處理總表命令，顯示所有用戶的業績總表，支持多種格式的請求 (優先處理)"""
    try:
        # 添加更詳細的日誌
        logger.info(f"收到總表請求: '{message.text}' 從用戶ID: {message.from_user.id}, 用戶名: {message.from_user.username or '未設置'}")
        print(f"處理總表請求: {message.text}")
        
        # 生成總表報告
        report = generate_total_report()
        
        # 發送報告
        sent_msg = bot.reply_to(message, report, parse_mode='HTML')
        logger.info(f"已發送總表報告，訊息ID: {sent_msg.message_id}")
        print(f"已發送總表報告給用戶ID: {message.from_user.id}")
    except Exception as e:
        logger.error(f"處理總表報告時出錯: {str(e)}\n{traceback.format_exc()}")
        print(f"總表處理錯誤: {str(e)}")
        bot.reply_to(message, f"❌ 生成總表報告時出錯：{str(e)}")

@bot.message_handler(func=lambda message: message.text.strip() == '重啟', content_types=['text'])
@error_handler
def handle_restart_text_priority(message):
    """處理純文字「重啟」命令，功能與 /restart 相同，高優先級版本"""
    logger.info(f"收到重啟命令(高優先級處理)，發送者: {message.from_user.id}")
    print(f"收到重啟命令(高優先級處理)，發送者: {message.from_user.id}")
    
    # 檢查是否為管理員
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此命令僅限管理員使用")
        return
    
    # 發送重啟提示
    restart_msg = bot.reply_to(message, "🔄 機器人即將重新啟動，請稍候...")
    
    # 發送重啟提示到目標群組（如果不是在目標群組中）
    if message.chat.id != TARGET_GROUP_ID:
        try:
            bot.send_message(TARGET_GROUP_ID, "🔄 機器人正在重新啟動，請稍候...")
        except Exception as e:
            logger.error(f"無法發送重啟通知到群組: {str(e)}")
    
    # 延遲一下確保消息發送成功
    time.sleep(2)
    
    # 記錄重啟事件
    logger.info(f"管理員 {message.from_user.id} 觸發機器人重啟")
    
    # 設置重啟標記
    with open("restart_flag.txt", "w") as f:
        f.write(str(datetime.now()))
    
    # 重啟機器人
    restart_bot()

# 在文件初始部分添加額外的調試配置
import sys
DEBUG_MODE = True  # 設置為True開啟額外調試

if DEBUG_MODE:
    print("=== 機器人啟動於調試模式 ===")

# 添加一個簡單的測試命令處理函數，放在優先位置
@bot.message_handler(commands=['test', 'ping'])
@error_handler
def handle_test_command(message):
    """處理測試命令，用於檢查機器人是否正常響應"""
    print(f"收到測試命令: {message.text} 從用戶ID: {message.from_user.id}")
    logger.info(f"收到測試命令: {message.text} 從用戶ID: {message.from_user.id}")
    
    try:
        # 發送回應消息
        sent_msg = bot.reply_to(message, "✅ 機器人正常運行中！")
        logger.info(f"已發送測試回應，消息ID: {sent_msg.message_id}")
    except Exception as e:
        error_msg = f"測試命令處理錯誤: {str(e)}"
        print(error_msg)
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        try:
            bot.reply_to(message, f"❌ 測試失敗: {str(e)}")
        except:
            print("無法發送錯誤回應")

# 添加一個通用消息處理器用於調試，放在文件的最後部分
if DEBUG_MODE:
    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def handle_all_messages(message):
        """捕獲所有未被其他處理器處理的消息（僅調試用）"""
        print(f"收到未處理的消息: '{message.text}' 從用戶ID: {message.from_user.id}")
        logger.info(f"收到未處理的消息: '{message.text}' 從用戶ID: {message.from_user.id}")
        # 在調試模式下，可以選擇是否回應
        # bot.reply_to(message, "⚠️ 抱歉，無法處理此指令。")

# 添加鎖定機制防止多實例
LOCK_FILE = "bot_instance.lock"

def check_instance_running():
    """檢查是否已有實例在運行"""
    try:
        # 檢查鎖文件是否存在
        if os.path.exists(LOCK_FILE):
            # 讀取PID
            with open(LOCK_FILE, 'r') as f:
                pid = f.read().strip()
                
            # 檢查進程是否存在
            try:
                if platform.system() == "Windows":
                    # Windows下檢查進程
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    SYNCHRONIZE = 0x100000
                    process = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
                    if process != 0:
                        kernel32.CloseHandle(process)
                        return True
                else:
                    # Linux/Unix下檢查進程
                    os.kill(int(pid), 0)
                    return True
            except (OSError, ValueError):
                # 進程不存在，可以安全刪除鎖文件
                pass
                
            # 舊鎖文件對應的進程已不存在，刪除它
            os.remove(LOCK_FILE)
            
        # 創建新的鎖文件
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
            
        return False
        
    except Exception as e:
        print(f"檢查實例時出錯: {e}")
        return False

def release_lock():
    """釋放鎖文件"""
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
            print("鎖文件已移除")
        except Exception as e:
            print(f"移除鎖文件時出錯: {e}")

# 設置網絡重試
def create_robust_session():
    """創建具有重試功能的請求會話"""
    session = requests.Session()
    retry_strategy = requests.adapters.Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# 修改主循環部分
if __name__ == "__main__":
    try:
        # 檢查是否已有實例在運行
        if check_instance_running():
            print("檢測到另一個機器人實例已在運行！終止此實例。")
            sys.exit(1)
            
        # 設置退出處理
        def handle_exit(*args, **kwargs):
            print("接收到退出信號，正在清理...")
            release_lock()
            sys.exit(0)
            
        # 註冊信號處理
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)
        
        # 使用自定義會話
        apihelper.SESSION = create_robust_session()
        
        # 設置更長的連接超時
        apihelper.READ_TIMEOUT = 30
        apihelper.CONNECT_TIMEOUT = 10
        
        # 設置日誌
        setup_logging()
        # 初始化檔案
        init_files()
        # 設置排程
        setup_schedule()
        # 發送啟動通知
        send_startup_notification()
        # 啟動心跳檢測
        start_heartbeat()
        # 設置定時清理任務
        schedule_cleaning()
        
        logging.info("機器人已啟動並開始監聽...")
        print("=== 機器人已啟動並開始監聽 ===")
        
        # 修改為考慮排程的無限循環
        print("開始輪詢消息...")
        reconnect_count = 0
        
        while True:
            try:
                if bot_should_run:
                    print(f"正在輪詢消息中... (重連次數: {reconnect_count})")
                    # 使用非線程輪詢，以避免多線程衝突
                    bot.polling(none_stop=True, interval=3, timeout=30, long_polling_timeout=10)
                    print("輪詢週期結束")
                else:
                    print("機器人當前設定為不運行狀態")
                    # 當機器人應該停止時，每分鐘醒來一次檢查狀態
                    time.sleep(60)
                    
                # 如果沒有異常，重置重連計數
                reconnect_count = 0
                    
            except requests.exceptions.ConnectionError as e:
                error_msg = f"連接錯誤: {e}"
                print(error_msg)
                logging.error(error_msg)
                reconnect_count += 1
                # 連接錯誤後等待時間隨重連次數增加
                sleep_time = min(30, 5 * reconnect_count)
                print(f"等待 {sleep_time} 秒後重試...")
                time.sleep(sleep_time)
                
            except telebot.apihelper.ApiTelegramException as e:
                if "Conflict" in str(e):
                    error_msg = f"API衝突錯誤(可能有多個實例): {e}"
                    print(error_msg)
                    logging.error(error_msg)
                    # 衝突錯誤需要較長等待
                    time.sleep(10)
                else:
                    error_msg = f"Telegram API錯誤: {e}"
                    print(error_msg)
                    logging.error(error_msg)
                    time.sleep(5)
                
            except Exception as e:
                error_msg = f"機器人運行出錯: {e}\n{traceback.format_exc()}"
                print(error_msg)
                logging.error(error_msg)
                # 其他錯誤後等待 5 秒再重試
                time.sleep(5)
                
    except KeyboardInterrupt:
        logging.info("接收到鍵盤中斷，正在關閉機器人...")
        print("接收到鍵盤中斷，正在關閉機器人...")
        release_lock()
        shutdown_bot()
    except Exception as e:
        print(f"主程序異常: {e}")
        logging.error(f"主程序異常: {e}\n{traceback.format_exc()}")
        release_lock()
        sys.exit(1)