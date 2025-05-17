#!/bin/bash

# 快速設置腳本 - 設置三個 Telegram 機器人

echo "開始設置 Telegram 機器人..."

# 檢查 Git 是否安裝
if ! command -v git &>/dev/null; then
    echo "請先安裝 Git"
    exit 1
fi

# 檢查是否已有 SSH 金鑰
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "設置 SSH 金鑰..."
    mkdir -p ~/.ssh
    cat > ~/.ssh/id_ed25519 << 'EOL'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDP8q+h0nrOuI6NyTUsQ6X0QhQdNEXdgQNdv58BJRXbwAAAAKDpN9Sh6TfU
oQAAAAtzc2gtZWQyNTUxOQAAACDP8q+h0nrOuI6NyTUsQ6X0QhQdNEXdgQNdv58BJRXbwA
AAAEAF2xeXQbPaOBQk1LGkVbmlVTnurDgFx0mW4m7gCAWLa8/yr6HSes64jo3JNSxDpfRC
FB00Rd2BA12/nwElFdvAAAAAHGRlcGxveS1rZXktZm9yLXRlbGVncmFtLUJPVFMB
-----END OPENSSH PRIVATE KEY-----
EOL
    chmod 600 ~/.ssh/id_ed25519
    
    # 添加到 ssh-agent
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519
fi

# 克隆儲存庫
if [ ! -d "telegram-BOTS" ]; then
    echo "克隆 telegram-BOTS 儲存庫..."
    git clone git@github.com:Jun878787/telegram-BOTS.git
    cd telegram-BOTS
else
    echo "已存在 telegram-BOTS 目錄，正在更新..."
    cd telegram-BOTS
    git pull
fi

# 創建 .env 文件
echo "創建環境變數文件..."

# Automatic List-Bot
cat > Automatic\ List-Bot/.env << EOL
# 格式化列表機器人 (Automatic List-Bot) 環境變數
TELEGRAM_BOT_TOKEN=7946349508:AAGyixEKL0PCQv6J_F7FNljVnndR1PUE8yg
RAILWAY_API_KEY=8e48c716-7fd3-4372-afe8-1e3e60c218db
SERVICE_ID=749549f8-5561-4fc3-b634-3657e2e4c2cf
PORT=8080
TZ=Asia/Taipei
TARGET_GROUP_ID=-1002557176274
ADMIN_IDS=7842840472
DEBUG=False
EOL

# Fleet SummAry-Bot
cat > Fleet\ SummAry-Bot/.env << EOL
# 車隊總表機器人 (Fleet SummAry-Bot) 環境變數
TELEGRAM_BOT_TOKEN=7205575949:AAHLA8VpXWBJXhPe9riEym6aOaAvojw_UWw
RAILWAY_API_KEY=8e48c716-7fd3-4372-afe8-1e3e60c218db
SERVICE_ID=d82f533f-e9f7-4e3f-86e2-5b3133fac13a
PORT=8080
TZ=Asia/Taipei
TARGET_GROUP_ID=-1002557176274
ADMIN_IDS=7842840472
DEBUG=False
EOL

# Performance General List-Bot
cat > Performance\ General\ List-Bot/.env << EOL
# 群組別總表機器人 (Performance General List-Bot) 環境變數
TELEGRAM_BOT_TOKEN=7582678588:AAGrU4u06xT8qP-t0L4TZE0BmJf9N44L2Hg
RAILWAY_API_KEY=8e48c716-7fd3-4372-afe8-1e3e60c218db
SERVICE_ID=d08978ea-90c6-4a9e-8a36-cc2f3319d3e7
PORT=8080
TZ=Asia/Taipei
TARGET_GROUP_ID=-1002557176274
ADMIN_IDS=7842840472
DEBUG=False
EOL

echo "環境變數已設置完成"

# 安裝依賴
echo "安裝依賴..."
pip install -r requirements.txt

echo "設置完成！ 請閱讀以下文件進行下一步操作："
echo "1. GitHub部署指南.md - 將機器人部署到 GitHub"
echo "2. Railway部署指南.md - 將機器人部署到 Railway"

echo "您現在可以使用以下命令在本地測試機器人："
echo "cd Automatic\ List-Bot && python bot.py"
echo "cd Fleet\ SummAry-Bot && python bot.py"
echo "cd Performance\ General\ List-Bot && python bot.py" 