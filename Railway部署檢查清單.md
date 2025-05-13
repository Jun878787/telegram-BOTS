# Railway 部署檢查清單

## 準備工作

### GitHub 倉庫設置
- [ ] 創建 GitHub 倉庫 (單個或多個)
- [ ] 確保每個機器人代碼都已推送到 GitHub
- [ ] 檢查 .gitignore 文件是否正確 (排除敏感配置文件和私鑰)

### 配置文件
- [ ] 每個機器人都有 railway.json 文件
- [ ] 環境變數範例文件 (.env.example) 已更新
- [ ] requirements.txt 文件包含所有必要依賴
- [ ] Procfile 已正確配置啟動命令

## Railway 部署

### 車隊總帳機器人
- [ ] 在 Railway 中創建新專案
- [ ] 連接 GitHub 倉庫
- [ ] 設置以下環境變數:
  - [ ] TELEGRAM_BOT_TOKEN=車隊總帳機器人的令牌
  - [ ] PORT=8080 (或其他端口)
  - [ ] TZ=Asia/Taipei
  - [ ] 其他必要的環境變數
- [ ] 記錄 SERVICE_ID (用於排程任務)

### 業績管家機器人 1
- [ ] 在 Railway 中創建新專案
- [ ] 連接 GitHub 倉庫
- [ ] 設置以下環境變數:
  - [ ] TELEGRAM_BOT_TOKEN=業績管家機器人1的令牌
  - [ ] PORT=8080 (或其他端口)
  - [ ] TZ=Asia/Taipei
  - [ ] 其他必要的環境變數
- [ ] 記錄 SERVICE_ID (用於排程任務)

### 業績管家機器人 2
- [ ] 在 Railway 中創建新專案
- [ ] 連接 GitHub 倉庫
- [ ] 設置以下環境變數:
  - [ ] TELEGRAM_BOT_TOKEN=業績管家機器人2的令牌
  - [ ] PORT=8080 (或其他端口)
  - [ ] TZ=Asia/Taipei
  - [ ] 其他必要的環境變數
- [ ] 記錄 SERVICE_ID (用於排程任務)

## 排程任務設置

### 獲取 API 密鑰
- [ ] 在 Railway 平台獲取 API 密鑰
- [ ] 在排程伺服器上設置 API 密鑰和 SERVICE_ID 環境變數

### 設置啟動/關閉時間
- [ ] 設置啟動任務 (07:00): 調用 `python railway_scheduler.py start`
- [ ] 設置關閉任務 (02:00): 調用 `python railway_scheduler.py stop`

### 選項 A: 使用 Railway 上的 Cron Job
- [ ] 將 railway_scheduler.py 部署到單獨的 Railway 服務
- [ ] 設置每日 07:00 執行啟動腳本
- [ ] 設置每日 02:00 執行關閉腳本

### 選項 B: 使用外部排程服務
- [ ] 在外部伺服器設置 Cron Job (如 Linux crontab)
```
0 7 * * * /path/to/python /path/to/railway_scheduler.py start
0 2 * * * /path/to/python /path/to/railway_scheduler.py stop
```

## 多機器人協同工作設置

- [ ] 修改每個機器人的指令前綴
- [ ] 在 BotFather 中更新指令列表
- [ ] 修改機器人代碼，添加消息過濾條件
- [ ] 確保每個機器人使用獨立的數據存儲
- [ ] 如使用 Webhook，設置不同的 Webhook 路徑

## 部署後測試

- [ ] 驗證每個機器人是否正常運行
- [ ] 測試定時啟動和關閉功能
- [ ] 確認多機器人在同一群組中互不干擾
- [ ] 測試所有主要功能 