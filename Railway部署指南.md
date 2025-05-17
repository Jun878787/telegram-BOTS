# Railway 部署指南

本文件將指導您如何將三個 Telegram 機器人部署到 Railway 平台。

## 準備工作

請確保您已完成 [GitHub部署指南.md](GitHub部署指南.md) 中的所有步驟，並且代碼已成功推送到 GitHub 儲存庫。

## 機器人信息

1. **格式化列表機器人 (Automatic List-Bot)**
   - GitHub 路徑: `https://github.com/Jun878787/telegram-BOTS/tree/main/performance-manager-bot-2`
   - Bot Token: `7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg`
   - SERVICE_ID: `749549f8-5561-4fc3-b634-3657e2e4c2cf`

2. **車隊總表機器人 (Fleet SummAry-Bot)**
   - GitHub 路徑: `https://github.com/Jun878787/telegram-BOTS/tree/main/fleet-accounting-bot`
   - Bot Token: `7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw`
   - SERVICE_ID: `d82f533f-e9f7-4e3f-86e2-5b3133fac13a`

3. **群組別總表機器人 (Performance General List-Bot)**
   - GitHub 路徑: `https://github.com/Jun878787/telegram-BOTS/tree/main/performance-manager-bot-1`
   - Bot Token: `7582678588:AAGrU4u06xT8qP-t0L4TZE0BmJf9N44L2Hg`
   - SERVICE_ID: `d08978ea-90c6-4a9e-8a36-cc2f3319d3e7`

## Railway 部署步驟

### 1. 創建 Railway 帳號

1. 前往 [Railway](https://railway.app/) 並使用 GitHub 帳號登入
2. 如果您是第一次使用 Railway，可能需要完成電子郵件驗證

### 2. 為每個機器人創建 Railway 專案

對於每個機器人，請按照以下步驟操作：

#### 機器人 1: 格式化列表機器人 (Automatic List-Bot)

1. 在 Railway 控制台中，點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇您的 GitHub 儲存庫 `Jun878787/telegram-BOTS`
4. 選擇部署分支 `main` 和子目錄 `/performance-manager-bot-2`
5. 按照以下步驟設置環境變數

環境變數設置：
```
TELEGRAM_BOT_TOKEN=7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg
SERVICE_ID=749549f8-5561-4fc3-b634-3657e2e4c2cf
PORT=8080
TZ=Asia/Taipei
TARGET_GROUP_ID=-1002557176274
ADMIN_IDS=7842840472
```

#### 機器人 2: 車隊總表機器人 (Fleet SummAry-Bot)

1. 在 Railway 控制台中，點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇您的 GitHub 儲存庫 `Jun878787/telegram-BOTS`
4. 選擇部署分支 `main` 和子目錄 `/fleet-accounting-bot`
5. 按照以下步驟設置環境變數

環境變數設置：
```
TELEGRAM_BOT_TOKEN=7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw
SERVICE_ID=d82f533f-e9f7-4e3f-86e2-5b3133fac13a
PORT=8080
TZ=Asia/Taipei
TARGET_GROUP_ID=-1002557176274
ADMIN_IDS=7842840472
```

#### 機器人 3: 群組別總表機器人 (Performance General List-Bot)

1. 在 Railway 控制台中，點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇您的 GitHub 儲存庫 `Jun878787/telegram-BOTS`
4. 選擇部署分支 `main` 和子目錄 `/performance-manager-bot-1`
5. 按照以下步驟設置環境變數

環境變數設置：
```
TELEGRAM_BOT_TOKEN=7582678588:AAGrU4u06xT8qP-t0L4TZE0BmJf9N44L2Hg
SERVICE_ID=d08978ea-90c6-4a9e-8a36-cc2f3319d3e7
PORT=8080
TZ=Asia/Taipei
TARGET_GROUP_ID=-1002557176274
ADMIN_IDS=7842840472
```

### 3. 啟動部署

1. 完成環境變數設置後，Railway 會自動開始部署
2. 您可以在 Railway 控制台中監視部署進度
3. 部署完成後，每個機器人都將獲得一個唯一的 Railway 服務 URL

### 4. 設置定時運行（可選）

如果需要設置機器人在特定時間自動啟動和關閉，您可以使用 Railway 的 Cron 服務：

1. 在 Railway 控制台中，前往您的專案
2. 點擊 "Add"，選擇 "Cron Jobs" 服務
3. 設置每天 07:00 啟動機器人的 Cron 表達式：`0 7 * * *`
4. 設置每天 02:00 關閉機器人的 Cron 表達式：`0 2 * * *`

## 驗證部署

部署完成後，您可以通過以下方式驗證機器人是否正常運行：

1. 在 Telegram 中搜尋您的機器人用戶名
2. 發送相應的啟動命令：
   - 格式化列表機器人: `/list_start`
   - 車隊總表機器人: `/acc_start`
   - 組別總表機器人: `/pm1_start`
3. 如果機器人回應，則說明部署成功

## 常見問題

1. **部署失敗**: 檢查 Railway 日誌以獲取詳細的錯誤信息
2. **機器人無響應**: 確認您已正確設置所有環境變數
3. **Webhook 設置錯誤**: 確保 PORT 環境變數設置為 8080

## 後續步驟

成功部署後，您可能需要：

1. 設置機器人的管理員權限
2. 配置 Webhook 以處理事件
3. 設置定時任務自動啟動和關閉機器人

如有任何問題，請參考 Railway 文檔或聯繫支持團隊。 