import telebot
import logging
from datetime import datetime
import os
import re
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from accounting import Accounting
from keyboard import get_main_menu, get_history_menu, get_rate_setting_menu, get_admin_menu
from keyboard import get_delete_records_menu, get_confirmation_keyboard, get_back_to_main_button, get_transaction_buttons
import dotenv

# 載入環境變數
dotenv.load_dotenv()

# 初始化機器人
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '7695972838:AAGGf6AnG7WpKvYhaZm-40X3iM-HiEkvjQg')
bot = telebot.TeleBot(bot_token)
accounting = Accounting()

# 設置日誌記錄
if not os.path.exists('logs'):
    os.makedirs('logs')
current_date = datetime.now().strftime('%Y-%m-%d')
log_file = f'logs/bot_log_{current_date}.txt'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BotLogger')

# 使用者狀態字典，用於跟踪用戶當前的操作狀態
user_states = {}

# 狀態常量
STATE_IDLE = 'idle'  # 空閒狀態
STATE_WAITING_RATE = 'waiting_rate'  # 等待輸入匯率
STATE_WAITING_ADDRESS = 'waiting_address'  # 等待輸入地址
STATE_WAITING_WELCOME = 'waiting_welcome'  # 等待輸入歡迎詞
STATE_WAITING_ADMIN = 'waiting_admin'  # 等待輸入管理員
STATE_WAITING_OPERATOR = 'waiting_operator'  # 等待輸入操作員

# 機器人心跳和啟動狀態
bot_running = False
heartbeat_thread = None

def start_heartbeat():
    """啟動心跳檢測線程"""
    def heartbeat():
        while bot_running:
            logger.info("機器人心跳檢測：正常運行中...")
            time.sleep(300)  # 每5分鐘檢測一次
    
    global heartbeat_thread
    heartbeat_thread = threading.Thread(target=heartbeat)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

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

def format_number(number):
    """格式化數字，添加千位分隔符，小數點後為00時不顯示"""
    if isinstance(number, (int, float)):
        formatted = "{:,.2f}".format(number)
        # 如果小數點後為00，則去除小數部分
        if formatted.endswith('.00'):
            formatted = formatted[:-3]
        return formatted
    return "0"

def is_admin(user_id):
    """檢查用戶是否為管理員"""
    return accounting.is_admin(user_id)

def is_operator(user_id):
    """檢查用戶是否為操作員"""
    return accounting.is_operator(user_id) or is_admin(user_id)  # 管理員也有操作員權限

def get_transaction_message(period='today', year=None, month=None):
    """生成交易報表消息"""
    summary = accounting.get_transaction_summary(period, year, month)
    
    # 取得匯率與費率
    exchange_rate = summary['exchange_rate']
    fee_rate = summary['fee_rate']
    
    # 生成報表標題
    if period == 'today':
        title = "【今日報表】"
    elif period == 'month':
        title = "【本月報表】"
    elif period == 'specific' and year and month:
        title = f"【{year}年{month}月報表】"
    else:
        title = "【總報表】"
    
    # 使用等寬字體
    message = f"<pre>{title}\n"
    message += f"入款筆數: {summary['deposit_count']}筆\n"
    
    # 顯示入款詳情
    if summary['deposit_count'] > 0:
        for deposit in summary['deposits']:
            operator = deposit.get('operator', '業務')
            message += f"[{operator}] <code>{deposit['time']}</code> {format_number(deposit['amount'])} / {deposit['exchange_rate']} = <code>{format_number(deposit['usdt_amount'])}</code>U\n"
    
    # 顯示已完成下發
    message += f"\n已完成下發: {summary['processed_count']}筆\n"
    if summary['processed_count'] > 0:
        for withdrawal in summary['processed_withdrawals']:
            message += f"<code>{withdrawal['time']}</code> {format_number(abs(withdrawal['amount']))} / {withdrawal['exchange_rate']} = <code>{format_number(withdrawal['usdt_amount'])}</code>U\n"
    
    # 顯示總金額
    message += f"\n總入金額: {summary['deposit_count']}筆\n"
    message += f"NTD: <code>{format_number(summary['total_deposit'])}</code> | USDT: <code>{format_number(summary['total_deposit_usdt'])}</code>\n"
    
    # 顯示匯率與費率
    message += f"\n當前匯率與費率\n"
    message += f"費率: {fee_rate}% | 匯率: {exchange_rate}\n"
    
    # 顯示總下發、應下發、未下發金額
    message += f"\n總下發\n"
    message += f"NTD: <code>{format_number(summary['total_withdrawal'])}</code> | USDT: <code>{format_number(summary['total_withdrawal_usdt'])}</code>\n"
    
    message += f"應下發\n"
    message += f"NTD: <code>{format_number(summary['total_deposit'])}</code> | USDT: <code>{format_number(summary['total_deposit_usdt'])}</code>\n"
    
    message += f"未下發\n"
    unprocessed_amount = summary['total_deposit'] - summary['total_withdrawal']
    unprocessed_usdt = summary['total_deposit_usdt'] - summary['total_withdrawal_usdt']
    message += f"NTD: <code>{format_number(max(0, unprocessed_amount))}</code> | USDT: <code>{format_number(max(0, unprocessed_usdt))}</code></pre>\n"
    
    return message

def get_operator_summary(period='month'):
    """生成按操作員分組的交易摘要"""
    operators_data = accounting.get_transactions_by_operator(period)
    
    # 生成標題
    if period == 'today':
        title = "【今日操作員報表】"
    elif period == 'month':
        title = "【本月操作員報表】"
    else:
        title = "【總操作員報表】"
    
    message = f"<pre>{title}\n\n"
    
    # 總計數據
    total_deposit_ntt = 0
    total_deposit_usdt = 0
    
    # 為每個操作員生成報表
    for operator, transactions in operators_data.items():
        # 過濾出入款記錄
        deposits = [t for t in transactions if t['type'] == 'deposit']
        withdrawals = [t for t in transactions if t['type'] == 'withdrawal']
        
        # 計算總金額
        total_op_deposit = sum(t['amount'] for t in deposits)
        total_op_deposit_usdt = sum(t['usdt_amount'] for t in deposits)
        total_op_withdrawal = sum(abs(t['amount']) for t in withdrawals)
        total_op_withdrawal_usdt = sum(t['usdt_amount'] for t in withdrawals)
        
        # 更新總計
        total_deposit_ntt += total_op_deposit
        total_deposit_usdt += total_op_deposit_usdt
        
        # 添加操作員報表
        message += f"【{operator}】\n"
        message += f"入款: {len(deposits)}筆 - NTD: <code>{format_number(total_op_deposit)}</code> (USDT: <code>{format_number(total_op_deposit_usdt)}</code>)\n"
        message += f"出款: {len(withdrawals)}筆 - NTD: <code>{format_number(total_op_withdrawal)}</code> (USDT: <code>{format_number(total_op_withdrawal_usdt)}</code>)\n\n"
    
    # 添加總計
    message += f"【總計】\n"
    message += f"總入款: NTD: <code>{format_number(total_deposit_ntt)}</code> (USDT: <code>{format_number(total_deposit_usdt)}</code>)</pre>\n"
    
    return message

