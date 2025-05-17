# 啟動格式化列表機器人
$env:PYTHONIOENCODING = "utf-8"
Set-Location -Path "$PSScriptRoot\Automatic List-Bot"
Start-Process -FilePath "python3" -ArgumentList "bot.py" -NoNewWindow 