#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORS 測試腳本
"""

import requests

def test_cors():
    """測試 CORS 標頭"""
    base_url = "http://localhost:5000"
    
    print("=== CORS 測試 ===\n")
    
    # 測試 1: 基本請求
    print("測試 1: 基本請求")
    try:
        response = requests.get(f"{base_url}/api/session/check")
        print(f"狀態碼: {response.status_code}")
        print("CORS 標頭:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        print()
    except Exception as e:
        print(f"錯誤: {e}\n")
    
    # 測試 2: 帶 Origin 標頭
    print("測試 2: 帶 Origin 標頭")
    try:
        headers = {'Origin': 'http://localhost:3000'}
        response = requests.get(f"{base_url}/api/session/check", headers=headers)
        print(f"狀態碼: {response.status_code}")
        print("CORS 標頭:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        print()
    except Exception as e:
        print(f"錯誤: {e}\n")
    
    # 測試 3: OPTIONS 預檢請求
    print("測試 3: OPTIONS 預檢請求")
    try:
        headers = {'Origin': 'http://localhost:3000'}
        response = requests.options(f"{base_url}/api/session/check", headers=headers)
        print(f"狀態碼: {response.status_code}")
        print("CORS 標頭:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        print()
    except Exception as e:
        print(f"錯誤: {e}\n")
    
    # 測試 4: Origin 為 null
    print("測試 4: Origin 為 null")
    try:
        headers = {'Origin': 'null'}
        response = requests.get(f"{base_url}/api/session/check", headers=headers)
        print(f"狀態碼: {response.status_code}")
        print("CORS 標頭:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        print()
    except Exception as e:
        print(f"錯誤: {e}\n")

if __name__ == "__main__":
    test_cors() 