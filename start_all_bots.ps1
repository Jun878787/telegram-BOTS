# 啟動所有 Telegram 機器人
Write-Host "正在啟動所有 Telegram 機器人..." -ForegroundColor Green

# 啟動格式化列表機器人
$bot1 = Start-Process -FilePath "powershell" -ArgumentList "-File .\setup_env.ps1; Set-Location -Path '.\Automatic List-Bot'; python bot.py" -PassThru -WindowStyle Hidden
Write-Host "格式化列表機器人已啟動，進程ID: $($bot1.Id)" -ForegroundColor Cyan

# 啟動車隊總表機器人
$bot2 = Start-Process -FilePath "powershell" -ArgumentList "-File .\setup_fleet_bot.ps1; Set-Location -Path '.\Fleet SummAry-Bot'; python bot.py" -PassThru -WindowStyle Hidden
Write-Host "車隊總表機器人已啟動，進程ID: $($bot2.Id)" -ForegroundColor Cyan

# 啟動組別總表機器人
$bot3 = Start-Process -FilePath "powershell" -ArgumentList "-File .\setup_performance_bot.ps1; Set-Location -Path '.\Performance General List-Bot'; python bot.py" -PassThru -WindowStyle Hidden
Write-Host "組別總表機器人已啟動，進程ID: $($bot3.Id)" -ForegroundColor Cyan

Write-Host "所有機器人已成功啟動。使用以下指令可以檢查機器人進程:" -ForegroundColor Green
Write-Host "Get-Process -Id $($bot1.Id),$($bot2.Id),$($bot3.Id)" -ForegroundColor Yellow

Write-Host "要停止所有機器人，請使用以下指令:" -ForegroundColor Green
Write-Host "Stop-Process -Id $($bot1.Id),$($bot2.Id),$($bot3.Id)" -ForegroundColor Yellow

# 儲存進程ID到文件中，以便以後停止
"$($bot1.Id),$($bot2.Id),$($bot3.Id)" | Out-File -FilePath "bot_processes.txt"
Write-Host "所有機器人進程ID已保存到 bot_processes.txt" -ForegroundColor Green 