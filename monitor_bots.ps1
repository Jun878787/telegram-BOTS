# 監控 Telegram 機器人進程的腳本

Write-Host "正在檢查 Telegram 機器人進程..." -ForegroundColor Green

# 檢查所有 Python 相關進程
$pythonProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*py*" -or 
    $_.MainWindowTitle -like "*python*" -or 
    $_.MainWindowTitle -like "*bot*" 
}

if ($pythonProcesses) {
    Write-Host "找到以下 Python 相關進程:" -ForegroundColor Cyan
    $pythonProcesses | Format-Table -Property Id, ProcessName, Path, StartTime
} else {
    Write-Host "沒有找到 Python 相關進程" -ForegroundColor Yellow
}

# 檢查可能的 Telegram 機器人進程
$allProcesses = Get-Process
Write-Host "正在檢查所有進程的命令行參數以查找 bot.py..." -ForegroundColor Green

foreach ($process in $allProcesses) {
    try {
        $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
        if ($cmdLine -like "*bot.py*") {
            Write-Host "找到可能的機器人進程:" -ForegroundColor Cyan
            Write-Host "進程ID: $($process.Id), 名稱: $($process.ProcessName), 命令行: $cmdLine" -ForegroundColor Cyan
        }
    } catch {
        # 忽略錯誤
    }
}

# 檢查 .env 文件是否正確載入
Write-Host "檢查環境變數設置..." -ForegroundColor Green
$envFiles = Get-ChildItem -Path $PSScriptRoot -Recurse -Filter ".env" -File
if ($envFiles) {
    Write-Host "找到以下 .env 文件:" -ForegroundColor Cyan
    $envFiles | Format-Table -Property FullName, Length, LastWriteTime
} else {
    Write-Host "沒有找到 .env 文件" -ForegroundColor Yellow
}

# 提供指導
Write-Host "建議:" -ForegroundColor Green
Write-Host "1. 確保 .env 文件存在並包含正確的環境變數" -ForegroundColor Yellow
Write-Host "2. 確保已安裝所有必要的 Python 依賴" -ForegroundColor Yellow
Write-Host "3. 嘗試直接運行 Python 機器人腳本" -ForegroundColor Yellow
Write-Host "4. 檢查 Telegram 應用程序中是否有機器人響應" -ForegroundColor Yellow 