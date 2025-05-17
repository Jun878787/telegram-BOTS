# 停止所有機器人的PowerShell腳本

Write-Host "正在停止所有Telegram機器人..." -ForegroundColor Green

# 檢查是否存在記錄進程ID的文件
if (Test-Path "$PSScriptRoot\bot_processes.txt") {
    # 從文件讀取進程ID
    $processIds = Get-Content -Path "$PSScriptRoot\bot_processes.txt" -Raw
    $processIds = $processIds.Split(",")
    
    foreach ($id in $processIds) {
        try {
            if ($id -ne "") {
                Stop-Process -Id $id -ErrorAction SilentlyContinue
                Write-Host "已停止進程ID: $id" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "無法停止進程ID: $id - 可能已不存在" -ForegroundColor Yellow
        }
    }
    
    # 刪除進程ID文件
    Remove-Item -Path "$PSScriptRoot\bot_processes.txt" -Force
    Write-Host "已刪除進程ID記錄文件" -ForegroundColor Green
} else {
    # 如果找不到進程ID文件，嘗試通過進程名稱尋找和停止
    Write-Host "找不到進程ID記錄文件，嘗試通過進程名稱停止機器人..." -ForegroundColor Yellow
    
    $pythonProcesses = Get-Process -Name python3 -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        foreach ($process in $pythonProcesses) {
            Stop-Process -Id $process.Id -Force
            Write-Host "已停止Python進程ID: $($process.Id)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "沒有找到正在運行的Python進程" -ForegroundColor Yellow
    }
}

Write-Host "所有機器人已停止" -ForegroundColor Green 