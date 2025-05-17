#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import datetime
import pytz

# 定義數據文件路徑
DATA_FILE = "fleet_accounting_data.json"

# 設定時區
TZ = os.environ.get("TZ", "Asia/Taipei")
timezone = pytz.timezone(TZ)

# 初始化數據結構
def initialize_data():
    """初始化數據結構"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    
    # 初始結構
    return {
        "vehicle_records": {},
        "total_income": 0,
        "total_expense": 0,
        "last_update": datetime.datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    }

# 保存數據
def save_data(data):
    """保存數據到文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 添加車輛記錄
def add_vehicle(data, vehicle_id, vehicle_info):
    """添加新車輛或更新現有車輛信息"""
    if "vehicle_records" not in data:
        data["vehicle_records"] = {}
    
    data["vehicle_records"][vehicle_id] = {
        "info": vehicle_info,
        "income": 0,
        "expense": 0,
        "trips": [],
        "maintenance": []
    }
    
    data["last_update"] = datetime.datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    save_data(data)
    return f"已添加/更新車輛: {vehicle_id}"

# 記錄收入
def add_income(data, vehicle_id, amount, description):
    """記錄車輛收入"""
    if "vehicle_records" not in data or vehicle_id not in data["vehicle_records"]:
        return f"錯誤: 找不到車輛 {vehicle_id}"
    
    # 更新車輛收入
    data["vehicle_records"][vehicle_id]["income"] += amount
    
    # 記錄行程
    trip = {
        "date": datetime.datetime.now(timezone).strftime('%Y-%m-%d'),
        "amount": amount,
        "description": description
    }
    data["vehicle_records"][vehicle_id]["trips"].append(trip)
    
    # 更新總收入
    if "total_income" not in data:
        data["total_income"] = 0
    data["total_income"] += amount
    
    data["last_update"] = datetime.datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    save_data(data)
    return f"已記錄車輛 {vehicle_id} 收入: ${amount} - {description}"

# 記錄支出
def add_expense(data, vehicle_id, amount, category, description):
    """記錄車輛支出"""
    if "vehicle_records" not in data or vehicle_id not in data["vehicle_records"]:
        return f"錯誤: 找不到車輛 {vehicle_id}"
    
    # 更新車輛支出
    data["vehicle_records"][vehicle_id]["expense"] += amount
    
    # 記錄維護/支出
    expense = {
        "date": datetime.datetime.now(timezone).strftime('%Y-%m-%d'),
        "amount": amount,
        "category": category,
        "description": description
    }
    data["vehicle_records"][vehicle_id]["maintenance"].append(expense)
    
    # 更新總支出
    if "total_expense" not in data:
        data["total_expense"] = 0
    data["total_expense"] += amount
    
    data["last_update"] = datetime.datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    save_data(data)
    return f"已記錄車輛 {vehicle_id} 支出: ${amount} - {category} - {description}"

# 獲取車輛報告
def get_vehicle_report(data, vehicle_id):
    """獲取單個車輛的報告"""
    if "vehicle_records" not in data or vehicle_id not in data["vehicle_records"]:
        return f"錯誤: 找不到車輛 {vehicle_id}"
    
    vehicle = data["vehicle_records"][vehicle_id]
    report = f"車輛 {vehicle_id} 報告:\n"
    report += f"基本信息: {vehicle['info']}\n"
    report += f"總收入: ${vehicle['income']}\n"
    report += f"總支出: ${vehicle['expense']}\n"
    report += f"淨利潤: ${vehicle['income'] - vehicle['expense']}\n"
    
    # 最近5筆行程
    if vehicle["trips"]:
        report += "\n最近行程:\n"
        for trip in vehicle["trips"][-5:]:
            report += f"{trip['date']} - ${trip['amount']} - {trip['description']}\n"
    
    # 最近5筆維護記錄
    if vehicle["maintenance"]:
        report += "\n最近支出:\n"
        for maint in vehicle["maintenance"][-5:]:
            report += f"{maint['date']} - ${maint['amount']} - {maint['category']} - {maint['description']}\n"
    
    return report

# 獲取總體報告
def get_summary_report(data):
    """獲取車隊總體報告"""
    if "vehicle_records" not in data:
        return "錯誤: 無車輛記錄"
    
    total_income = data.get("total_income", 0)
    total_expense = data.get("total_expense", 0)
    net_profit = total_income - total_expense
    
    report = "車隊總帳報告:\n"
    report += f"車輛數量: {len(data['vehicle_records'])}\n"
    report += f"總收入: ${total_income}\n"
    report += f"總支出: ${total_expense}\n"
    report += f"淨利潤: ${net_profit}\n"
    report += f"最後更新: {data.get('last_update', '未知')}"
    
    return report 