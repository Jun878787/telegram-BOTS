# 啟動車隊總表機器人
Write-Host "正在啟動車隊總表機器人..." -ForegroundColor Green

# 首先設置環境變數
. .\setup_fleet_bot.ps1

# 切換到機器人目錄
Set-Location -Path ".\Fleet SummAry-Bot"

# 啟動機器人
python bot.py

# 保持腳本運行
Write-Host "已啟動車隊總表機器人。按任意鍵結束..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 