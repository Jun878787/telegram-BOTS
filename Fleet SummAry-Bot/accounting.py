#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import datetime
import pytz
import logging
from decimal import Decimal, ROUND_HALF_UP

class Accounting:
    """處理車隊業務邏輯的會計類"""
    
    def __init__(self):
        """初始化會計類"""
        self.data_file = "fleet_accounting.json"
        self.TZ = os.environ.get("TZ", "Asia/Taipei")
        self.timezone = pytz.timezone(self.TZ)
        self.logger = logging.getLogger('AccountingLogger')
        
        # 初始化數據
        self.data = self.load_data()
    
    def load_data(self):
        """從文件加載數據"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"載入會計數據時發生錯誤：{str(e)}")
        
        # 返回初始數據結構
        return {
            "vehicles": {},
            "transactions": [],
            "monthly_summary": {},
            "last_update": datetime.datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def save_data(self):
        """保存數據到文件"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.data["last_update"] = datetime.datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            return True
        except Exception as e:
            self.logger.error(f"保存會計數據時發生錯誤：{str(e)}")
            return False
    
    def add_vehicle(self, vehicle_id, vehicle_info, plate_number=None, driver=None):
        """添加或更新車輛"""
        try:
            # 格式化車輛ID為大寫
            vehicle_id = vehicle_id.upper().strip()
            
            # 創建或更新車輛記錄
            if vehicle_id not in self.data.setdefault("vehicles", {}):
                self.data["vehicles"][vehicle_id] = {
                    "info": vehicle_info,
                    "plate_number": plate_number,
                    "driver": driver,
                    "status": "active",
                    "register_date": datetime.datetime.now(self.timezone).strftime('%Y-%m-%d'),
                    "total_income": 0,
                    "total_expense": 0,
                    "trips": [],
                    "maintenance": []
                }
            else:
                # 更新現有車輛資料
                if vehicle_info:
                    self.data["vehicles"][vehicle_id]["info"] = vehicle_info
                if plate_number:
                    self.data["vehicles"][vehicle_id]["plate_number"] = plate_number
                if driver:
                    self.data["vehicles"][vehicle_id]["driver"] = driver
            
            self.save_data()
            return True, f"已新增/更新車輛: {vehicle_id}"
        except Exception as e:
            self.logger.error(f"添加車輛時發生錯誤：{str(e)}")
            return False, f"添加車輛時發生錯誤：{str(e)}"
    
    def add_income(self, vehicle_id, amount, description, date=None):
        """添加車輛收入"""
        try:
            # 格式化車輛ID為大寫
            vehicle_id = vehicle_id.upper().strip()
            
            # 檢查車輛是否存在
            if vehicle_id not in self.data.setdefault("vehicles", {}):
                return False, f"車輛 {vehicle_id} 不存在"
            
            # 轉換金額為Decimal並四捨五入到兩位小數
            try:
                amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except:
                return False, "金額格式錯誤"
            
            # 使用當前日期或指定日期
            if date is None:
                date = datetime.datetime.now(self.timezone).strftime('%Y-%m-%d')
            
            # 添加收入記錄
            trip = {
                "date": date,
                "amount": float(amount),
                "description": description,
                "type": "income"
            }
            
            # 更新車輛總收入
            self.data["vehicles"][vehicle_id]["trips"].append(trip)
            self.data["vehicles"][vehicle_id]["total_income"] += float(amount)
            
            # 添加到交易記錄
            transaction = {
                "date": date,
                "time": datetime.datetime.now(self.timezone).strftime('%H:%M:%S'),
                "vehicle_id": vehicle_id,
                "amount": float(amount),
                "description": description,
                "type": "income"
            }
            self.data.setdefault("transactions", []).append(transaction)
            
            # 更新月度摘要
            month_key = datetime.datetime.now(self.timezone).strftime('%Y-%m')
            if month_key not in self.data.setdefault("monthly_summary", {}):
                self.data["monthly_summary"][month_key] = {
                    "income": 0,
                    "expense": 0,
                    "vehicles": {}
                }
            
            self.data["monthly_summary"][month_key]["income"] += float(amount)
            
            if vehicle_id not in self.data["monthly_summary"][month_key].setdefault("vehicles", {}):
                self.data["monthly_summary"][month_key]["vehicles"][vehicle_id] = {
                    "income": 0,
                    "expense": 0
                }
            
            self.data["monthly_summary"][month_key]["vehicles"][vehicle_id]["income"] += float(amount)
            
            self.save_data()
            return True, f"已新增車輛 {vehicle_id} 收入: ${float(amount)} - {description}"
        except Exception as e:
            self.logger.error(f"添加收入時發生錯誤：{str(e)}")
            return False, f"添加收入時發生錯誤：{str(e)}"
    
    def add_expense(self, vehicle_id, amount, category, description, date=None):
        """添加車輛支出"""
        try:
            # 格式化車輛ID為大寫
            vehicle_id = vehicle_id.upper().strip()
            
            # 檢查車輛是否存在
            if vehicle_id not in self.data.setdefault("vehicles", {}):
                return False, f"車輛 {vehicle_id} 不存在"
            
            # 轉換金額為Decimal並四捨五入到兩位小數
            try:
                amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except:
                return False, "金額格式錯誤"
            
            # 使用當前日期或指定日期
            if date is None:
                date = datetime.datetime.now(self.timezone).strftime('%Y-%m-%d')
            
            # 添加支出記錄
            expense = {
                "date": date,
                "amount": float(amount),
                "category": category,
                "description": description,
                "type": "expense"
            }
            
            # 更新車輛總支出
            self.data["vehicles"][vehicle_id]["maintenance"].append(expense)
            self.data["vehicles"][vehicle_id]["total_expense"] += float(amount)
            
            # 添加到交易記錄
            transaction = {
                "date": date,
                "time": datetime.datetime.now(self.timezone).strftime('%H:%M:%S'),
                "vehicle_id": vehicle_id,
                "amount": float(amount),
                "category": category,
                "description": description,
                "type": "expense"
            }
            self.data.setdefault("transactions", []).append(transaction)
            
            # 更新月度摘要
            month_key = datetime.datetime.now(self.timezone).strftime('%Y-%m')
            if month_key not in self.data.setdefault("monthly_summary", {}):
                self.data["monthly_summary"][month_key] = {
                    "income": 0,
                    "expense": 0,
                    "vehicles": {}
                }
            
            self.data["monthly_summary"][month_key]["expense"] += float(amount)
            
            if vehicle_id not in self.data["monthly_summary"][month_key].setdefault("vehicles", {}):
                self.data["monthly_summary"][month_key]["vehicles"][vehicle_id] = {
                    "income": 0,
                    "expense": 0
                }
            
            self.data["monthly_summary"][month_key]["vehicles"][vehicle_id]["expense"] += float(amount)
            
            self.save_data()
            return True, f"已新增車輛 {vehicle_id} 支出: ${float(amount)} - {category} - {description}"
        except Exception as e:
            self.logger.error(f"添加支出時發生錯誤：{str(e)}")
            return False, f"添加支出時發生錯誤：{str(e)}"
    
    def get_vehicle_report(self, vehicle_id):
        """獲取指定車輛的報表"""
        try:
            # 格式化車輛ID為大寫
            vehicle_id = vehicle_id.upper().strip()
            
            # 檢查車輛是否存在
            if vehicle_id not in self.data.setdefault("vehicles", {}):
                return f"車輛 {vehicle_id} 不存在"
            
            vehicle = self.data["vehicles"][vehicle_id]
            
            # 格式化報表
            report = f"🚗 車輛 {vehicle_id} 報表\n"
            report += f"---------------------------\n"
            report += f"車輛信息: {vehicle.get('info', '未知')}\n"
            if vehicle.get('plate_number'):
                report += f"車牌號碼: {vehicle['plate_number']}\n"
            if vehicle.get('driver'):
                report += f"駕駛員: {vehicle['driver']}\n"
            report += f"狀態: {vehicle.get('status', '活躍')}\n"
            report += f"註冊日期: {vehicle.get('register_date', '未知')}\n"
            report += f"---------------------------\n"
            report += f"總收入: ${vehicle.get('total_income', 0):,.2f}\n"
            report += f"總支出: ${vehicle.get('total_expense', 0):,.2f}\n"
            
            # 計算淨利潤
            net_profit = vehicle.get('total_income', 0) - vehicle.get('total_expense', 0)
            report += f"淨利潤: ${net_profit:,.2f}\n"
            
            # 最近5筆收入
            recent_trips = sorted(vehicle.get('trips', []), key=lambda x: x.get('date', ''), reverse=True)[:5]
            if recent_trips:
                report += f"\n最近收入記錄:\n"
                for trip in recent_trips:
                    report += f"{trip.get('date', '未知')} - ${trip.get('amount', 0):,.2f} - {trip.get('description', '無描述')}\n"
            
            # 最近5筆支出
            recent_expenses = sorted(vehicle.get('maintenance', []), key=lambda x: x.get('date', ''), reverse=True)[:5]
            if recent_expenses:
                report += f"\n最近支出記錄:\n"
                for expense in recent_expenses:
                    report += f"{expense.get('date', '未知')} - ${expense.get('amount', 0):,.2f} - {expense.get('category', '無類別')} - {expense.get('description', '無描述')}\n"
            
            report += f"\n最後更新: {self.data.get('last_update', '未知')}"
            
            return report
        except Exception as e:
            self.logger.error(f"獲取車輛報表時發生錯誤：{str(e)}")
            return f"獲取車輛報表時發生錯誤：{str(e)}"
    
    def get_fleet_summary(self, month=None):
        """獲取車隊總體摘要報表"""
        try:
            # 如果沒有指定月份，使用當前月份
            if month is None:
                month = datetime.datetime.now(self.timezone).strftime('%Y-%m')
            
            # 檢查是否有該月數據
            if month not in self.data.setdefault("monthly_summary", {}):
                # 如果沒有該月數據，計算所有數據
                total_income = sum(v.get('total_income', 0) for v in self.data.get('vehicles', {}).values())
                total_expense = sum(v.get('total_expense', 0) for v in self.data.get('vehicles', {}).values())
                net_profit = total_income - total_expense
                vehicle_count = len(self.data.get('vehicles', {}))
                
                report = f"🚌 車隊總體報表\n"
                report += f"---------------------------\n"
                report += f"車輛數量: {vehicle_count}\n"
                report += f"總收入: ${total_income:,.2f}\n"
                report += f"總支出: ${total_expense:,.2f}\n"
                report += f"淨利潤: ${net_profit:,.2f}\n"
                report += f"---------------------------\n"
                
                # 按照淨利潤排序車輛
                sorted_vehicles = sorted(
                    [(vid, v.get('total_income', 0) - v.get('total_expense', 0)) 
                     for vid, v in self.data.get('vehicles', {}).items()],
                    key=lambda x: x[1], reverse=True
                )
                
                # 顯示車輛淨利潤排名
                if sorted_vehicles:
                    report += f"\n車輛淨利潤排名:\n"
                    for i, (vid, profit) in enumerate(sorted_vehicles[:5], 1):
                        vehicle_info = self.data['vehicles'][vid].get('info', '未知')
                        report += f"{i}. {vid} ({vehicle_info}): ${profit:,.2f}\n"
            else:
                # 使用月度摘要數據
                monthly_data = self.data["monthly_summary"][month]
                total_income = monthly_data.get('income', 0)
                total_expense = monthly_data.get('expense', 0)
                net_profit = total_income - total_expense
                vehicle_count = len(monthly_data.get('vehicles', {}))
                
                # 格式化月份為更易讀的格式
                display_month = datetime.datetime.strptime(month, '%Y-%m').strftime('%Y年%m月')
                
                report = f"🚌 {display_month}車隊報表\n"
                report += f"---------------------------\n"
                report += f"車輛數量: {vehicle_count}\n"
                report += f"月度總收入: ${total_income:,.2f}\n"
                report += f"月度總支出: ${total_expense:,.2f}\n"
                report += f"月度淨利潤: ${net_profit:,.2f}\n"
                report += f"---------------------------\n"
                
                # 按照淨利潤排序車輛
                sorted_vehicles = sorted(
                    [(vid, v.get('income', 0) - v.get('expense', 0)) 
                     for vid, v in monthly_data.get('vehicles', {}).items()],
                    key=lambda x: x[1], reverse=True
                )
                
                # 顯示車輛淨利潤排名
                if sorted_vehicles:
                    report += f"\n車輛月度淨利潤排名:\n"
                    for i, (vid, profit) in enumerate(sorted_vehicles[:5], 1):
                        if vid in self.data.get('vehicles', {}):
                            vehicle_info = self.data['vehicles'][vid].get('info', '未知')
                            report += f"{i}. {vid} ({vehicle_info}): ${profit:,.2f}\n"
                        else:
                            report += f"{i}. {vid}: ${profit:,.2f}\n"
            
            report += f"\n最後更新: {self.data.get('last_update', '未知')}"
            
            return report
        except Exception as e:
            self.logger.error(f"獲取車隊摘要報表時發生錯誤：{str(e)}")
            return f"獲取車隊摘要報表時發生錯誤：{str(e)}"
    
    def get_all_vehicles(self):
        """獲取所有車輛的簡要信息"""
        vehicles = []
        for vid, vehicle in self.data.get('vehicles', {}).items():
            vehicles.append({
                'id': vid,
                'info': vehicle.get('info', '未知'),
                'plate_number': vehicle.get('plate_number', ''),
                'driver': vehicle.get('driver', ''),
                'status': vehicle.get('status', 'active'),
                'total_income': vehicle.get('total_income', 0),
                'total_expense': vehicle.get('total_expense', 0),
                'net_profit': vehicle.get('total_income', 0) - vehicle.get('total_expense', 0)
            })
        
        # 按淨利潤排序
        vehicles.sort(key=lambda x: x['net_profit'], reverse=True)
        return vehicles
    
    def set_vehicle_status(self, vehicle_id, status):
        """設定車輛狀態（活躍/維修/閒置/報廢）"""
        try:
            # 格式化車輛ID為大寫
            vehicle_id = vehicle_id.upper().strip()
            
            # 檢查車輛是否存在
            if vehicle_id not in self.data.setdefault("vehicles", {}):
                return False, f"車輛 {vehicle_id} 不存在"
            
            # 有效狀態選項
            valid_statuses = ['active', 'maintenance', 'idle', 'retired']
            status = status.lower()
            
            if status not in valid_statuses:
                return False, f"無效的狀態: {status}。有效選項: {', '.join(valid_statuses)}"
            
            # 更新狀態
            self.data["vehicles"][vehicle_id]["status"] = status
            self.save_data()
            
            # 返回狀態中文名稱
            status_names = {
                'active': '活躍',
                'maintenance': '維修中',
                'idle': '閒置',
                'retired': '報廢'
            }
            
            return True, f"已將車輛 {vehicle_id} 狀態設為：{status_names.get(status, status)}"
        except Exception as e:
            self.logger.error(f"設定車輛狀態時發生錯誤：{str(e)}")
            return False, f"設定車輛狀態時發生錯誤：{str(e)}"
    
    def get_transactions(self, start_date=None, end_date=None, vehicle_id=None, transaction_type=None):
        """獲取交易記錄"""
        try:
            transactions = self.data.get("transactions", [])
            
            # 應用過濾條件
            if start_date:
                transactions = [t for t in transactions if t.get('date', '') >= start_date]
            
            if end_date:
                transactions = [t for t in transactions if t.get('date', '') <= end_date]
            
            if vehicle_id:
                vehicle_id = vehicle_id.upper().strip()
                transactions = [t for t in transactions if t.get('vehicle_id', '') == vehicle_id]
            
            if transaction_type:
                transactions = [t for t in transactions if t.get('type', '') == transaction_type]
            
            # 按日期和時間排序
            transactions.sort(key=lambda x: (x.get('date', ''), x.get('time', '')), reverse=True)
            
            return transactions
        except Exception as e:
            self.logger.error(f"獲取交易記錄時發生錯誤：{str(e)}")
            return [] 