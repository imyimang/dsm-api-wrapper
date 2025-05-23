#!/usr/bin/env python3
"""
簡單的修復驗證測試
"""

import requests
import json

def test_fixes():
    """測試修復效果"""
    print("🔧 測試 Flask Session 和 Token 修復")
    print("=" * 40)
    
    session = requests.Session()
    base_url = 'http://localhost:5000'
    
    # 1. 測試 session 基本功能
    print("\n1. 測試 Session 功能...")
    try:
        test_response = session.post(f'{base_url}/api/debug/session/test')
        if test_response.status_code == 200:
            result = test_response.json()
            print(f"   ✅ Session 測試: {result['debug_info']['verification_success']}")
            print(f"   Session 鍵: {result['debug_info']['session_keys']}")
        else:
            print(f"   ❌ Session 測試失敗: {test_response.status_code}")
    except Exception as e:
        print(f"   ❌ Session 測試錯誤: {e}")
    
    # 2. 測試 Cookie 登入
    print("\n2. 測試 Cookie 登入...")
    try:
        login_response = session.post(f'{base_url}/api/login', json={
            'account': 'cbs34',
            'password': '757713@Info'
        })
        
        if login_response.status_code == 200:
            print("   ✅ Cookie 登入成功")
            # 檢查 session
            debug_response = session.get(f'{base_url}/api/debug/session')
            if debug_response.status_code == 200:
                debug_result = debug_response.json()
                session_exists = debug_result['debug_info']['flask_session_exists']
                print(f"   Flask Session 存在: {session_exists}")
                if session_exists:
                    print("   🎉 Flask Session 修復成功!")
                else:
                    print("   ❌ Flask Session 仍有問題")
        else:
            print(f"   ❌ Cookie 登入失敗: {login_response.status_code}")
    except Exception as e:
        print(f"   ❌ Cookie 登入錯誤: {e}")
    
    # 3. 測試 Token 登入
    print("\n3. 測試 Token 登入...")
    try:
        token_response = requests.post(f'{base_url}/api/login/token', json={
            'account': 'cbs34',
            'password': '757713@Info'
        })
        
        if token_response.status_code == 200:
            result = token_response.json()
            token = result['data']['token']
            print("   ✅ Token 登入成功")
            print(f"   Token: {token[:16]}...")
            
            # 測試 token session 檢查
            check_response = requests.get(f'{base_url}/api/session/check/token', 
                                        headers={'Authorization': f'Bearer {token}'})
            if check_response.status_code == 200:
                print("   ✅ Token Session 檢查成功")
            else:
                print(f"   ❌ Token Session 檢查失敗: {check_response.status_code}")
        else:
            print(f"   ❌ Token 登入失敗: {token_response.status_code}")
            print(f"   錯誤: {token_response.text}")
    except Exception as e:
        print(f"   ❌ Token 登入錯誤: {e}")
    
    print("\n" + "=" * 40)
    print("✅ 測試完成！")

if __name__ == "__main__":
    test_fixes() 