def handle_calculation(expression):
    """處理計算表達式"""
    try:
        # 移除所有空格和逗號
        expression = expression.replace(' ', '').replace(',', '')
        
        # 匹配四則運算表達式
        if re.match(r'^[\d+\-*/().]+$', expression):
            # 安全地計算表達式
            result = eval(expression)
            return f"計算結果：{format_number(result)}"
        else:
            return "無效的計算表達式。請僅使用數字和 +、-、*、/、(、) 符號。"
    except Exception as e:
        return f"計算錯誤：{str(e)}"

def parse_transaction_command(text):
    """
    解析交易命令，支援多種格式：
    1. +金額 或 -金額
    2. mm/dd +金額 或 mm/dd -金額
    3. @使用者 H:M:S +金額 或 @使用者 H:M:S -金額
    
    返回：
    - amount: 金額
    - transaction_type: 'deposit' 或 'withdrawal'
    - custom_date: 自定義日期（如果有）
    - custom_time: 自定義時間（如果有）
    - operator: 操作員（如果有）
    """
    result = {
        'amount': None,
        'transaction_type': None,
        'custom_date': None,
        'custom_time': None,
        'operator': None
    }
    
    # 清除逗號
    text = text.replace(',', '')
    
    # 檢查是否為入款或出款命令
    if '+' in text or text.startswith('加'):
        result['transaction_type'] = 'deposit'
    elif '-' in text or text.startswith('減'):
        result['transaction_type'] = 'withdrawal'
    else:
        return None  # 不是交易命令
    
    # 處理"加"或"減"開頭的命令
    if text.startswith('加') or text.startswith('減'):
        text = text.replace('加', '+', 1).replace('減', '-', 1)
    
    # 解析日期 (mm/dd 格式)
    date_match = re.search(r'(\d{1,2}/\d{1,2})', text)
    if date_match:
        date_str = date_match.group(1)
        month, day = map(int, date_str.split('/'))
        current_year = datetime.now().year
        result['custom_date'] = f"{current_year}-{month:02d}-{day:02d}"
        # 從文本中移除日期部分
        text = text.replace(date_str, '')
    
    # 解析時間 (H:M:S 格式)
    time_match = re.search(r'(\d{1,2}:\d{1,2}(?::\d{1,2})?)', text)
    if time_match:
        time_str = time_match.group(1)
        # 確保時間格式為 HH:MM:SS
        if time_str.count(':') == 1:
            time_str += ':00'
        result['custom_time'] = time_str
        # 從文本中移除時間部分
        text = text.replace(time_str, '')
    
    # 解析操作員 (@username 格式)
    operator_match = re.search(r'@(\w+)', text)
    if operator_match:
        result['operator'] = operator_match.group(1)
        # 從文本中移除操作員部分
        text = text.replace(operator_match.group(0), '')
    
    # 解析金額
    amount_match = re.search(r'[+-]?\d+(\.\d+)?', text)
    if amount_match:
        result['amount'] = float(amount_match.group(0).replace('+', ''))
    
    # 確保金額有效
    if result['amount'] is None or result['amount'] <= 0:
        return None
    
    return result

