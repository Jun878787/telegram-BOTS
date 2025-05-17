#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import datetime
import pytz
import logging

class Config:
    """配置類，管理機器人設定和數據存儲"""
    
    def __init__(self):
        """初始化配置類"""
        self.data_file = "fleet_data.json"
        self.TZ = os.environ.get("TZ", "Asia/Taipei")
        self.timezone = pytz.timezone(self.TZ)
        self.logger = logging.getLogger('ConfigLogger')
        
        # 初始化數據
        self.data = self.load_data()
    
    def load_data(self):
        """從文件加載數據"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"載入數據時發生錯誤：{str(e)}")
        
        # 返回初始數據結構
        return {
            "deposits": [],
            "withdrawals": [],
            "rates": {
                "deposit": 33.0,
                "withdrawal": 32.5
            },
            "operators": [],
            "warnings": {},
            "welcome_message": "👋 歡迎 {SURNAME} 加入 {GROUPNAME}！",
            "farewell_enabled": True,
            "farewell_message": "👋 {SURNAME} 已離開群組，期待再相會！",
            "broadcast_mode": False
        }
    
    def save_data(self):
        """保存數據到文件"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存數據時發生錯誤：{str(e)}")
            return False
    
    def get_transaction_summary(self):
        """獲取交易摘要"""
        deposits = self.data.get("deposits", [])
        withdrawals = self.data.get("withdrawals", [])
        
        total_deposit = sum(deposit["amount"] for deposit in deposits)
        total_withdrawal = sum(withdrawal["amount"] for withdrawal in withdrawals)
        
        return {
            "deposits": deposits,
            "withdrawals": withdrawals,
            "deposit_count": len(deposits),
            "withdrawal_count": len(withdrawals),
            "total_deposit": total_deposit,
            "processed_amount": total_withdrawal,
            "last_update": datetime.datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def add_transaction(self, amount, transaction_type):
        """添加交易記錄"""
        try:
            amount = float(amount)
            current_time = datetime.datetime.now(self.timezone).strftime('%H:%M')
            
            if transaction_type == "deposit":
                # 入款，金額保持為正數
                self.data.setdefault("deposits", []).append({
                    "time": current_time,
                    "amount": amount,
                    "date": datetime.datetime.now(self.timezone).strftime('%Y-%m-%d')
                })
            elif transaction_type == "withdrawal":
                # 出款，金額保存為負數
                self.data.setdefault("withdrawals", []).append({
                    "time": current_time,
                    "amount": -abs(amount),  # 確保為負數
                    "date": datetime.datetime.now(self.timezone).strftime('%Y-%m-%d')
                })
            
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"添加交易記錄時發生錯誤：{str(e)}")
            return False
    
    def clear_today_transactions(self):
        """清空今日交易記錄"""
        try:
            self.data["deposits"] = []
            self.data["withdrawals"] = []
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"清空今日交易記錄時發生錯誤：{str(e)}")
            return False
    
    def clear_all_transactions(self):
        """清空所有交易記錄"""
        return self.clear_today_transactions()
    
    def cancel_last_deposit(self):
        """撤銷最後一筆入款"""
        try:
            if self.data.get("deposits", []):
                self.data["deposits"].pop()
                self.save_data()
                return True
            return False
        except Exception as e:
            self.logger.error(f"撤銷最後一筆入款時發生錯誤：{str(e)}")
            return False
    
    def cancel_last_withdrawal(self):
        """撤銷最後一筆出款"""
        try:
            if self.data.get("withdrawals", []):
                self.data["withdrawals"].pop()
                self.save_data()
                return True
            return False
        except Exception as e:
            self.logger.error(f"撤銷最後一筆出款時發生錯誤：{str(e)}")
            return False
    
    def get_rates(self):
        """獲取匯率設定"""
        return self.data.get("rates", {"deposit": 33.0, "withdrawal": 32.5})
    
    def set_deposit_rate(self, rate):
        """設定入款匯率"""
        try:
            self.data.setdefault("rates", {})["deposit"] = float(rate)
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"設定入款匯率時發生錯誤：{str(e)}")
            return False
    
    def set_withdrawal_rate(self, rate):
        """設定出款匯率"""
        try:
            self.data.setdefault("rates", {})["withdrawal"] = float(rate)
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"設定出款匯率時發生錯誤：{str(e)}")
            return False
    
    def get_operators(self):
        """獲取操作員列表"""
        return self.data.get("operators", [])
    
    def add_operator(self, user_id):
        """添加操作員"""
        try:
            if user_id not in self.data.setdefault("operators", []):
                self.data["operators"].append(user_id)
                self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"添加操作員時發生錯誤：{str(e)}")
            return False
    
    def remove_operator(self, user_id):
        """移除操作員"""
        try:
            if user_id in self.data.setdefault("operators", []):
                self.data["operators"].remove(user_id)
                self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"移除操作員時發生錯誤：{str(e)}")
            return False
    
    def is_operator(self, user_id):
        """檢查用戶是否為操作員"""
        return user_id in self.data.get("operators", [])
    
    def add_warning(self, user_id):
        """增加用戶警告次數"""
        try:
            user_id = str(user_id)  # 確保ID為字串
            warnings = self.data.setdefault("warnings", {})
            warnings[user_id] = warnings.get(user_id, 0) + 1
            self.save_data()
            return warnings[user_id]
        except Exception as e:
            self.logger.error(f"添加警告時發生錯誤：{str(e)}")
            return 0
    
    def remove_warning(self, user_id):
        """減少用戶警告次數"""
        try:
            user_id = str(user_id)
            warnings = self.data.setdefault("warnings", {})
            if user_id in warnings and warnings[user_id] > 0:
                warnings[user_id] -= 1
                self.save_data()
            return warnings.get(user_id, 0)
        except Exception as e:
            self.logger.error(f"移除警告時發生錯誤：{str(e)}")
            return 0
    
    def get_warnings(self, user_id):
        """獲取用戶警告次數"""
        user_id = str(user_id)
        return self.data.get("warnings", {}).get(user_id, 0)
    
    def clear_warnings(self, user_id):
        """清空用戶警告次數"""
        try:
            user_id = str(user_id)
            warnings = self.data.setdefault("warnings", {})
            if user_id in warnings:
                warnings[user_id] = 0
                self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"清空警告時發生錯誤：{str(e)}")
            return False
    
    def set_welcome_message(self, message):
        """設定歡迎詞"""
        try:
            self.data["welcome_message"] = message
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"設定歡迎詞時發生錯誤：{str(e)}")
            return False
    
    def get_welcome_message(self):
        """獲取歡迎詞"""
        return self.data.get("welcome_message", "👋 歡迎 {SURNAME} 加入 {GROUPNAME}！")
    
    def set_farewell_enabled(self, enabled):
        """設定是否啟用告別訊息"""
        try:
            self.data["farewell_enabled"] = bool(enabled)
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"設定告別訊息啟用狀態時發生錯誤：{str(e)}")
            return False
    
    def get_farewell_enabled(self):
        """獲取告別訊息啟用狀態"""
        return self.data.get("farewell_enabled", True)
    
    def set_farewell_message(self, message):
        """設定告別詞"""
        try:
            self.data["farewell_message"] = message
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"設定告別詞時發生錯誤：{str(e)}")
            return False
    
    def get_farewell_message(self):
        """獲取告別詞"""
        return self.data.get("farewell_message", "👋 {SURNAME} 已離開群組，期待再相會！")
    
    def set_broadcast_mode(self, enabled):
        """設定群發廣播模式"""
        try:
            self.data["broadcast_mode"] = bool(enabled)
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"設定群發廣播模式時發生錯誤：{str(e)}")
            return False
    
    def get_broadcast_mode(self):
        """獲取群發廣播模式狀態"""
        return self.data.get("broadcast_mode", False) 