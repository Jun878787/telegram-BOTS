#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

def load_dotenv(env_file='.env'):
    """
    從 .env 文件載入環境變數
    """
    if not os.path.exists(env_file):
        print(f"錯誤: 找不到環境變數文件 {env_file}")
        return False
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            os.environ[key] = value
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        env_file = sys.argv[1]
    else:
        env_file = '.env'
    
    if load_dotenv(env_file):
        print(f"已成功從 {env_file} 載入環境變數")
        
        # 輸出載入的環境變數（隱藏敏感信息）
        for key in os.environ:
            if key.startswith('TELEGRAM'):
                # 隱藏令牌的主要部分
                value = os.environ[key]
                if len(value) > 10:
                    masked_value = value[:8] + "..." + value[-4:]
                else:
                    masked_value = "***"
                print(f"{key}={masked_value}")
            elif key in ['TARGET_GROUP_ID', 'ADMIN_IDS', 'PORT', 'TZ', 'DEBUG']:
                print(f"{key}={os.environ[key]}")
    else:
        print(f"無法載入環境變數文件 {env_file}")
        sys.exit(1) 