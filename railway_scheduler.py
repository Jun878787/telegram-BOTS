#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import os
import sys
import time
import datetime
import argparse
import json

# 相關配置，請替換成您的實際資訊
API_KEY = os.environ.get("RAILWAY_API_KEY", "")  # 從環境變數獲取或手動設置
SERVICE_IDS = {
    "fleet-accounting": os.environ.get("FLEET_ACCOUNTING_SERVICE_ID", ""),
    "performance-manager-1": os.environ.get("PERFORMANCE_MANAGER_1_SERVICE_ID", ""),
    "performance-manager-2": os.environ.get("PERFORMANCE_MANAGER_2_SERVICE_ID", "")
}

RAILWAY_API_BASE = "https://api.railway.app/v2"


def start_service(service_id):
    """啟動指定的Railway服務"""
    url = f"{RAILWAY_API_BASE}/services/{service_id}/restart"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f"成功啟動服務 {service_id}")
        return True
    else:
        print(f"啟動服務 {service_id} 失敗: {response.text}")
        return False


def stop_service(service_id):
    """停止指定的Railway服務"""
    url = f"{RAILWAY_API_BASE}/services/{service_id}/stop"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f"成功停止服務 {service_id}")
        return True
    else:
        print(f"停止服務 {service_id} 失敗: {response.text}")
        return False


def manage_services(action):
    """管理所有機器人服務"""
    if not API_KEY:
        print("錯誤: 未設置 RAILWAY_API_KEY 環境變數或直接在腳本中配置")
        return False
    
    success = True
    for name, service_id in SERVICE_IDS.items():
        if not service_id:
            print(f"警告: 未設置 {name} 的服務ID")
            continue
        
        if action == "start":
            success = success and start_service(service_id)
        elif action == "stop":
            success = success and stop_service(service_id)
    
    return success


def main():
    parser = argparse.ArgumentParser(description="Railway 服務排程管理工具")
    parser.add_argument("action", choices=["start", "stop"], help="要執行的操作: start 啟動服務, stop 停止服務")
    args = parser.parse_args()
    
    now = datetime.datetime.now()
    print(f"時間: {now.strftime('%Y-%m-%d %H:%M:%S')} - 執行操作: {args.action}")
    
    if manage_services(args.action):
        print("所有操作已完成")
        sys.exit(0)
    else:
        print("操作過程中發生錯誤")
        sys.exit(1)


if __name__ == "__main__":
    main()

# 車隊總帳機器人
with open("fleet_accounting_data.json", "w") as f:
    json.dump(data, f)

# 業績管家機器人1
with open("performance_manager_1_data.json", "w") as f:
    json.dump(data, f)

# 車隊總帳機器人
updater.start_webhook(listen="0.0.0.0", port=PORT, url_path="bot1_webhook")
updater.bot.set_webhook("https://您的域名/bot1_webhook")

# 業績管家機器人1
updater.start_webhook(listen="0.0.0.0", port=PORT, url_path="bot2_webhook") 