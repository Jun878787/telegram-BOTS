#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
import time
import datetime
import pytz
import re
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import Config
from accounting import Accounting
import json

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

#!/usr/bin/env python
# -*- coding: utf-8 -*-



# 導入自定義功能模塊
try:
    from accounting_functions import (
        initialize_data, save_data, add_vehicle, add_income, 
        add_expense, get_vehicle_report, get_summary_report
    )
except ImportError:
    print("錯誤: 找不到 accounting_functions.py 模塊")
    sys.exit(1)

try:
    # 嘗試導入 python-telegram-bot v13.x 的模塊
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
    from telegram import Bot, Update, ParseMode
    
    # 設置版本標記
    PTB_VERSION_20 = False
except ImportError as e:
    print("錯誤：請安裝 python-telegram-bot 13.x 版本")
    print("執行：pip install python-telegram-bot==13.15")
    sys.exit(1)

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

# 對話狀態
(
    VEHICLE_ID, VEHICLE_INFO, 
    INCOME_VEHICLE_ID, INCOME_AMOUNT, INCOME_DESCRIPTION,
    EXPENSE_VEHICLE_ID, EXPENSE_AMOUNT, EXPENSE_CATEGORY, EXPENSE_DESCRIPTION,
    REPORT_VEHICLE_ID
) = range(10)

# 初始化數據
data = initialize_data()

# 初始化機器人和配置
bot = telebot.TeleBot('8076453380:AAHnaGkOtryyS-KecrnXcSq0agPclRTrUkQ')
config = Config()
accounting = Accounting()

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

def create_admin_settings_keyboard():
    """創建群管設定鍵盤"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton('👋歡迎詞設定'),
        KeyboardButton('👋🏻告別詞設定')
    )
    keyboard.row(
        KeyboardButton('⚡️快速指令'),
        KeyboardButton('📋查看管理員')
    )
    keyboard.row(
        KeyboardButton('🔍查看操作員'),
        KeyboardButton('🔙返回主選單')
    )
    return keyboard

def create_farewell_settings_keyboard():
    """創建告別詞設定鍵盤"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton('❎關閉告別訊息'),
        KeyboardButton('✅開啟告別訊息')
    )
    keyboard.row(
        KeyboardButton('✍️自訂告別訊息'),
        KeyboardButton('🚮刪除舊的告別訊息')
    )
    keyboard.row(
        KeyboardButton('🔙返回群管功能')
    )
    return keyboard

def get_admin_settings_message():
    """獲取群管設定說明"""
    return """🔧 群組管理設定

可用功能：
1️⃣ 👋歡迎詞設定：設定新成員加入時的歡迎詞
2️⃣ ⚡️快速指令：查看所有管理員指令
3️⃣ 📋查看管理員：列出目前群組的所有管理員
4️⃣ 🔍查看操作員：列出目前設定的操作員

群管指令：
/ban - 禁言用戶
/unban - 解除禁言
/kick - 踢出用戶
/warn - 警告用戶
/unwarn - 移除警告
/warns - 查看警告次數
/info - 查看用戶資訊
/del - 刪除訊息"""

@bot.message_handler(func=lambda message: message.text == '🔧群管功能')
def handle_admin_settings(message):
    """處理群管功能請求"""
    try:
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 發送群管設定說明
        bot.reply_to(message, get_admin_settings_message(), reply_markup=create_admin_settings_keyboard())
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示群管設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🔙返回主選單')
def handle_return_main_menu(message):
    """處理返回主選單"""
    bot.reply_to(message, "已返回主選單", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text == '👋歡迎詞設定')
def handle_welcome_settings(message):
    """處理歡迎詞設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        help_text = """👋 歡迎詞設定說明

目前歡迎詞：
👋 歡迎 {SURNAME} Go to 北金 North™Sea ᴍ8ᴘ👋

可用變數：
{SURNAME} - 新成員的用戶名
{FULLNAME} - 新成員的完整名稱
{FIRSTNAME} - 新成員的名字
{GROUPNAME} - 群組名稱

設定方式：
直接回覆 "設定歡迎詞：" 加上您要的歡迎詞內容
例如：設定歡迎詞：歡迎 {SURNAME} 加入我們！"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示歡迎詞設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '👋🏻告別詞設定')
def handle_farewell_settings(message):
    """處理告別詞設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 獲取當前狀態
        enabled = config.get_farewell_enabled()
        status = "✅ 開啟" if enabled else "❎ 關閉"
        
        help_text = f"""👋🏻 告別模板
從此選單中，您可以設定當有人離開群組時將在群組中發送的告別訊息。

狀態: {status}

可用變數：
{SURNAME} - 離開成員的用戶名
{FULLNAME} - 離開成員的完整名稱
{FIRSTNAME} - 離開成員的名字
{GROUPNAME} - 群組名稱

