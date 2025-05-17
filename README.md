# Telegram 機器人部署指南

本專案包含三個 Telegram 機器人，可部署到 GitHub 和 Railway 平台。

## 機器人列表

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

## 快速開始

### 自動設置（推薦）

使用提供的設置腳本快速設置所有機器人：

```bash
chmod +x setup.sh
./setup.sh
```

### 手動設置

請查看以下文件，了解完整的部署流程：

- [GitHub部署指南.md](GitHub部署指南.md) - 如何將機器人部署到 GitHub
- [Railway部署指南.md](Railway部署指南.md) - 如何將機器人部署到 Railway
- [Railway部署檢查清單.md](Railway部署檢查清單.md) - 部署前的檢查清單

## 主要步驟摘要

1. **GitHub 設置**：
   - 創建代碼倉庫
   - 設置 SSH 部署金鑰
   - 推送機器人代碼

2. **Railway 部署**：
   - 為每個機器人創建 Railway 專案
   - 設置環境變數
   - 部署應用

3. **定時運行設置**：
   - 使用 Railway 的 Cron 服務設定運行時間
   - 可設置為 07:00 啟動，02:00 關閉

## 機器人功能概述

### 格式化列表機器人 (Automatic List-Bot)
- 指令前綴: `/list_`
- 主要功能: 處理和格式化列表數據
- 命令列表:
  - `/list_start` - 啟動機器人
  - `/list_help` - 顯示幫助信息
  - `/list_status` - 顯示機器人狀態

### 車隊總表機器人 (Fleet SummAry-Bot)
- 指令前綴: `/acc_`
- 主要功能: 管理車隊總帳數據
- 命令列表:
  - `/acc_start` - 啟動機器人
  - `/acc_help` - 顯示幫助信息
  - `/acc_status` - 顯示機器人狀態

### 群組別總表機器人 (Performance General List-Bot)
- 指令前綴: `/pm1_`
- 主要功能: 管理組別業績數據
- 命令列表:
  - `/pm1_start` - 啟動機器人
  - `/pm1_help` - 顯示幫助信息
  - `/pm1_status` - 顯示機器人狀態

## 目標群組與管理員設定

- 目標群組 ID: `-1002557176274` (👀 Fenny_私人倉庫)
- 管理員 ID: `7842840472` (北金國際-M8P-Ann)

## 文件說明

- `railway.json` - Railway 部署配置
- `railway.toml` - Railway 專案設定
- `requirements.txt` - Python 依賴列表
- `Procfile` - 定義 Railway 啟動命令
- `.env.example` - 環境變數範例

## 常見問題

1. **機器人無法啟動**: 檢查環境變數和依賴是否正確設置
2. **排程任務失敗**: 確認 API 密鑰和 SERVICE_ID 是否正確
3. **機器人指令衝突**: 確保每個機器人使用唯一的指令前綴 