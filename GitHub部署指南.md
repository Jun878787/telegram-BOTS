# Telegram 機器人 GitHub 部署指南

## 前置準備

1. 確保您有一個 GitHub 帳戶
2. 確保您的機器人令牌是有效的
3. 確保目標群組 ID 是正確的
4. 準備好所需的環境變數

## 第一步：創建 GitHub 倉庫

1. 登入 GitHub
2. 點擊右上角的 "+" 圖標，選擇 "New repository"
3. 填寫倉庫名稱，例如 `telegram-bots`
4. 選擇 "Private"（如果您想保持私有）
5. 點擊 "Create repository"

## 第二步：上傳代碼到 GitHub

方法一：使用 Git 命令行
```bash
# 初始化本地倉庫
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit"

# 添加遠程倉庫
git remote add origin https://github.com/您的用戶名/telegram-bots.git

# 推送到主分支
git push -u origin main
```

方法二：使用 GitHub 桌面版
1. 下載並安裝 [GitHub Desktop](https://desktop.github.com/)
2. 登入您的 GitHub 帳戶
3. 創建新倉庫或添加現有倉庫
4. 提交更改
5. 點擊 "Push origin"

## 第三步：設置 GitHub Secrets

1. 在您的倉庫頁面，點擊 "Settings" 標籤
2. 在左側選單中選擇 "Secrets and variables" > "Actions"
3. 點擊 "New repository secret"
4. 添加以下 Secrets：
   - TELEGRAM_LIST_BOT_TOKEN: 格式化列表機器人的令牌
   - TELEGRAM_FLEET_BOT_TOKEN: 車隊總表機器人的令牌
   - TELEGRAM_PERFORMANCE_BOT_TOKEN: 組別總表機器人的令牌
   - TARGET_GROUP_ID: 目標群組的 ID
   - ADMIN_IDS: 管理員用戶的 ID

## 第四步：配置 GitHub Actions

我們已經創建了 GitHub Actions 工作流程配置文件 `.github/workflows/deploy_bots.yml`，它自動處理以下步驟：

1. 檢出代碼
2. 設置 Python 環境
3. 安裝依賴
4. 創建環境變數文件
5. 測試機器人連接
6. 創建運行和停止腳本

您可以在倉庫頁面的 "Actions" 標籤中查看工作流程的執行情況。

## 第五步：手動觸發部署

1. 在倉庫頁面，點擊 "Actions" 標籤
2. 在左側選擇 "Deploy Telegram Bots" 工作流程
3. 點擊 "Run workflow" 按鈕
4. 選擇要部署的分支（通常是 main 或 master）
5. 點擊 "Run workflow" 開始部署

## 故障排除

如果部署失敗，請檢查以下幾點：

1. GitHub Actions 日誌是否有錯誤信息
2. 機器人令牌是否正確
3. 目標群組 ID 是否正確
4. 依賴是否正確安裝
5. 代碼是否有語法錯誤

## 注意事項

1. 請勿在公共倉庫中存儲敏感信息，如機器人令牌
2. 使用 Secrets 來保存敏感信息
3. 定期檢查機器人的運行狀態
4. 如需修改代碼，請在本地測試後再推送到 GitHub

## 實用指令

```bash
# 檢查機器人進程
ps aux | grep "python bot.py"

# 檢查機器人日誌
cat logs/bot_log_*.txt

# 手動啟動機器人
./run_bots.sh

# 手動停止機器人
./stop_bots.sh

# 測試機器人連接
python test_connection.py
``` 