def get_fixed_bottom_buttons():
    """返回固定底部按鈕"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # 使用等寬字體格式的按鈕文字
    keyboard.add(
        KeyboardButton("當日報表"),
        KeyboardButton("歷史報表")
    )
    keyboard.add(
        KeyboardButton("查看總表"),
        KeyboardButton("入款撤回")
    )
    keyboard.add(
        KeyboardButton("匯率設置"),
        KeyboardButton("出款撤回")
    )
    
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """處理 /start 命令，發送歡迎消息"""
    log_message(message, "開始使用機器人")
    user_id = message.from_user.id
    
    # 重置用戶狀態
    if user_id in user_states:
        user_states[user_id] = STATE_IDLE
    
    # 檢查是否是新用戶，如果是則添加到操作員列表
    accounting.add_operator_if_new(user_id, message.from_user.username)
    
    # 發送歡迎消息
    welcome_text = accounting.get_welcome_message()
    bot.reply_to(message, welcome_text, reply_markup=get_main_menu())
    
    # 發送固定按鈕
    bot.send_message(message.chat.id, "您可以使用下方按鈕快速訪問常用功能：", reply_markup=get_fixed_bottom_buttons())

@bot.message_handler(commands=['help'])
def send_help(message):
    """處理/help命令"""
    log_message(message, "查看幫助")
    bot.reply_to(message, "📚 北金小記帳 使用說明 📚\n\n"
                 "💰 【記帳功能】\n"
                 "➕ +金額 - 記錄入款\n"
                 "➖ -金額 - 記錄出款\n"
                 "📝 例如：+1000 或 -500\n\n"
                 "🔍 【查詢功能】\n"
                 "📅 /today 或「今日報表」- 查看今日報表\n"
                 "📆 /month 或「本月報表」- 查看本月報表\n"
                 "👥 /operators 或「操作員報表」- 查看操作員報表\n\n"
                 "⚙️ 【設定功能】\n"
                 "💱 /rate 數字 或「設定匯率數字」- 設定匯率（如：/rate 30.5 或 設定匯率30.5）\n"
                 "💹 /fee 數字 或「設定費率數字」- 設定費率（如：/fee 1.5 或 設定費率1.5）\n"
                 "📍 /address 或「查看地址」- 查看地址\n"
                 "📝 /set_address 內容 或「設定地址 內容」- 設定地址\n"
                 "💬 /set_welcome 或「設定歡迎詞 內容」- 設定歡迎詞\n\n"
                 "🛠️ 【管理功能】\n"
                 "👑 /set_admin @用戶名 或「設定管理員 @用戶名」- 設定管理員\n"
                 "👤 /set_operator @用戶名 或「設定操作員 @用戶名」- 設定操作員\n"
                 "👥 /view_admins 或「管理員列表」- 查看管理員列表\n"
                 "👥 /view_operators 或「操作員列表」- 查看操作員列表\n"
                 "🗑️ /clear 或「清除今日記錄」- 清除今日記錄\n"
                 "🗑️ /clear_month 或「清除本月記錄」- 清除本月記錄\n"
                 "🗑️ /clear_all 或「清除所有記錄」- 清除所有記錄\n"
                 "✅ /mark 交易ID 或「標記為已下發 交易ID」- 標記為已下發\n"
                 "↩️ /cancel_deposit 或「取消最後一筆入款」- 取消最後一筆入款\n"
                 "↩️ /cancel_withdrawal 或「取消最後一筆出款」- 取消最後一筆出款\n"
                 "🔄 /restart 或「重新啟動機器人」或「重啟」- 重新啟動機器人",
                 reply_markup=get_back_to_main_button())

@bot.message_handler(commands=['restart'])
def restart_bot(message):
    """重啟機器人，刷新所有數據"""
    global bot_running
    
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.reply_to(message, "⚠️ 您沒有權限使用此功能")
        return
    
    log_message(message, "重啟機器人")
    
    # 重啟機器人邏輯
    bot_running = False
    time.sleep(1)
    bot_running = True
    
    # 重新加載資料
    accounting.reload_data()
    
    # 清空使用者狀態
    user_states.clear()
    
    # 啟動心跳檢測
    start_heartbeat()
    
    # 發送確認消息
    bot.send_message(message.chat.id, "✅ 機器人已成功重新啟動！機器人開始監聽消息...", reply_markup=get_main_menu())
    
    # 重新發送底部固定按鈕
    bot.send_message(message.chat.id, "固定按鈕已重新載入：", reply_markup=get_fixed_bottom_buttons())

@bot.message_handler(commands=['today'])
def show_today_report(message):
    """處理/today命令，顯示今日報表"""
    log_message(message, "查看今日報表")
    try:
        report_message = get_transaction_message('today')
        bot.reply_to(message, report_message, parse_mode='HTML', reply_markup=get_back_to_main_button())
    except Exception as e:
        logger.error(f"顯示今日報表時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 顯示今日報表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '今日報表')
def show_today_report_chinese(message):
    """處理'今日報表'中文命令"""
    show_today_report(message)

@bot.message_handler(commands=['month'])
def show_month_report(message):
    """處理/month命令，顯示本月報表"""
    log_message(message, "查看本月報表")
    try:
        report_message = get_transaction_message('month')
        bot.reply_to(message, report_message, parse_mode='HTML', reply_markup=get_back_to_main_button())
    except Exception as e:
        logger.error(f"顯示本月報表時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 顯示本月報表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '本月報表')
def show_month_report_chinese(message):
    """處理'本月報表'中文命令"""
    show_month_report(message)

@bot.message_handler(commands=['operators'])
def show_operators_report(message):
    """處理/operators命令，顯示操作員報表"""
    log_message(message, "查看操作員報表")
    try:
        report_message = get_operator_summary('month')
        bot.reply_to(message, report_message, parse_mode='HTML', reply_markup=get_back_to_main_button())
    except Exception as e:
        logger.error(f"顯示操作員報表時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 顯示操作員報表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '操作員報表')
def show_operators_report_chinese(message):
    """處理'操作員報表'中文命令"""
    show_operators_report(message)

@bot.message_handler(commands=['rate'])
def set_exchange_rate(message):
    """處理/rate命令，設定匯率"""
    log_message(message, "設定匯率")
    
    # 檢查權限
    if not is_operator(message.from_user.id):
        bot.reply_to(message, "❌ 只有操作員或管理員可以設定匯率！")
        return
    
    try:
        # 解析命令參數
        parts = message.text.split()
        if len(parts) == 1:
            # 無參數，顯示匯率設定菜單
            bot.reply_to(message, "💱 請選擇或輸入匯率：", reply_markup=get_rate_setting_menu())
            return
        elif len(parts) != 2:
            bot.reply_to(message, "❌ 格式錯誤！請使用：/rate 數字")
            return
        
        rate = float(parts[1])
        if rate <= 0:
            bot.reply_to(message, "❌ 匯率必須大於0")
            return
        
        accounting.set_exchange_rate(rate)
        bot.reply_to(message, f"✅ 匯率已設定為 {rate}", reply_markup=get_back_to_main_button())
    except ValueError:
        bot.reply_to(message, "❌ 請輸入有效的數字")
    except Exception as e:
        logger.error(f"設定匯率時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 設定匯率時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定匯率'))
def set_exchange_rate_chinese(message):
    """處理'設定匯率'中文命令"""
    # 從消息中提取匯率值
    try:
        rate_str = message.text.replace('設定匯率', '').strip()
        if not rate_str:
            bot.reply_to(message, "❌ 格式錯誤！請使用：設定匯率 數字")
            return
        
        # 創建模擬的命令消息
        simulated_text = f"/rate {rate_str}"
        message.text = simulated_text
        set_exchange_rate(message)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理匯率設定時發生錯誤：{str(e)}")

@bot.message_handler(commands=['fee'])
def set_fee_rate(message):
    """處理/fee命令，設定費率"""
    log_message(message, "設定費率")
    
    # 檢查權限
    if not is_operator(message.from_user.id):
        bot.reply_to(message, "❌ 只有操作員或管理員可以設定費率！")
        return
    
    try:
        # 解析命令參數
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ 格式錯誤！請使用：/fee 數字")
            return
        
        rate = float(parts[1])
        if rate < 0:
            bot.reply_to(message, "❌ 費率不能為負數")
            return
        
        accounting.set_fee_rate(rate)
        bot.reply_to(message, f"✅ 費率已設定為 {rate}%", reply_markup=get_back_to_main_button())
    except ValueError:
        bot.reply_to(message, "❌ 請輸入有效的數字")
    except Exception as e:
        logger.error(f"設定費率時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 設定費率時發生錯誤：{str(e)}")

@bot.message_handler(commands=['clear'])
def clear_today_transactions(message):
    """處理/clear命令，清除今日交易記錄"""
    log_message(message, "清除今日記錄")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有管理員可以清除記錄！")
        return
    
    # 顯示確認按鈕
    bot.reply_to(message, "⚠️ 確定要刪除今日所有交易記錄嗎？此操作不可逆！", 
                 reply_markup=get_confirmation_keyboard("delete_today"))

@bot.message_handler(commands=['clear_month'])
def clear_month_transactions(message):
    """處理/clear_month命令，清除本月交易記錄"""
    log_message(message, "清除本月記錄")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有管理員可以清除記錄！")
        return
    
    # 顯示確認按鈕
    bot.reply_to(message, "⚠️ 確定要刪除本月所有交易記錄嗎？此操作不可逆！", 
                 reply_markup=get_confirmation_keyboard("delete_month"))

@bot.message_handler(commands=['clear_all'])
def clear_all_transactions(message):
    """處理/clear_all命令，清除所有交易記錄"""
    log_message(message, "清除所有記錄")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有管理員可以清除記錄！")
        return
    
    # 顯示確認按鈕
    bot.reply_to(message, "⚠️ 確定要刪除所有交易記錄嗎？此操作不可逆！", 
                 reply_markup=get_confirmation_keyboard("delete_all"))

@bot.message_handler(commands=['mark'])
def mark_transaction_processed(message):
    """處理/mark命令，標記交易為已下發"""
    log_message(message, "標記交易為已下發")
    
    # 檢查權限
    if not is_operator(message.from_user.id):
        bot.reply_to(message, "❌ 只有操作員或管理員可以標記交易！")
        return
    
    try:
        # 解析命令參數
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ 格式錯誤！請使用：/mark 交易ID")
            return
        
        transaction_id = int(parts[1])
        success = accounting.mark_transaction_processed(transaction_id)
        if success:
            bot.reply_to(message, f"✅ 交易 #{transaction_id} 已標記為已下發", reply_markup=get_back_to_main_button())
        else:
            bot.reply_to(message, f"❌ 找不到交易 #{transaction_id}")
    except ValueError:
        bot.reply_to(message, "❌ 請輸入有效的交易ID")
    except Exception as e:
        logger.error(f"標記交易時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 標記交易時發生錯誤：{str(e)}")

@bot.message_handler(commands=['cancel_deposit'])
def cancel_last_deposit(message):
    """處理/cancel_deposit命令，取消最後一筆入款"""
    log_message(message, "取消最後一筆入款")
    
    # 檢查權限
    if not is_operator(message.from_user.id):
        bot.reply_to(message, "❌ 只有操作員或管理員可以取消交易！")
        return
    
    try:
        transaction = accounting.cancel_last_transaction('deposit')
        if transaction:
            response = f"已取消最後一筆入款：\n金額: {format_number(transaction['amount'])} 元\n\n"
            # 更新報表
            report_message = get_transaction_message('today')
            bot.reply_to(message, response + report_message, parse_mode='HTML', reply_markup=get_back_to_main_button())
        else:
            bot.reply_to(message, "❌ 沒有入款記錄可取消")
    except Exception as e:
        logger.error(f"取消入款時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 取消入款時發生錯誤：{str(e)}")

@bot.message_handler(commands=['cancel_withdrawal'])
def cancel_last_withdrawal(message):
    """處理/cancel_withdrawal命令，取消最後一筆出款"""
    log_message(message, "取消最後一筆出款")
    
    # 檢查權限
    if not is_operator(message.from_user.id):
        bot.reply_to(message, "❌ 只有操作員或管理員可以取消交易！")
        return
    
    try:
        transaction = accounting.cancel_last_transaction('withdrawal')
        if transaction:
            response = f"已取消最後一筆出款：\n金額: {format_number(abs(transaction['amount']))} 元\n\n"
            # 更新報表
            report_message = get_transaction_message('today')
            bot.reply_to(message, response + report_message, parse_mode='HTML', reply_markup=get_transaction_buttons())
        else:
            bot.reply_to(message, "❌ 沒有出款記錄可取消")
    except Exception as e:
        logger.error(f"取消出款時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 取消出款時發生錯誤：{str(e)}")

@bot.message_handler(commands=['set_admin'])
def set_admin(message):
    """處理/set_admin命令，設定管理員"""
    log_message(message, "設定管理員")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有現有管理員可以指派新管理員！")
        return
    
    # 獲取命令參數
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith('@'):
        # 如果沒有提供用戶名，則進入設定狀態
        bot.reply_to(message, "請輸入要設定為管理員的用戶名稱，格式: @username")
        user_states[message.from_user.id] = STATE_WAITING_ADMIN
        return
    
    # 解析用戶名
    username = parts[1][1:]  # 移除@符號
    
    # 添加管理員
    # 注意：這裡無法直接獲得用戶ID，只能儲存用戶名
    accounting.add_admin(-1, username)  # 使用-1作為臨時ID
    bot.reply_to(message, f"✅ 已設定 @{username} 為管理員。請讓該用戶與機器人互動一次以完成設定。", reply_markup=get_back_to_main_button())

@bot.message_handler(commands=['set_operator'])
def set_operator(message):
    """處理/set_operator命令，設定操作員"""
    log_message(message, "設定操作員")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有管理員可以指派操作員！")
        return
    
    # 獲取命令參數
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith('@'):
        # 如果沒有提供用戶名，則進入設定狀態
        bot.reply_to(message, "請輸入要設定為操作員的用戶名稱，格式: @username")
        user_states[message.from_user.id] = STATE_WAITING_OPERATOR
        return
    
    # 解析用戶名
    username = parts[1][1:]  # 移除@符號
    
    # 添加操作員
    accounting.add_operator(-1, username)  # 使用-1作為臨時ID
    bot.reply_to(message, f"✅ 已設定 @{username} 為操作員。請讓該用戶與機器人互動一次以完成設定。", reply_markup=get_back_to_main_button())

@bot.message_handler(commands=['view_admins'])
def view_admins(message):
    """處理/view_admins命令，查看管理員列表"""
    log_message(message, "查看管理員列表")
    
    # 獲取管理員列表
    admins = accounting.get_admins()
    
    if not admins:
        bot.reply_to(message, "目前沒有設定管理員。")
        return
    
    # 生成管理員列表消息
    response = "【管理員列表】\n"
    for admin in admins:
        response += f"- @{admin['username']} (ID: {admin['id']})\n"
    
    bot.reply_to(message, response, reply_markup=get_back_to_main_button())

@bot.message_handler(commands=['view_operators'])
def view_operators(message):
    """處理/view_operators命令，查看操作員列表"""
    log_message(message, "查看操作員報表")
    
    # 獲取操作員列表
    operators = accounting.get_operators()
    
    if not operators:
        bot.reply_to(message, "目前沒有設定操作員。")
        return
    
    # 生成操作員列表消息
    response = "【操作員列表】\n"
    for operator in operators:
        response += f"- @{operator['username']} (ID: {operator['id']})\n"
    
    bot.reply_to(message, response, reply_markup=get_back_to_main_button())

@bot.message_handler(commands=['set_welcome'])
def set_welcome(message):
    """處理/set_welcome命令，設定歡迎詞"""
    log_message(message, "設定歡迎詞")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有管理員可以設定歡迎詞！")
        return
    
    # 進入等待歡迎詞狀態
    bot.reply_to(message, "請輸入新的歡迎詞:")
    user_states[message.from_user.id] = STATE_WAITING_WELCOME

@bot.message_handler(commands=['set_address'])
def set_address(message):
    """處理/set_address命令，設定地址"""
    log_message(message, "設定地址")
    
    # 檢查權限
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ 只有管理員可以設定地址！")
        return
    
    # 獲取命令參數
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        # 如果沒有提供地址，則進入設定狀態
        bot.reply_to(message, "請輸入要設定的地址內容:")
        user_states[message.from_user.id] = STATE_WAITING_ADDRESS
        return
    
    # 設定地址
    address = parts[1]
    accounting.set_group_address(message.chat.id, address)
    bot.reply_to(message, f"✅ 已設定地址為：\n{address}", reply_markup=get_back_to_main_button())

@bot.message_handler(commands=['address'])
def show_address(message):
    """處理/address命令，顯示地址"""
    log_message(message, "顯示地址")
    
    # 獲取地址
    address = accounting.get_group_address(message.chat.id)
    
    if not address:
        bot.reply_to(message, "⚠️ 尚未設定地址。請管理員使用 /set_address 命令設定。")
        return
    
    bot.reply_to(message, f"📍 【地址信息】\n{address}", reply_markup=get_back_to_main_button())

@bot.message_handler(func=lambda message: message.text and (message.text.startswith('+') or message.text.startswith('加')))
def handle_deposit(message):
    """處理入款操作"""
    log_message(message, "入款操作")
    try:
        # 解析交易指令
        parsed = parse_transaction_command(message.text)
        if not parsed:
            bot.reply_to(message, "❌ 格式錯誤！請使用：+金額 或 加金額")
            return
        
        # 獲取交易數據
        amount = parsed['amount']
        operator = parsed.get('operator') or message.from_user.username or message.from_user.first_name
        custom_date = parsed.get('custom_date')
        custom_time = parsed.get('custom_time')
        
        # 添加交易記錄
        transaction = accounting.add_transaction(
            amount=amount, 
            transaction_type='deposit', 
            operator=operator, 
            custom_date=custom_date, 
            custom_time=custom_time
        )
        
        # 回覆確認消息
        bot.reply_to(message, f"已記錄入款：\n"
                             f"交易ID: #{transaction['id']}\n"
                             f"金額: {format_number(transaction['amount'])} 元\n"
                             f"匯率: {transaction['exchange_rate']}\n"
                             f"USDT: {format_number(transaction['usdt_amount'])}", 
                             reply_markup=get_transaction_buttons())
    except ValueError as e:
        bot.reply_to(message, f"❌ 格式錯誤！{str(e)}")
    except Exception as e:
        logger.error(f"處理入款時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 處理入款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and (message.text.startswith('-') or message.text.startswith('減')))
def handle_withdrawal(message):
    """處理出款操作"""
    log_message(message, "出款操作")
    try:
        # 解析交易指令
        parsed = parse_transaction_command(message.text)
        if not parsed:
            bot.reply_to(message, "❌ 格式錯誤！請使用：-金額 或 減金額")
            return
        
        # 獲取交易數據
        amount = parsed['amount']
        operator = parsed.get('operator') or message.from_user.username or message.from_user.first_name
        custom_date = parsed.get('custom_date')
        custom_time = parsed.get('custom_time')
        
        # 添加交易記錄
        transaction = accounting.add_transaction(
            amount=amount, 
            transaction_type='withdrawal', 
            operator=operator, 
            custom_date=custom_date, 
            custom_time=custom_time
        )
        
        # 回覆確認消息
        bot.reply_to(message, f"已記錄出款：\n"
                             f"交易ID: #{transaction['id']}\n"
                             f"金額: {format_number(abs(transaction['amount']))} 元\n"
                             f"匯率: {transaction['exchange_rate']}\n"
                             f"USDT: {format_number(transaction['usdt_amount'])}",
                             reply_markup=get_transaction_buttons())
    except ValueError as e:
        bot.reply_to(message, f"❌ 格式錯誤！{str(e)}")
    except Exception as e:
        logger.error(f"處理出款時發生錯誤：{str(e)}")
        bot.reply_to(message, f"❌ 處理出款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and re.match(r'^[\d+\-*/().]+$', message.text.replace(' ', '').replace(',', '')))
def handle_calculator(message):
    """處理計算機功能"""
    log_message(message, "計算機功能")
    result = handle_calculation(message.text)
    bot.reply_to(message, result)

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == STATE_WAITING_RATE)
def handle_rate_input(message):
    """處理匯率輸入"""
    log_message(message, "匯率輸入")
    try:
        rate = float(message.text.strip())
        if rate <= 0:
            bot.reply_to(message, "❌ 匯率必須大於0")
            return
            
        accounting.set_exchange_rate(rate)
        bot.reply_to(message, f"✅ 匯率已設定為 {rate}", reply_markup=get_back_to_main_button())
        
        # 重置用戶狀態
        user_states[message.from_user.id] = STATE_IDLE
    except ValueError:
        bot.reply_to(message, "❌ 請輸入有效的數字")

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == STATE_WAITING_ADDRESS)
def handle_address_input(message):
    """處理地址輸入"""
    log_message(message, "地址輸入")
    
    # 設置地址
    accounting.set_group_address(message.chat.id, message.text)
    bot.reply_to(message, f"✅ 已設定地址為：\n{message.text}", reply_markup=get_back_to_main_button())
    
    # 重置用戶狀態
    user_states[message.from_user.id] = STATE_IDLE

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == STATE_WAITING_WELCOME)
def handle_welcome_input(message):
    """處理歡迎詞輸入"""
    log_message(message, "歡迎詞輸入")
    
    # 設置歡迎詞
    accounting.set_group_welcome_message(message.chat.id, message.text)
    bot.reply_to(message, f"✅ 已設定歡迎詞為：\n{message.text}", reply_markup=get_back_to_main_button())
    
    # 重置用戶狀態
    user_states[message.from_user.id] = STATE_IDLE

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == STATE_WAITING_ADMIN)
def handle_admin_input(message):
    """處理管理員輸入"""
    log_message(message, "管理員輸入")
    
    if not message.text.startswith('@'):
        bot.reply_to(message, "❌ 格式錯誤！請使用格式: @username")
        return
        
    # 解析用戶名
    username = message.text[1:]  # 移除@符號
    
    # 添加管理員
    accounting.add_admin(-1, username)  # 使用-1作為臨時ID
    bot.reply_to(message, f"✅ 已設定 @{username} 為管理員。請讓該用戶與機器人互動一次以完成設定。", reply_markup=get_back_to_main_button())
    
    # 重置用戶狀態
    user_states[message.from_user.id] = STATE_IDLE

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == STATE_WAITING_OPERATOR)
def handle_operator_input(message):
    """處理操作員輸入"""
    log_message(message, "操作員輸入")
    
    if not message.text.startswith('@'):
        bot.reply_to(message, "❌ 格式錯誤！請使用格式: @username")
        return
        
    # 解析用戶名
    username = message.text[1:]  # 移除@符號
    
    # 添加操作員
    accounting.add_operator(-1, username)
    bot.reply_to(message, f"✅ 已設定 @{username} 為操作員。請讓該用戶與機器人互動一次以完成設定。", reply_markup=get_back_to_main_button())
    
    # 重置用戶狀態
    user_states[message.from_user.id] = STATE_IDLE

# 捕捉所有其他消息
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """處理所有其他消息"""
    # 檢查消息是否為空
    if not message.text:
        return
        
    # 檢查是否有管理員或操作員以 -1 ID，需要更新為實際 ID
    if accounting.is_admin(-1) or accounting.is_operator(-1):
        username = message.from_user.username
        user_id = message.from_user.id
        
        # 更新管理員 ID
        for admin in accounting.get_admins():
            if admin['id'] == -1 and admin['username'] == username:
                accounting.remove_admin(-1)
                accounting.add_admin(user_id, username)
                bot.send_message(message.chat.id, f"✅ 已更新 @{username} 的管理員 ID: {user_id}")
        
        # 更新操作員 ID
        for operator in accounting.get_operators():
            if operator['id'] == -1 and operator['username'] == username:
                accounting.remove_operator(-1)
                accounting.add_operator(user_id, username)
                bot.send_message(message.chat.id, f"✅ 已更新 @{username} 的操作員 ID: {user_id}")
    
    # 私聊中響應
    if message.chat.type == 'private':
        bot.reply_to(message, "請使用有效的命令。輸入 /help 查看幫助。")

# 添加回調按鈕處理函數
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """處理按鈕回調"""
    try:
        # 獲取回調數據
        callback_data = call.data
        
        # 處理各種回調
        if callback_data == "back_to_main":
            # 返回主選單
            bot.edit_message_text(
                "🎮 請選擇功能：",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_menu()
            )
            
        elif callback_data == "today_report":
            # 顯示今日報表
            report_message = get_transaction_message('today')
            bot.edit_message_text(
                report_message,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "month_report":
            # 顯示本月報表
            report_message = get_transaction_message('month')
            bot.edit_message_text(
                report_message,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "history_reports":
            # 顯示歷史報表選單
            bot.edit_message_text(
                "📆 請選擇要查看的月份：",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_history_menu()
            )
            
        elif callback_data.startswith("history_"):
            # 顯示特定月份報表
            parts = callback_data.split("_")
            if len(parts) == 3:
                year = int(parts[1])
                month = int(parts[2])
                report_message = get_transaction_message('specific', year, month)
                bot.edit_message_text(
                    report_message,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=get_back_to_main_button()
                )
                
        elif callback_data == "commands_help":
            # 顯示操作說明
            help_text = "📚 北金小記帳 使用說明 📚\n\n"
            help_text += "💰 【記帳功能】\n"
            help_text += "➕ +金額 - 記錄入款\n"
            help_text += "➖ -金額 - 記錄出款\n"
            help_text += "🔢 【進階用法】\n"
            help_text += "📅 mm/dd +金額 - 記錄特定日期入款\n"
            help_text += "👤 @操作員 ⏱️ H:M:S +金額 - 記錄特定操作員和時間入款\n\n"
            help_text += "🔍 【查詢功能】\n"
            help_text += "📅 /today 或「今日報表」- 查看今日報表\n"
            help_text += "📆 /month 或「本月報表」- 查看本月報表\n"
            help_text += "👥 /operators 或「操作員報表」- 查看操作員報表\n\n"
            help_text += "⚙️ 【設定功能】\n"
            help_text += "💱 /rate 數字 或「設定匯率數字」- 設定匯率\n"
            help_text += "💹 /fee 數字 或「設定費率數字」- 設定費率\n"
            help_text += "📍 /address 或「查看地址」- 查看地址\n"
            help_text += "📝 /set_address 內容 或「設定地址 內容」- 設定地址\n"
            help_text += "💬 /set_welcome 或「設定歡迎詞 內容」- 設定歡迎詞\n\n"
            help_text += "🛠️ 【管理功能】\n"
            help_text += "👑 /set_admin @用戶名 或「設定管理員 @用戶名」- 設定管理員\n"
            help_text += "👤 /set_operator @用戶名 或「設定操作員 @用戶名」- 設定操作員\n"
            help_text += "👥 /view_admins 或「管理員列表」- 查看管理員列表\n"
            help_text += "👥 /view_operators 或「操作員列表」- 查看操作員列表\n"
            help_text += "🗑️ /clear 或「清除今日記錄」- 清除今日記錄\n"
            help_text += "🗑️ /clear_month 或「清除本月記錄」- 清除本月記錄\n"
            help_text += "🗑️ /clear_all 或「清除所有記錄」- 清除所有記錄\n"
            help_text += "✅ /mark 交易ID 或「標記為已下發 交易ID」- 標記為已下發\n"
            help_text += "↩️ /cancel_deposit 或「取消最後一筆入款」- 取消最後一筆入款\n"
            help_text += "↩️ /cancel_withdrawal 或「取消最後一筆出款」- 取消最後一筆出款\n"
            help_text += "🔄 /restart 或「重新啟動機器人」或「重啟」- 重新啟動機器人"
            
            bot.edit_message_text(
                help_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "rate_setting":
            # 顯示匯率設定選單
            bot.edit_message_text(
                "💱 請選擇或輸入匯率：",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_rate_setting_menu()
            )
            
        elif callback_data.startswith("set_rate_"):
            # 設定特定匯率
            # 檢查權限
            if not is_operator(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有操作員或管理員可以設定匯率！")
                return
                
            # 解析匯率
            rate = float(callback_data.split("_")[2])
            accounting.set_exchange_rate(rate)
            
            bot.edit_message_text(
                f"✅ 匯率已設定為 {rate}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "custom_rate":
            # 進入自訂匯率狀態
            if not is_operator(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有操作員或管理員可以設定匯率！")
                return
                
            bot.edit_message_text(
                "💱 請輸入新的匯率數值：",
                call.message.chat.id,
                call.message.message_id
            )
            
            # 更新用戶狀態
            user_states[call.from_user.id] = STATE_WAITING_RATE
            
        elif callback_data == "show_commands":
            # 顯示所有指令列表
            commands = " 記帳功能\n"
            commands += "🔺<code>+金額</code> //設定當日入款\n"
            commands += "🔺<code>-金額</code> //設定當日出款\n"
            commands += "<code>MM/DD +金額</code> //記錄特定日期入款\n\n"
            
            commands += " 查詢功能\n"
            commands += "🔹<code>今日報表</code> //顯示當日報表內容\n"
            commands += "🔹<code>本月報表</code> //顯示當月報表內容\n"
            commands += "🔹<code>操作員報表</code> //顯示操作員的列表\n\n"
            
            commands += " 設定功能\n"
            commands += "🔺<code>設定匯率oo.oo</code> //設定當日匯率\n"
            commands += "🔺<code>設定費率oo.oo</code> //設定當日費率\n"
            commands += "🔺<code>查看地址</code> //顯示usdT地址\n"
            commands += "🔺<code>設定地址 內容</code> //設定usdT地址\n"
            commands += "🔺<code>設定歡迎詞 內容</code> //設定新成員入群的詞語\n\n"
            
            commands += " 管理功能\n"
            commands += "🔺<code>設定管理員 @oooo</code> //將指定人設定為管理員\n"
            commands += "🔺<code>設定操作員 @oooo</code> //將指定人設定為操作員\n"
            commands += "🔺<code>管理員列表</code> //查看管理員有誰\n"
            commands += "🔺<code>操作員列表</code> //查看操作員有誰\n"
            commands += "🔺<code>清除今日記錄</code> //刪除當天的所有訊息紀錄\n"
            commands += "🔺<code>清除本月記錄</code> //刪除當月的所有訊息紀錄\n"
            commands += "🔺<code>清除所有記錄</code> //刪除群內的所有訊息紀錄\n"
            commands += "🔺<code>標記為已下發 交易ID</code> //將指定交易ID設為下發金額\n"
            commands += "🔹<code>取消最後一筆入款</code> //撤銷上一筆款\n"
            commands += "🔹<code>取消最後一筆出款</code> //撤銷上一筆出款\n"
            commands += "🔹<code>重啟</code> //重新啟動機器人"
            
            bot.edit_message_text(
                commands,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "cancel_deposit":
            # 取消最後一筆入款
            if not is_operator(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有操作員或管理員可以取消交易！")
                return
                
            transaction = accounting.cancel_last_transaction('deposit')
            if transaction:
                response = f"已取消最後一筆入款：\n金額: {format_number(transaction['amount'])} 元\n\n"
                # 更新報表
                report_message = get_transaction_message('today')
                bot.edit_message_text(
                    response + report_message,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=get_back_to_main_button()
                )
            else:
                bot.answer_callback_query(call.id, "❌ 沒有入款記錄可取消")
                
        elif callback_data == "cancel_withdrawal":
            # 取消最後一筆出款
            if not is_operator(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有操作員或管理員可以取消交易！")
                return
                
            transaction = accounting.cancel_last_transaction('withdrawal')
            if transaction:
                response = f"已取消最後一筆出款：\n金額: {format_number(abs(transaction['amount']))} 元\n\n"
                # 更新報表
                report_message = get_transaction_message('today')
                bot.edit_message_text(
                    response + report_message,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=get_back_to_main_button()
                )
            else:
                bot.answer_callback_query(call.id, "❌ 沒有出款記錄可取消")
                
        elif callback_data == "restart_bot":
            # 重新啟動機器人
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以重新啟動機器人！")
                return
                
            bot.edit_message_text(
                "🔄 正在重新啟動機器人...\n⚙️ 初始化檔案...\n💓 啟動心跳檢測線程...",
                call.message.chat.id,
                call.message.message_id
            )
            
            # 重置全局狀態
            user_states.clear()
            
            # 啟動心跳
            global bot_running
            bot_running = True
            start_heartbeat()
            
            # 發送重啟完成消息
            time.sleep(2)  # 模擬重啟過程
            bot.edit_message_text(
                "✅ 機器人已成功重新啟動！\n🤖 機器人開始監聽消息...",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_menu()
            )
            
        elif callback_data == "set_admin":
            # 進入設定管理員頁面
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以設定管理員！")
                return
                
            bot.edit_message_text(
                "👑 請輸入要設定為管理員的用戶名稱，格式: @username",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
            # 更新用戶狀態
            user_states[call.from_user.id] = STATE_WAITING_ADMIN
            
        elif callback_data == "delete_records_menu":
            # 顯示刪除記錄選單
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            bot.edit_message_text(
                "🗑️ 請選擇要刪除的記錄：",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_delete_records_menu()
            )
            
        elif callback_data == "delete_today_records":
            # 確認刪除今日記錄
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            bot.edit_message_text(
                "⚠️ 確定要刪除今日所有交易記錄嗎？此操作不可逆！",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_confirmation_keyboard("delete_today")
            )
            
        elif callback_data == "delete_month_records":
            # 確認刪除本月記錄
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            bot.edit_message_text(
                "⚠️ 確定要刪除本月所有交易記錄嗎？此操作不可逆！",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_confirmation_keyboard("delete_month")
            )
            
        elif callback_data == "delete_all_records":
            # 確認刪除所有記錄
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            bot.edit_message_text(
                "⚠️ 確定要刪除所有交易記錄嗎？此操作不可逆！",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_confirmation_keyboard("delete_all")
            )
            
        elif callback_data == "back_to_admin":
            # 返回管理員選單
            bot.edit_message_text(
                "👑 管理員功能：",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_menu()
            )
            
        elif callback_data == "confirm_delete_today":
            # 確認刪除今日記錄
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            accounting.clear_today_transactions()
            bot.edit_message_text(
                "✅ 已刪除今日所有交易記錄",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "confirm_delete_month":
            # 確認刪除本月記錄
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            accounting.clear_month_transactions()
            bot.edit_message_text(
                "✅ 已刪除本月所有交易記錄",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "confirm_delete_all":
            # 確認刪除所有記錄
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ 只有管理員可以刪除記錄！")
                return
                
            accounting.clear_all_transactions()
            bot.edit_message_text(
                "✅ 已刪除所有交易記錄",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
        elif callback_data == "cancel_action":
            # 取消操作
            bot.edit_message_text(
                "❌ 操作已取消",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_back_to_main_button()
            )
            
        # 處理完成，清除回調通知
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"處理回調時發生錯誤：{str(e)}")
        try:
            bot.answer_callback_query(call.id, "❌ 處理回調時發生錯誤，請稍後再試")
        except:
            pass

@bot.message_handler(func=lambda message: message.text == '管理員列表')
def view_admins_chinese(message):
    """處理'管理員列表'中文命令"""
    view_admins(message)

@bot.message_handler(func=lambda message: message.text == '操作員列表')
def view_operators_chinese(message):
    """處理'操作員列表'中文命令"""
    view_operators(message)

@bot.message_handler(func=lambda message: message.text == '清除今日記錄')
def clear_today_transactions_chinese(message):
    """處理'清除今日記錄'中文命令"""
    clear_today_transactions(message)

@bot.message_handler(func=lambda message: message.text == '清除本月記錄')
def clear_month_transactions_chinese(message):
    """處理'清除本月記錄'中文命令"""
    clear_month_transactions(message)

@bot.message_handler(func=lambda message: message.text == '清除所有記錄')
def clear_all_transactions_chinese(message):
    """處理'清除所有記錄'中文命令"""
    clear_all_transactions(message)

@bot.message_handler(func=lambda message: message.text and message.text.startswith('標記為已下發 '))
def mark_transaction_processed_chinese(message):
    """處理'標記為已下發'中文命令"""
    try:
        transaction_id = message.text.replace('標記為已下發', '').strip()
        if not transaction_id or not transaction_id.isdigit():
            bot.reply_to(message, "❌ 格式錯誤！請使用：標記為已下發 交易ID")
            return
        
        # 創建模擬的命令消息
        simulated_text = f"/mark {transaction_id}"
        message.text = simulated_text
        mark_transaction_processed(message)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理標記交易時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '取消最後一筆入款')
def cancel_last_deposit_chinese(message):
    """處理'取消最後一筆入款'中文命令"""
    cancel_last_deposit(message)

@bot.message_handler(func=lambda message: message.text == '取消最後一筆出款')
def cancel_last_withdrawal_chinese(message):
    """處理'取消最後一筆出款'中文命令"""
    cancel_last_withdrawal(message)

@bot.message_handler(func=lambda message: message.text == '重新啟動機器人' or message.text == '重啟')
def restart_bot_chinese(message):
    """處理'重新啟動機器人'和'重啟'中文命令"""
    restart_bot(message)

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定費率'))
def set_fee_rate_chinese(message):
    """處理'設定費率'中文命令"""
    # 從消息中提取費率值
    try:
        fee_str = message.text.replace('設定費率', '').strip()
        if not fee_str:
            bot.reply_to(message, "❌ 格式錯誤！請使用：設定費率 數字")
            return
        
        # 創建模擬的命令消息
        simulated_text = f"/fee {fee_str}"
        message.text = simulated_text
        set_fee_rate(message)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理費率設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '查看地址')
def show_address_chinese(message):
    """處理'查看地址'中文命令"""
    show_address(message)

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定地址 '))
def set_address_chinese(message):
    """處理'設定地址'中文命令"""
    try:
        address_content = message.text[5:].strip()  # 跳過"設定地址 "
        if not address_content:
            bot.reply_to(message, "❌ 格式錯誤！請使用：設定地址 內容")
            return
        
        # 創建模擬的命令消息
        simulated_text = f"/set_address {address_content}"
        message.text = simulated_text
        set_address(message)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理地址設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定歡迎詞 '))
def set_welcome_chinese(message):
    """處理'設定歡迎詞'中文命令"""
    try:
        welcome_content = message.text[6:].strip()  # 跳過"設定歡迎詞 "
        
        # 設定歡迎詞並進入等待狀態
        message.text = "/set_welcome"
        set_welcome(message)
        
        # 立即處理歡迎詞內容
        if welcome_content:
            # 模擬使用者輸入歡迎詞
            welcome_msg = telebot.types.Message(
                message_id=message.message_id, 
                from_user=message.from_user,
                date=message.date, 
                chat=message.chat,
                content_type='text', 
                options={}, 
                json_string=None
            )
            welcome_msg.text = welcome_content
            handle_welcome_input(welcome_msg)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理歡迎詞設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定管理員 @'))
def set_admin_chinese(message):
    """處理'設定管理員'中文命令"""
    try:
        username = message.text.split('@', 1)[1].strip()
        if not username:
            bot.reply_to(message, "❌ 格式錯誤！請使用：設定管理員 @用戶名")
            return
        
        # 創建模擬的命令消息
        simulated_text = f"/set_admin @{username}"
        message.text = simulated_text
        set_admin(message)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理管理員設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定操作員 @'))
def set_operator_chinese(message):
    """處理'設定操作員'中文命令"""
    try:
        username = message.text.split('@', 1)[1].strip()
        if not username:
            bot.reply_to(message, "❌ 格式錯誤！請使用：設定操作員 @用戶名")
            return
        
        # 創建模擬的命令消息
        simulated_text = f"/set_operator @{username}"
        message.text = simulated_text
        set_operator(message)
    except Exception as e:
        bot.reply_to(message, f"❌ 處理操作員設定時發生錯誤：{str(e)}")

# 添加對應於固定按鈕的處理方法
@bot。message_handler(功能=拉姆達 訊息:訊息。文字 == "日月")
定義 固定_今日_報告(訊息):
    顯示_今日_報告(訊息)

@bot。message_handler(功能=拉姆達 訊息:訊息。文字 == "你")
定義 固定_歷史_報告(訊息):
    """“““““””
 user_id = 訊息。來自_用戶.身份證
    
    如果 不是 is_運算符(用戶_id):
 機器人。回覆_to(訊息, "“““ “ “ “ “ ””)
        返回
    
    日誌_訊息(訊息, "你")
 機器人。回覆_to(訊息, "我同意:",回覆_標記=取得_history_menu())

@bot。message_handler(功能=拉姆達 訊息:訊息。文字 == "你")
定義 固定_月_報告(訊息):
    顯示_月_報告(訊息)

@bot。message_handler(功能=拉姆達 訊息:訊息。文字 == "艾尼")
定義 固定_取消_存款(訊息):
    取消_last_deposit(訊息)

@bot。message_handler(功能=拉姆達 訊息:訊息。文字 == "你")
定義 固定_速率_設定(訊息):
    設定_exchange_rate(訊息)

@bot。message_handler(功能=拉姆達 訊息:訊息。文字 == "奧蘇")
定義 固定_取消_撤回(訊息):
    取消_last_撤回(訊息)

如果 __name__== '__主__':
    嘗試:
 記錄器。資訊("我個人...")
        
        # # 收入
 bot_running = 真實的
        
        # #
        開始_心跳()
        
        # “鐵路”webhook（）
        # “ORAilwayys inic”,“webhook”
 連接埠 = 整數(作業系統。環境.得到('港口', 8080))
        
        # # 人物
 記錄器。資訊("...")
 機器人。投票(無_停止=真實的,間隔=0)
    除了 例外 作為 乙:
 bot_running = 虛假的
 記錄器。錯誤(f」即個人清白:{str(e)}")
    最後:
 bot_running = 虛假的
 記錄器。資訊("我個人")
