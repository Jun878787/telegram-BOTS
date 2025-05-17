# 停止所有 Telegram 機器人
Write-Host "停止所有 Telegram 機器人..." -ForegroundColor Green

# 檢查進程ID文件是否存在
if (Test-Path -Path "bot_processes.txt") {
    # 從文件中讀取進程ID
    $processIds = Get-Content -Path "bot_processes.txt" -Raw
    $processIds = $processIds.Trim().Split(",")
    
    # 停止每個進程
    foreach ($id in $processIds) {
        try {
            Stop-Process -Id $id -Force -ErrorAction Stop
            Write-Host "成功停止進程 ID: $id" -ForegroundColor Cyan
        }
        catch {
            Write-Host "無法停止進程 ID: $id. 錯誤: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # 刪除進程ID文件
    Remove-Item -Path "bot_processes.txt" -Force
    Write-Host "進程ID文件已刪除" -ForegroundColor Cyan
}
else {
    Write-Host "找不到進程ID文件。嘗試通過名稱查找Python進程..." -ForegroundColor Yellow
    
    # 通過名稱查找並停止Python進程
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        foreach ($process in $pythonProcesses) {
            try {
                $process | Stop-Process -Force
                Write-Host "成功停止進程: $($process.Name) (ID: $($process.Id))" -ForegroundColor Cyan
            }
            catch {
                Write-Host "無法停止進程: $($process.Name) (ID: $($process.Id)). 錯誤: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    else {
        Write-Host "找不到正在運行的Python進程" -ForegroundColor Yellow
    }
}

Write-Host "所有機器人已停止" -ForegroundColor Green 