當前告別詞：
{config.get_farewell_message()}"""
        
        bot.reply_to(message, help_text, reply_markup=create_farewell_settings_keyboard())
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示告別詞設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '❎關閉告別訊息')
def handle_disable_farewell(message):
    """處理關閉告別訊息"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        config.set_farewell_enabled(False)
        bot.reply_to(message, "✅ 已關閉告別訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 關閉告別訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '✅開啟告別訊息')
def handle_enable_farewell(message):
    """處理開啟告別訊息"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        config.set_farewell_enabled(True)
        bot.reply_to(message, "✅ 已開啟告別訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 開啟告別訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '✍️自訂告別訊息')
def handle_custom_farewell(message):
    """處理自訂告別訊息"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        help_text = """請直接回覆 "設定告別詞：" 加上您要的告別詞內容
例如：設定告別詞：👋 {SURNAME} 已離開群組，期待再相會！

可用變數：
{SURNAME} - 離開成員的用戶名
{FULLNAME} - 離開成員的完整名稱
{FIRSTNAME} - 離開成員的名字
{GROUPNAME} - 群組名稱"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示自訂告別訊息說明時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定告別詞：'))
def handle_set_farewell(message):
    """處理設定告別詞"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        farewell_text = message.text.replace('設定告別詞：', '').strip()
        if not farewell_text:
            bot.reply_to(message, "❌ 告別詞不能為空")
            return
        
        config.set_farewell_message(farewell_text)
        bot.reply_to(message, f"✅ 已設定新的告別詞：\n\n{farewell_text}")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定告別詞時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🚮刪除舊的告別訊息')
def handle_clear_old_farewell(message):
    """處理刪除舊的告別訊息"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 獲取當前消息ID
        current_message_id = message.message_id
        
        # 從當前消息開始往前搜尋並刪除告別訊息
        for msg_id in range(current_message_id, 0, -1):
            try:
                msg = bot.get_chat_message(message.chat.id, msg_id)
                if msg and msg.text and "已離開群組" in msg.text:
                    bot.delete_message(message.chat.id, msg_id)
            except:
                continue
        
        bot.reply_to(message, "✅ 已清理舊的告別訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 清理舊的告別訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🔙返回群管功能')
def handle_return_admin_settings(message):
    """處理返回群管功能"""
    handle_admin_settings(message)

@bot.message_handler(func=lambda message: message.text == '⚡️快速指令')
def handle_quick_commands(message):
    """處理快速指令查看"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        bot.reply_to(message, get_admin_commands_message())
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示快速指令時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '📋查看管理員')
def handle_list_admins(message):
    """處理查看管理員列表"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 獲取群組管理員列表
        admins = bot.get_chat_administrators(message.chat.id)
        
        admin_list = "📋 群組管理員列表：\n\n"
        for admin in admins:
            user = admin.user
            status = "👑 群主" if admin.status == "creator" else "👮‍♂️ 管理員"
            admin_list += f"{status}：@{user.username or user.first_name}\n"
        
        bot.reply_to(message, admin_list)
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取管理員列表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🔍查看操作員')
def handle_list_operators(message):
    """處理查看操作員列表"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        operators = config.get_operators()
        if not operators:
            bot.reply_to(message, "目前沒有設定任何操作員")
            return
        
        operator_list = "🔍 操作員列表：\n\n"
        for operator_id in operators:
            try:
                user = bot.get_chat_member(message.chat.id, operator_id).user
                operator_list += f"@{user.username or user.first_name}\n"
            except:
                operator_list += f"ID: {operator_id}\n"
        
        bot.reply_to(message, operator_list)
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取操作員列表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定歡迎詞：'))
def handle_set_welcome(message):
    """處理設定歡迎詞"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        welcome_text = message.text.replace('設定歡迎詞：', '').strip()
        if not welcome_text:
            bot.reply_to(message, "❌ 歡迎詞不能為空")
            return
        
        config.set_welcome_message(welcome_text)
        bot.reply_to(message, f"✅ 已設定新的歡迎詞：\n\n{welcome_text}")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定歡迎詞時發生錯誤：{str(e)}")

def format_time(time_str):
    """格式化時間為 HHMM 格式"""
    if not time_str:
        return ''
    
    # 移除所有空格
    time_str = time_str.strip()
    
    # 處理 "4月16日 下午：16:30" 這樣的格式
    date_time_match = re.search(r'\d+月\d+日.*?(\d{1,2})[.:：](\d{2})', time_str)
    if date_time_match:
        hour = int(date_time_match.group(1))
        minute = int(date_time_match.group(2))
        return f"{hour:02d}:{minute:02d}"
    
    # 處理 "下午16:30" 或 "16:30" 格式
    time_match = re.search(r'(?:[上下午早晚]午?\s*)?(\d{1,2})[.:：](\d{2})', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        return f"{hour:02d}:{minute:02d}"
    
    return time_str

def format_customer_name(name):
    """格式化客戶名稱"""
    if not name:
        return ''
    name = name.strip()
    # 如果只有一個字
    if len(name) == 1:
        return f"{name}先生/小姐"
    return name

def format_company_name(name):
    """格式化公司名稱（取前四個字）"""
    if not name:
        return ''
    # 移除空格並取前四個字
    name = name.strip()
    return name[:4]

def format_amount(amount_str):
    """格式化金額為 XX.X萬 格式"""
    if not amount_str:
        return '0.0'
    
    # 移除所有空格和逗號
    amount_str = amount_str.replace(' ', '').replace(',', '')
    
    # 處理帶有"萬"字的情況
    if '萬' in amount_str:
        amount_str = amount_str.replace('萬', '')
        try:
            return f"{float(amount_str):.1f}"
        except ValueError:
            return '0.0'
    
    # 處理一般數字
    try:
        amount = float(amount_str)
        # 轉換為萬為單位
        return f"{amount/10000:.1f}"
    except ValueError:
        return '0.0'

def extract_district(address):
    """提取地址中的縣市區鄉鎮"""
    if not address:
        return ''
    
    # 統一將台改為臺
    address = address.replace('台', '臺')
    
    # 匹配完整的縣市區鄉鎮格式
    match = re.search(r'([臺台][北中南東西][市縣])([^市縣]{1,3}[區鄉鎮市])', address)
    if match:
        city = match.group(1).replace('臺', '台')
        district = match.group(2)
        return f"{city}{district}"
    
    return address

def find_company_name(text):
    """從文本中搜尋公司名稱"""
    if not text:
        return ''
    
    # 搜尋包含"有限公司"或"股份有限公司"的完整名稱
    company_patterns = [
        r'([^\n\r]+?股份有限公司)',  # 匹配股份有限公司
        r'([^\n\r]+?有限公司)',      # 匹配一般有限公司
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            company_name = match.group(1).strip()
            # 如果公司名稱超過4個字，只取前4個字
            if len(company_name) > 4:
                return company_name[:4]
            return company_name
    
    return ''

def extract_information(text, field_names):
    """從文本中提取指定字段的信息"""
    if not text:
        return ''
    
    # 按行搜索
    lines = text.split('\n')
    for line in lines:
        for field_name in field_names:
            # 處理帶數字編號的格式（如：1.客戶名稱、2.電話）
            field_pattern = f'(?:(?:\\d+\\.)?{field_name}|{field_name})[:：]\\s*'
            match = re.search(field_pattern, line)
            if match:
                value = line[match.end():].strip()
                return value
    
    # 如果是在找公司名稱且沒有找到，嘗試自動搜尋
    if '公司名稱' in field_names:
        return find_company_name(text)
    
    return ''

@bot.message_handler(func=lambda message: message.text == '列表' and message.reply_to_message)
def handle_list_command(message):
    """處理列表命令"""
    original_text = message.reply_to_message.text
    if not original_text:
        return

    # 提取各項信息
    company_name = format_company_name(extract_information(original_text, ['公司名稱']))
    customer_name = format_customer_name(extract_information(original_text, ['客戶名稱', '客戶姓名', '客戶', '姓名', '姓名：']))
    
    # 處理金額，支援"X萬"格式
    amount_text = extract_information(original_text, ['收款金額', '儲值金額', '額度', '金額', '存入操作金額'])
    amount = format_amount(amount_text)
    
    # 處理時間
    time = format_time(extract_information(original_text, ['時間', '收款時間', '預約時間', '日期時間']))
    
    # 處理地址
    address = extract_district(extract_information(original_text, ['公司地址', '預約地址', '收款地址', '收款地點', '交易地點', '地點']))

    # 格式化消息
    formatted_message = f'{time}【{company_name}-{amount}萬】{customer_name}【{address}】'

    # 發送格式化消息
    bot.reply_to(message, formatted_message)

def format_summary(amount, rate):
    """格式化金額和USDT"""
    try:
        amount = float(amount)
        rate = float(rate)
        usdt = amount / rate if rate > 0 else 0
        return f"{amount:,.0f} | {usdt:.2f}(USDT)"
    except (ValueError, TypeError):
        return "0 | 0.00(USDT)"

def get_transaction_message():
    """生成交易摘要消息"""
    try:
        summary = config.get_transaction_summary()
        rates = config.get_rates()
        
        # 入款部分 - 只顯示最近 2 筆
        message = f"🟢入款（{summary['deposit_count']}筆）：\n"
        if summary['deposits']:
            recent_deposits = summary['deposits'][-2:]  # 只取最後 2 筆
            for deposit in recent_deposits:
                time = format_time(deposit['time'])
                message += f"{time} {deposit['amount']:,.0f}\n"
        else:
            message += "暫無入款\n"
        
        # 出款部分
        message += f"\n🔴出款（{summary['withdrawal_count']}筆）：\n"
        if summary['withdrawals']:
            for withdrawal in summary['withdrawals']:
                time = format_time(withdrawal['time'])
                amount = abs(withdrawal['amount'])  # 使用絕對值
                message += f"{time} -{amount:,.0f}\n"
        else:
            message += "暫無出款\n"
        
        # 匯率信息
        message += f"\n入款匯率：{rates['deposit']}"
        message += f"\n出款匯率：{rates['withdrawal']}"
        message += f"\n總入款金額：{summary['total_deposit']:,.0f}"
        
        # 計算下發金額
        total_deposit = float(summary['total_deposit'])
        processed_amount = float(summary['processed_amount'])
        unprocessed_amount = total_deposit - processed_amount
        
        # 下發信息
        message += f"\n\n應下發：{format_summary(total_deposit, rates['deposit'])}"
        
        # 已下發金額顯示為正數，並使用出款匯率計算USDT
        withdrawal_rate = float(rates['withdrawal'])
        if processed_amount != 0:
            processed_amount_abs = abs(processed_amount)
            usdt_amount = processed_amount_abs / withdrawal_rate if withdrawal_rate > 0 else 0
            message += f"\n已下發：{processed_amount_abs:,.0f} | {usdt_amount:.2f}(USDT)"
        else:
            message += f"\n已下發：0 | 0.00(USDT)"
            
        # 未下發金額
        message += f"\n未下發：{format_summary(unprocessed_amount, rates['withdrawal'])}"
        
        return message
    except Exception as e:
        print(f"生成交易摘要時發生錯誤：{str(e)}")
        return "生成交易摘要時發生錯誤"

def get_history_message():
    """生成歷史帳單消息"""
    try:
        summary = config.get_transaction_summary()
        
        message = "📜 歷史帳單：\n\n"
        
        # 顯示所有入款記錄
        message += "🟢入款記錄：\n"
        if summary['deposits']:
            for deposit in summary['deposits']:
                time = format_time(deposit['time'])
                message += f"{time} +{deposit['amount']:,.0f}\n"
        else:
            message += "暫無入款記錄\n"
        
        # 顯示所有出款記錄
        message += "\n🔴出款記錄：\n"
        if summary['withdrawals']:
            for withdrawal in summary['withdrawals']:
                time = format_time(withdrawal['time'])
                message += f"{time} -{withdrawal['amount']:,.0f}\n"
        else:
            message += "暫無出款記錄\n"
        
        return message
    except Exception as e:
        print(f"生成歷史帳單時發生錯誤：{str(e)}")
        return "生成歷史帳單時發生錯誤"

def get_admin_help_message():
    """生成管理員使用說明"""
    return """北金 North™Sea ᴍ8ᴘ 專屬機器人
-----------------------------------------------
僅限群組主或群組管理員使用

🔴設定操作員 @xxxxx @ccccc
🔴查看操作員
🔴刪除操作員 @xxxxx @ccccc
🔴刪除帳單
🔴刪除歷史帳單 慎用
-----------------------------------------------
群組主或者群組管理員或操作人

🔴設定入款匯率33.25
🔴設定出款匯率33.25

🟢 入款操作
🔹 +1000

🟢 出款普通金額
🔹 -1000

🔴修正命令 入款-100 出款-100
🔴入款撤銷 撤銷最近一筆入款帳單
🔴出款撤銷 撤銷最近一筆出款帳單
🔴+0  顯示帳單

🟢 計算器
🔹 (500+600)*8+(600-9)/5
🔹 500+600+800/85

🔴設定群發廣播 群發廣播訊息
🔴取消群發廣播 取消群發廣播訊息

🔺刪除所有聊天室訊息
🔺刪除所有非置頂訊息"""

def get_operator_help_message():
    """生成操作人使用說明"""
    return """北金 North™Sea ᴍ8ᴘ 專屬機器人
-----------------------------------------------

🟢 計算器
🔹 (500+600)*8+(600-9)/5
🔹 500+600+800/85

🔴 列表
在要列表的文字訊息回覆 "列表" 就會自動幫您把格式列表完畢囉！"""

def create_help_keyboard():
    """創建使用說明的鍵盤按鈕"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton('👮‍♂️管理員按鈕'),
        KeyboardButton('✏️操作人按鈕')
    )
    return keyboard

@bot.message_handler(func=lambda message: message.text == '👀使用說明')
def handle_help(message):
    """處理使用說明請求"""
    # 顯示選擇按鈕
    bot.reply_to(message, "請選擇要查看的說明：", reply_markup=create_help_keyboard())

@bot.message_handler(func=lambda message: message.text == '👮‍♂️管理員按鈕')
def handle_admin_help(message):
    """處理管理員說明請求"""
    bot.reply_to(message, get_admin_help_message(), reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text == '✏️操作人按鈕')
def handle_operator_help(message):
    """處理操作人說明請求"""
    bot.reply_to(message, get_operator_help_message(), reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text and message.text.startswith('[') and message.text.endswith(']'))
def handle_command(message):
    """處理命令"""
    # 移除方括號
    command = message.text[1:-1]
    bot.reply_to(message, f"執行命令：{command}")

def is_valid_calculation(text):
    """檢查是否為有效的計算公式"""
    # 移除所有空格和逗號
    text = text.replace(' ', '').replace(',', '')
    
    # 如果以+或-開頭，直接返回False（這是記帳功能）
    if text.startswith('+') or text.startswith('-'):
        return False
    
    # 檢查是否包含運算符
    operators = '+-*/'
    operator_count = sum(text.count(op) for op in operators)
    if operator_count == 0:
        return False
    
    # 檢查括號是否配對
    brackets_count = 0
    for c in text:
        if c == '(':
            brackets_count += 1
        elif c == ')':
            brackets_count -= 1
        if brackets_count < 0:  # 右括號多於左括號
            return False
    
    # 檢查是否只包含合法字符
    valid_chars = set('0123456789.+-*/() ')
    if not all(c in valid_chars for c in text):
        return False
    
    # 檢查數字的數量（至少需要兩個數字）
    numbers = [n for n in re.split(r'[+\-*/() ]+', text) if n]
    if len(numbers) < 2:
        return False
    
    # 檢查每個數字是否有效
    try:
        for num in numbers:
            if num:
                float(num)
        return True
    except ValueError:
        return False

def evaluate_expression(expression):
    """計算數學表達式"""
    try:
        # 基本安全檢查：只允許數字和基本運算符
        if not all(c in '0123456789.+-*/() ' for c in expression):
            return None
            
        # 計算結果
        result = eval(expression)
        
        # 如果結果是整數，返回整數格式
        if isinstance(result, (int, float)):
            if result.is_integer():
                return int(result)
            return round(result, 2)
        return None
    except:
        return None

@bot.message_handler(func=lambda message: message.text and is_valid_calculation(message.text))
def handle_calculator(message):
    """處理計算器功能"""
    try:
        # 移除所有逗號和空格
        expression = message.text.replace(',', '').replace(' ', '')
        
        # 檢查是否為有效的計算表達式
        if not is_valid_calculation(expression):
            return  # 如果不是有效的計算表達式，直接返回（可能是記帳功能）
        
        # 計算結果
        result = evaluate_expression(expression)
        
        if result is not None:
            # 格式化大數字（加上千位分隔符）
            if isinstance(result, (int, float)):
                formatted_result = format(result, ',')
                bot.reply_to(message, f"{message.text} = {formatted_result}")
        else:
            return  # 如果計算失敗，直接返回（可能是記帳功能）
    except Exception as e:
        return  # 如果發生錯誤，直接返回（可能是記帳功能）

def get_rules_message():
    """獲取群組規章內容"""
    return """北金 North™Sea ᴍ8ᴘ 群組規章
------------------------------------
1️⃣ 平時與業務的對話紀錄，請務必收回確實！乾淨！請勿將盤口、客戶指定地點等等之相關對話留存。務必要確實收回徹底。

2️⃣ 1號業務掛線內容確實，裝袋前務必再次清點金額。確認後在綁袋，若是自行後交外務主管，全程錄影直到給與外務主管。
2號3號業務相同。全程錄影直到給與外務主管or幣商，才可將視頻關閉。

3️⃣ 若隔日晨間有預約單，務必確實設定鬧鐘，並且打電話叫人員起床。"""

@bot.message_handler(func=lambda message: message.text == '📝群組規章')
def handle_rules(message):
    """處理群組規章請求"""
    try:
        # 記錄操作
        log_message(message, "查看群組規章")
        
        # 發送群組規章
        bot.reply_to(message, get_rules_message())
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取群組規章時發生錯誤：{str(e)}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    """處理新成員加入群組"""
    try:
        for new_member in message.new_chat_members:
            # 獲取新成員信息
            surname = new_member.username or f"{new_member.first_name} {new_member.last_name}".strip()
            fullname = f"{new_member.first_name} {new_member.last_name}".strip()
            firstname = new_member.first_name
            groupname = message.chat.title
            
            # 獲取歡迎詞模板
            welcome_template = config.get_welcome_message()
            
            # 替換變數
            welcome_message = welcome_template.format(
                SURNAME=surname,
                FULLNAME=fullname,
                FIRSTNAME=firstname,
                GROUPNAME=groupname
            )
            
            # 發送歡迎消息
            bot.reply_to(message, welcome_message)
            
            # 記錄操作
            log_message(message, f"新成員加入：{surname}")
    except Exception as e:
        logger.error(f"處理新成員加入時發生錯誤：{str(e)}")

def get_admin_commands_message():
    """獲取管理員命令列表"""
    return """🔰 群組管理員命令列表：

👮‍♂️ 管理員命令：
/ban @用戶名 [時間] [原因] - 禁言用戶（時間格式：1h, 1d, 1w）
/unban @用戶名 - 解除禁言
/kick @用戶名 [原因] - 踢出用戶
/warn @用戶名 [原因] - 警告用戶
/unwarn @用戶名 - 移除警告
/warns @用戶名 - 查看警告次數
/info @用戶名 - 查看用戶資訊
/del - 回覆要刪除的訊息即可刪除

⚠️ 注意：請謹慎使用管理命令"""

@bot.message_handler(commands=['admin'])
def show_admin_commands(message):
    """顯示管理員命令列表"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        bot.reply_to(message, get_admin_commands_message())
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示管理員命令時發生錯誤：{str(e)}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "機器人已啟動，可以開始使用了！", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text == '📜歷史帳單')
def handle_history(message):
    """處理歷史帳單請求"""
    bot.reply_to(message, get_history_message())

@bot.message_handler(content_types=['left_chat_member'])
def handle_member_left(message):
    """處理成員離開群組"""
    try:
        # 檢查是否啟用告別訊息
        if not config.get_farewell_enabled():
            return
        
        left_member = message.left_chat_member
        # 獲取離開成員信息
        surname = left_member.username or f"{left_member.first_name} {left_member.last_name}".strip()
        fullname = f"{left_member.first_name} {left_member.last_name}".strip()
        firstname = left_member.first_name
        groupname = message.chat.title
        
        # 獲取告別詞模板
        farewell_template = config.get_farewell_message()
        
        # 替換變數
        farewell_message = farewell_template.format(
            SURNAME=surname,
            FULLNAME=fullname,
            FIRSTNAME=firstname,
            GROUPNAME=groupname
        )
        
        # 發送告別消息
        bot.reply_to(message, farewell_message)
        
        # 記錄操作
        log_message(message, f"成員離開：{surname}")
    except Exception as e:
        logger.error(f"處理成員離開時發生錯誤：{str(e)}")

def is_admin(user_id, chat_id):
    """檢查用戶是否為群組管理員"""
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
        return False

def is_operator(user_id):
    """檢查用戶是否為操作員"""
    try:
        return config.is_operator(user_id)
    except:
        return False

def main():
    """主函數，啟動機器人"""
    try:
        logger.info("機器人啟動中...")
        print("機器人啟動中...")
        
        # 創建初始化心跳檢測線程
        def heartbeat():
            while True:
                logger.info("心跳檢測: 機器人運行中")
                time.sleep(3600)  # 每小時記錄一次心跳
        
        # 啟動心跳檢測線程
        import threading
        heartbeat_thread = threading.Thread(target=heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        logger.info("機器人開始監聽消息...")
        print("機器人開始監聽消息...")
        
        # 啟動機器人
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"機器人運行時發生錯誤：{str(e)}")
        print(f"機器人運行時發生錯誤：{str(e)}")

# 運行機器人
if __name__ == '__main__':
    print("機器人已啟動...")
    logger.info("機器人已啟動...")
    main()

@bot.message_handler(commands=['ban'])
def ban_user(message):
    """禁言用戶"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/ban @用戶名 [時間] [原因]")
            return

        # 解析命令參數
        target_username = args[1].replace("@", "")
        duration = None
        reason = "未指定原因"

        if len(args) > 2:
            # 解析時間（如果有）
            time_arg = args[2].lower()
            if time_arg.endswith(('h', 'd', 'w')):
                value = int(time_arg[:-1])
                unit = time_arg[-1]
                if unit == 'h':
                    duration = timedelta(hours=value)
                elif unit == 'd':
                    duration = timedelta(days=value)
                elif unit == 'w':
                    duration = timedelta(weeks=value)

            # 解析原因
            if len(args) > 3:
                reason = ' '.join(args[3:])

        # 獲取目標用戶
        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            target_user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 檢查是否為管理員
        if is_admin(target_user.id, message.chat.id):
            bot.reply_to(message, "❌ 無法禁言管理員")
            return

        # 設置禁言
        until_date = datetime.now() + duration if duration else None
        bot.restrict_chat_member(
            message.chat.id,
            target_user.id,
            until_date=until_date,
            permissions=telebot.types.ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False
            )
        )

        # 發送禁言通知
        duration_text = f" {duration.days}天" if duration else " 永久"
        bot.reply_to(message, f"✅ 已禁言 {target_username}{duration_text}\n原因：{reason}")
        
        # 記錄操作
        log_message(message, f"禁言用戶：{target_username}，原因：{reason}")
    except Exception as e:
        bot.reply_to(message, f"❌ 禁言用戶時發生錯誤：{str(e)}")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    """解除用戶禁言"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/unban @用戶名")
            return

        target_username = args[1].replace("@", "")

        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            target_user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 解除禁言
        bot.restrict_chat_member(
            message.chat.id,
            target_user.id,
            permissions=telebot.types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True
            )
        )

        bot.reply_to(message, f"✅ 已解除 {target_username} 的禁言")
        
        # 記錄操作
        log_message(message, f"解除禁言：{target_username}")
    except Exception as e:
        bot.reply_to(message, f"❌ 解除禁言時發生錯誤：{str(e)}")

@bot.message_handler(commands=['kick'])
def kick_user(message):
    """踢出用戶"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/kick @用戶名 [原因]")
            return

        target_username = args[1].replace("@", "")
        reason = "未指定原因" if len(args) < 3 else ' '.join(args[2:])

        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            target_user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 檢查是否為管理員
        if is_admin(target_user.id, message.chat.id):
            bot.reply_to(message, "❌ 無法踢出管理員")
            return

        # 踢出用戶
        bot.kick_chat_member(message.chat.id, target_user.id)
        bot.unban_chat_member(message.chat.id, target_user.id)  # 解除封鎖，允許用戶再次加入

        bot.reply_to(message, f"✅ 已踢出 {target_username}\n原因：{reason}")
        
        # 記錄操作
        log_message(message, f"踢出用戶：{target_username}，原因：{reason}")
    except Exception as e:
        bot.reply_to(message, f"❌ 踢出用戶時發生錯誤：{str(e)}")

@bot.message_handler(commands=['warn'])
def warn_user(message):
    """警告用戶"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/warn @用戶名 [原因]")
            return

        target_username = args[1].replace("@", "")
        reason = "未指定原因" if len(args) < 3 else ' '.join(args[2:])

        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            target_user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 檢查是否為管理員
        if is_admin(target_user.id, message.chat.id):
            bot.reply_to(message, "❌ 無法警告管理員")
            return

        # 添加警告
        warns = config.add_warning(target_user.id)
        
        warning_message = f"⚠️ {target_username} 已被警告\n"
        warning_message += f"原因：{reason}\n"
        warning_message += f"警告次數：{warns}/3\n"
        
        if warns >= 3:
            # 自動禁言 24 小時
            until_date = datetime.now() + timedelta(days=1)
            bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                until_date=until_date,
                permissions=telebot.types.ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False
                )
            )
            warning_message += "\n❗️ 已達到警告上限，自動禁言 24 小時"
            config.clear_warnings(target_user.id)  # 清空警告次數

        bot.reply_to(message, warning_message)
        
        # 記錄操作
        log_message(message, f"警告用戶：{target_username}，原因：{reason}")
    except Exception as e:
        bot.reply_to(message, f"❌ 警告用戶時發生錯誤：{str(e)}")

