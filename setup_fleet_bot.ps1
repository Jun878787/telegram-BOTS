# PowerShell 腳本設定車隊總表機器人環境變數

# 為當前會話設置環境變數
Write-Host "設定車隊總表機器人環境變數..." -ForegroundColor Green

# 車隊總表機器人環境變數
$Env:TELEGRAM_BOT_TOKEN = "7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw"
Write-Host "已設置車隊總表機器人 Token" -ForegroundColor Cyan

# 其他共享環境變數
$Env:TARGET_GROUP_ID = "-1002557176274"
$Env:ADMIN_IDS = "7842840472"
$Env:PORT = "8080"
$Env:TZ = "Asia/Taipei"
$Env:DEBUG = "False"

Write-Host "已設置共享環境變數" -ForegroundColor Cyan
Write-Host "TARGET_GROUP_ID: $Env:TARGET_GROUP_ID" 
Write-Host "ADMIN_IDS: $Env:ADMIN_IDS"
Write-Host "PORT: $Env:PORT"
Write-Host "TZ: $Env:TZ"

Write-Host "環境變數設定完成!" -ForegroundColor Green 