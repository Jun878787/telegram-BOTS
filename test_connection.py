import telegram
import sys
import os
import traceback

print("開始測試 Telegram 機器人連接...")

# 測試所有機器人的連接
BOT_TOKENS = [
    "7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg",  # 格式化列表機器人
    "7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw",  # 車隊總表機器人
    "7582678588:AAGrU4u06xT8qP-t0L4TZE0BmJf9N44L2Hg"   # 組別總表機器人
]

TARGET_GROUP_ID = "-1002557176274"

print("開始測試 Telegram 機器人連接...")
print(f"目標群組ID: {TARGET_GROUP_ID}")

success = False
for i, token in enumerate(BOT_TOKENS):
    bot_name = ["格式化列表機器人", "車隊總表機器人", "組別總表機器人"][i]
    print(f"\n測試 {bot_name} ({token[:8]}...)")
    
    try:
        bot = telegram.Bot(token=token)
        print("  - 已成功創建機器人對象")
        
        bot_info = bot.get_me()
        print(f"  - 取得機器人資訊: {bot_info.first_name} (@{bot_info.username})")
        
        print(f"  - 嘗試發送測試消息到群組 {TARGET_GROUP_ID}")
        message = bot.send_message(
            chat_id=TARGET_GROUP_ID,
            text=f"這是來自 {bot_name} 的測試消息。如果您看到此消息，表示機器人連接正常。"
        )
        print(f"  - 測試消息發送成功! 消息 ID: {message.message_id}")
        success = True
    except Exception as e:
        print(f"  - 錯誤: {e}")
        print("  - 錯誤詳情:")
        traceback.print_exc()
        print("  - 請檢查網絡連接和Token是否有效")

if success:
    print("\n至少有一個機器人連接成功!")
    print("所有機器人可以正常運行!")
else:
    print("\n所有機器人連接測試失敗。")
    print("請檢查網絡連接和機器人令牌。")
    print("可能的問題:")
    print("1. 網絡連接問題")
    print("2. 機器人令牌無效")
    print("3. 機器人沒有權限發送消息到目標群組")
    print("4. 目標群組ID不正確")

try:
    input("按任意鍵結束測試...")
except:
    pass 