@bot.message_handler(commands=['unwarn'])
def unwarn_user(message):
    """移除用戶警告"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/unwarn @用戶名")
            return

        target_username = args[1].replace("@", "")

        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            target_user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 移除一次警告
        warns = config.remove_warning(target_user.id)
        
        bot.reply_to(message, f"✅ 已移除 {target_username} 的一次警告\n當前警告次數：{warns}/3")
        
        # 記錄操作
        log_message(message, f"移除警告：{target_username}")
    except Exception as e:
        bot.reply_to(message, f"❌ 移除警告時發生錯誤：{str(e)}")

@bot.message_handler(commands=['warns'])
def check_warns(message):
    """查看用戶警告次數"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/warns @用戶名")
            return

        target_username = args[1].replace("@", "")

        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            target_user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 獲取警告次數
        warns = config.get_warnings(target_user.id)
        
        bot.reply_to(message, f"👤 用戶：{target_username}\n⚠️ 警告次數：{warns}/3")
    except Exception as e:
        bot.reply_to(message, f"❌ 查看警告次數時發生錯誤：{str(e)}")

@bot.message_handler(commands=['info'])
def user_info(message):
    """查看用戶資訊"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ 使用方式：/info @用戶名")
            return

        target_username = args[1].replace("@", "")

        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{target_username}")
            user = chat_member.user
        except:
            bot.reply_to(message, "❌ 找不到指定用戶")
            return

        # 獲取用戶資訊
        info_message = f"""👤 用戶資訊：
