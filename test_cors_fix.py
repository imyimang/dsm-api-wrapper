#!/usr/bin/env python3
"""
🔧 跨域 Cookie 修復驗證測試
專門測試 SameSite=None 和 CORS credentials 修復效果
"""

import requests
import json
import time

def test_cors_cookie_fix():
    """測試跨域 Cookie 修復效果"""
    print("🚀 測試跨域 Cookie 修復效果")
    print("=" * 50)
    
    base_url = 'http://localhost:5000'
    
    # 🧪 測試 1: 檢查修復後的 Cookie 設置
    print("\n1. 🍪 測試 Cookie 設置...")
    session = requests.Session()
    
    # 模擬跨域請求 (設置 Origin header)
    headers = {
        'Origin': 'http://localhost:3000',
        'Content-Type': 'application/json'
    }
    
    try:
        # 登入並檢查 Set-Cookie header
        login_response = session.post(f'{base_url}/api/login', 
                                    json={'account': 'cbs34', 'password': '757713@Info'},
                                    headers=headers)
        
        if login_response.status_code == 200:
            print("   ✅ 登入成功")
            
            # 檢查 Set-Cookie header
            set_cookies = login_response.headers.get('Set-Cookie', '')
            print(f"   📋 Set-Cookie header: {set_cookies[:100]}...")
            
            # 檢查是否包含 SameSite=None
            if 'SameSite=None' in set_cookies:
                print("   🎉 SameSite=None 設置成功！")
            else:
                print("   ⚠️ 未找到 SameSite=None")
            
            # 檢查 CORS headers
            cors_origin = login_response.headers.get('Access-Control-Allow-Origin')
            cors_creds = login_response.headers.get('Access-Control-Allow-Credentials')
            
            print(f"   🌐 CORS Origin: {cors_origin}")
            print(f"   🔐 CORS Credentials: {cors_creds}")
            
            if cors_origin == 'http://localhost:3000' and cors_creds == 'true':
                print("   🎉 CORS 設置正確！")
            else:
                print("   ❌ CORS 設置有問題")
                
        else:
            print(f"   ❌ 登入失敗: {login_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 測試 1 錯誤: {e}")
    
    # 🧪 測試 2: 模擬瀏覽器跨域 Session 檢查
    print("\n2. 🌐 測試跨域 Session 檢查...")
    try:
        # 使用新的 session 模擬跨域請求
        cross_origin_session = requests.Session()
        
        # 先登入
        login_resp = cross_origin_session.post(f'{base_url}/api/login',
                                             json={'account': 'cbs34', 'password': '757713@Info'},
                                             headers=headers)
        
        if login_resp.status_code == 200:
            # 等待一下讓 session 設置生效
            time.sleep(0.5)
            
            # 檢查 session
            check_resp = cross_origin_session.get(f'{base_url}/api/session/check',
                                                headers=headers)
            
            print(f"   📊 Session 檢查狀態: {check_resp.status_code}")
            
            if check_resp.status_code == 200:
                result = check_resp.json()
                if result.get('success'):
                    print("   🎉 跨域 Session 檢查成功！")
                    print(f"   📋 Session 有效: {result['data']['valid']}")
                else:
                    print("   ❌ Session 檢查失敗")
            else:
                print(f"   ❌ Session 檢查 HTTP 錯誤: {check_resp.status_code}")
                
        else:
            print(f"   ❌ 登入失敗: {login_resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ 測試 2 錯誤: {e}")
    
    # 🧪 測試 3: 測試 debug 端點
    print("\n3. 🔍 測試除錯端點...")
    try:
        debug_resp = session.get(f'{base_url}/api/debug/session', headers=headers)
        
        if debug_resp.status_code == 200:
            result = debug_resp.json()
            debug_info = result.get('debug_info', {})
            
            print(f"   📊 Flask Session 存在: {debug_info.get('flask_session_exists')}")
            print(f"   📋 Session 鍵: {debug_info.get('flask_session_keys', [])}")
            
            if debug_info.get('flask_session_exists'):
                print("   🎉 Flask Session 正常運作！")
            else:
                print("   ❌ Flask Session 仍有問題")
        else:
            print(f"   ❌ Debug 端點錯誤: {debug_resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ 測試 3 錯誤: {e}")
    
    # 🧪 測試 4: 測試 null origin (模擬 file:// 協議)
    print("\n4. 📄 測試 null origin (file:// 協議)...")
    try:
        null_headers = {
            'Origin': 'null',  # 模擬 file:// 協議
            'Content-Type': 'application/json'
        }
        
        null_session = requests.Session()
        login_resp = null_session.post(f'{base_url}/api/login',
                                     json={'account': 'cbs34', 'password': '757713@Info'},
                                     headers=null_headers)
        
        if login_resp.status_code == 200:
            cors_origin = login_resp.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 Null Origin 回應: {cors_origin}")
            
            if cors_origin == 'null':
                print("   🎉 Null origin 處理正確！")
            else:
                print("   ⚠️ Null origin 處理可能有問題")
        else:
            print(f"   ❌ Null origin 測試失敗: {login_resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ 測試 4 錯誤: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 跨域 Cookie 修復測試完成！")
    print("\n💡 如果測試通過，請在瀏覽器中重新測試：")
    print("   1. 清除瀏覽器 cookies")
    print("   2. 重新載入前端應用")
    print("   3. 嘗試登入和 session 檢查")

if __name__ == "__main__":
    test_cors_cookie_fix() 