ID：{user.id}
用戶名：@{user.username}
名字：{user.first_name}
姓氏：{user.last_name or '無'}
是否為機器人：{'是' if user.is_bot else '否'}
狀態：{chat_member.status}
警告次數：{config.get_warnings(user.id)}/3"""

        bot.reply_to(message, info_message)
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取用戶資訊時發生錯誤：{str(e)}")

@bot.message_handler(commands=['del'])
def delete_message(message):
    """刪除訊息"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        # 檢查是否為回覆訊息
        if not message.reply_to_message:
            bot.reply_to(message, "❌ 請回覆要刪除的訊息")
            return

        # 刪除目標訊息
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        # 刪除命令訊息
        bot.delete_message(message.chat.id, message.message_id)
        
        # 記錄操作
        log_message(message, "刪除訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除訊息時發生錯誤：{str(e)}")
        
@bot.message_handler(func=lambda message: message.text and message.text.startswith('+'))
def handle_deposit(message):
    """處理入款操作"""
    try:
        # 從消息中提取金額
        amount_str = message.text.strip()[1:]  # 移除 '+' 符號
        # 移除所有逗號
        amount_str = amount_str.replace(',', '')
        amount = float(amount_str)
        
        # 添加交易記錄
        config.add_transaction(amount, 'deposit')
        
        # 回覆完整交易摘要
        bot.reply_to(message, get_transaction_message(), reply_markup=create_keyboard())
    except ValueError:
        bot.reply_to(message, "❌ 格式錯誤！請使用：+金額")
    except Exception as e:
        bot.reply_to(message, f"❌ 處理入款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('-'))
def handle_withdrawal(message):
    """處理出款操作"""
    try:
        # 從消息中提取金額
        amount_str = message.text.strip()[1:]  # 移除 '-' 符號
        # 移除所有逗號
        amount_str = amount_str.replace(',', '')
        amount = float(amount_str)
        
        # 添加交易記錄
        config.add_transaction(amount, 'withdrawal')
        
        # 回覆完整交易摘要
        bot.reply_to(message, get_transaction_message(), reply_markup=create_keyboard())
    except ValueError:
        bot.reply_to(message, "❌ 格式錯誤！請使用：-金額")
    except Exception as e:
        bot.reply_to(message, f"❌ 處理出款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '刪除帳單')
def handle_clear_today(message):
    """處理刪除今日帳單的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除今日帳單")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.clear_today_transactions()
        bot.reply_to(message, "✅ 已清空今日帳單")
    except Exception as e:
        bot.reply_to(message, f"❌ 清空今日帳單時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '刪除歷史帳單')
def handle_clear_history(message):
    """處理刪除歷史帳單的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除歷史帳單")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.clear_all_transactions()
        bot.reply_to(message, "✅ 已清空所有歷史帳單")
    except Exception as e:
        bot.reply_to(message, f"❌ 清空歷史帳單時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定入款匯率'))
def handle_set_deposit_rate(message):
    """處理設定入款匯率的請求"""
    try:
        # 記錄操作
        log_message(message, "設定入款匯率")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 提取匯率數值
        rate = float(message.text.replace('設定入款匯率', '').strip())
        config.set_deposit_rate(rate)
        bot.reply_to(message, f"✅ 已設定入款匯率為：{rate}")
    except ValueError:
        bot.reply_to(message, "❌ 匯率格式錯誤！請使用正確的數字格式")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定入款匯率時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定出款匯率'))
def handle_set_withdrawal_rate(message):
    """處理設定出款匯率的請求"""
    try:
        # 記錄操作
        log_message(message, "設定出款匯率")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 提取匯率數值
        rate = float(message.text.replace('設定出款匯率', '').strip())
        config.set_withdrawal_rate(rate)
        bot.reply_to(message, f"✅ 已設定出款匯率為：{rate}")
    except ValueError:
        bot.reply_to(message, "❌ 匯率格式錯誤！請使用正確的數字格式")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定出款匯率時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '入款撤銷')
def handle_cancel_last_deposit(message):
    """處理撤銷最後一筆入款的請求"""
    try:
        # 記錄操作
        log_message(message, "撤銷入款")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 獲取交易摘要
        summary = config.get_transaction_summary()
        if not summary['deposits']:
            bot.reply_to(message, "❌ 沒有可撤銷的入款記錄")
            return
        
        # 獲取最後一筆入款金額用於顯示
        last_amount = summary['deposits'][-1]['amount']
        
        # 執行撤銷操作
        if config.cancel_last_deposit():
            bot.reply_to(message, f"✅ 已撤銷最後一筆入款：{last_amount:,.0f}")
            # 更新交易摘要
            bot.reply_to(message, get_transaction_message())
        else:
            bot.reply_to(message, "❌ 撤銷入款失敗")
    except Exception as e:
        bot.reply_to(message, f"❌ 撤銷入款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '出款撤銷')
def handle_cancel_last_withdrawal(message):
    """處理撤銷最後一筆出款的請求"""
    try:
        # 記錄操作
        log_message(message, "撤銷出款")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 獲取交易摘要
        summary = config.get_transaction_summary()
        if not summary['withdrawals']:
            bot.reply_to(message, "❌ 沒有可撤銷的出款記錄")
            return
        
        # 獲取最後一筆出款金額用於顯示
        last_amount = abs(summary['withdrawals'][-1]['amount'])
        
        # 執行撤銷操作
        if config.cancel_last_withdrawal():
            bot.reply_to(message, f"✅ 已撤銷最後一筆出款：{last_amount:,.0f}")
            # 更新交易摘要
            bot.reply_to(message, get_transaction_message())
        else:
            bot.reply_to(message, "❌ 撤銷出款失敗")
    except Exception as e:
        bot.reply_to(message, f"❌ 撤銷出款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '+0')
def handle_show_summary(message):
    """處理顯示交易摘要的請求"""
    try:
        # 記錄操作
        log_message(message, "查看交易摘要")
        
        # 獲取並發送交易摘要
        summary = get_transaction_message()
        bot.reply_to(message, summary)
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取交易摘要時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '設定群發廣播')
def handle_enable_broadcast(message):
    """處理啟用群發廣播的請求"""
    try:
        # 記錄操作
        log_message(message, "啟用群發廣播")
        
        # 檢查權限
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.set_broadcast_mode(True)
        bot.reply_to(message, "✅ 已啟用群發廣播模式")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定群發廣播時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '取消群發廣播')
def handle_disable_broadcast(message):
    """處理取消群發廣播的請求"""
    try:
        # 記錄操作
        log_message(message, "取消群發廣播")
        
        # 檢查權限
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.set_broadcast_mode(False)
        bot.reply_to(message, "✅ 已取消群發廣播模式")
    except Exception as e:
        bot.reply_to(message, f"❌ 取消群發廣播時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🛠️修復機器人')
def handle_repair_bot(message):
    """處理修復機器人請求"""
    repair_message = "「你的機器人好像壞掉了？」 快來修復它！"
    support_link = "https://t.me/Fanny_Orz"
    
    # 創建帶有連結的消息
    response = f"{repair_message}\n\n聯繫技術支援：{support_link}"
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == '刪除所有聊天室訊息')
def handle_delete_all_messages(message):
    """處理刪除所有聊天室訊息的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除所有聊天室訊息")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        # 獲取當前消息ID
        current_message_id = message.message_id
        
        # 從當前消息開始往前刪除
        for msg_id in range(current_message_id, 0, -1):
            try:
                bot.delete_message(message.chat.id, msg_id)
            except:
                continue
        
        # 發送成功消息（這條消息也會被刪除）
        bot.send_message(message.chat.id, "✅ 已清空所有聊天室訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '刪除所有非置頂訊息')
def handle_delete_non_pinned_messages(message):
    """處理刪除所有非置頂訊息的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除所有非置頂訊息")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        # 獲取置頂消息
        try:
            pinned_message = bot.get_chat(message.chat.id).pinned_message
            pinned_message_id = pinned_message.message_id if pinned_message else None
        except:
            pinned_message_id = None

        # 獲取當前消息ID
        current_message_id = message.message_id
        
        # 從當前消息開始往前刪除非置頂消息
        for msg_id in range(current_message_id, 0, -1):
            try:
                # 跳過置頂消息
                if pinned_message_id and msg_id == pinned_message_id:
                    continue
                bot.delete_message(message.chat.id, msg_id)
            except:
                continue
        
        # 發送成功消息（這條消息也會被刪除）
        bot.send_message(message.chat.id, "✅ 已清空所有非置頂訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除訊息時發生錯誤：{str(e)}")
