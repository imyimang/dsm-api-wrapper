#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synology NAS Flask API 測試腳本
"""

import requests
import json
import time

class NASApiTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_api_docs(self):
        """測試API文檔端點"""
        print("🧪 測試API文檔...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API文檔獲取成功: {data['title']}")
                return True
            else:
                print(f"❌ API文檔獲取失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API文檔測試錯誤: {e}")
            return False
    
    def test_login(self, account=None, password=None):
        """測試登入功能"""
        print("🧪 測試登入功能...")
        
        # 使用測試帳號或提示輸入
        if not account:
            account = input("請輸入NAS帳號: ")
        if not password:
            password = input("請輸入NAS密碼: ")
        
        try:
            login_data = {
                "account": account,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 登入成功: {data['message']}")
                    print(f"   SID: {data['data']['sid']}")
                    print(f"   登入時間: {data['data']['login_time']}")
                    return True
                else:
                    print(f"❌ 登入失敗: {data.get('message')}")
                    return False
            else:
                print(f"❌ 登入請求失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 登入測試錯誤: {e}")
            return False
    
    def test_session_check(self):
        """測試session檢查"""
        print("🧪 測試session檢查...")
        try:
            response = self.session.get(f"{self.base_url}/api/session/check")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Session有效: {data['message']}")
                    if "data" in data:
                        print(f"   登入時間: {data['data']['login_time']}")
                        print(f"   已登入時間: {data['data']['elapsed_hours']} 小時")
                    return True
                else:
                    print(f"❌ Session無效: {data.get('message')}")
                    return False
            else:
                print(f"❌ Session檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Session檢查錯誤: {e}")
            return False
    
    def test_list_files(self, path="/home/www"):
        """測試檔案列表功能"""
        print(f"🧪 測試檔案列表 (路徑: {path})...")
        try:
            response = self.session.get(
                f"{self.base_url}/api/files",
                params={"path": path}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    files_data = data["data"]
                    total_files = len(files_data.get("files", []))
                    print(f"✅ 檔案列表獲取成功: 共 {total_files} 個項目")
                    
                    # 顯示前5個檔案資訊
                    for i, file_info in enumerate(files_data.get("files", [])[:5]):
                        file_type = "📁" if file_info.get("isdir") else "📄"
                        print(f"   {file_type} {file_info.get('name')}")
                    
                    if total_files > 5:
                        print(f"   ... 還有 {total_files - 5} 個項目")
                    
                    return True
                else:
                    print(f"❌ 檔案列表獲取失敗: {data.get('message')}")
                    return False
            else:
                print(f"❌ 檔案列表請求失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 檔案列表測試錯誤: {e}")
            return False
    
    def test_background_tasks(self):
        """測試後台任務列表"""
        print("🧪 測試後台任務列表...")
        try:
            response = self.session.get(f"{self.base_url}/api/tasks")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tasks = data["data"].get("tasks", [])
                    print(f"✅ 後台任務列表獲取成功: 共 {len(tasks)} 個任務")
                    
                    if tasks:
                        for task in tasks[:3]:  # 顯示前3個任務
                            print(f"   📋 任務: {task.get('name', 'Unknown')}")
                    else:
                        print("   🔍 目前沒有執行中的任務")
                    
                    return True
                else:
                    print(f"❌ 後台任務列表獲取失敗: {data.get('message')}")
                    return False
            else:
                print(f"❌ 後台任務請求失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 後台任務測試錯誤: {e}")
            return False
    
    def test_debug_toggle(self):
        """測試debug模式切換"""
        print("🧪 測試debug模式切換...")
        try:
            response = self.session.post(f"{self.base_url}/api/debug/toggle")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    debug_mode = data.get("debug_mode")
                    print(f"✅ Debug模式切換成功: {data['message']}")
                    print(f"   當前debug模式: {'開啟' if debug_mode else '關閉'}")
                    return True
                else:
                    print(f"❌ Debug模式切換失敗: {data.get('message')}")
                    return False
            else:
                print(f"❌ Debug切換請求失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Debug切換測試錯誤: {e}")
            return False
    
    def test_logout(self):
        """測試登出功能"""
        print("🧪 測試登出功能...")
        try:
            response = self.session.post(f"{self.base_url}/api/logout")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 登出成功: {data['message']}")
                    return True
                else:
                    print(f"❌ 登出失敗: {data.get('message')}")
                    return False
            else:
                print(f"❌ 登出請求失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 登出測試錯誤: {e}")
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        print("🎯 開始執行 NAS API 測試套件")
        print("=" * 50)
        
        results = []
        
        # 1. 測試API文檔
        results.append(("API文檔", self.test_api_docs()))
        
        # 2. 測試登入
        results.append(("登入功能", self.test_login()))
        
        # 3. 如果登入成功，繼續測試其他功能
        if results[-1][1]:  # 如果登入成功
            results.append(("Session檢查", self.test_session_check()))
            results.append(("檔案列表", self.test_list_files()))
            results.append(("後台任務", self.test_background_tasks()))
            results.append(("Debug切換", self.test_debug_toggle()))
            results.append(("登出功能", self.test_logout()))
        
        # 顯示測試結果摘要
        print("\n" + "=" * 50)
        print("📊 測試結果摘要:")
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📈 總結: {passed} 通過, {failed} 失敗")
        
        if failed == 0:
            print("🎉 所有測試都通過了！API服務器運作正常。")
        else:
            print("⚠️ 有部分測試失敗，請檢查服務器狀態和網路連線。")
        
        return failed == 0

def main():
    print("🧪 Synology NAS Flask API 測試工具")
    print("確保API服務器正在 http://localhost:5000 上運行")
    print("-" * 50)
    
    # 檢查服務器是否運行
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code != 200:
            print("❌ 無法連接到API服務器，請確認服務器是否正在運行")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到API服務器，請先啟動服務器:")
        print("   python app.py")
        return
    except Exception as e:
        print(f"❌ 連接錯誤: {e}")
        return
    
    tester = NASApiTester()
    
    print("選擇測試模式:")
    print("1. 執行完整測試套件")
    print("2. 僅測試API文檔")
    print("3. 自定義測試")
    
    choice = input("\n請選擇 (1-3): ").strip()
    
    if choice == "1":
        tester.run_all_tests()
    elif choice == "2":
        tester.test_api_docs()
    elif choice == "3":
        print("\n可用的測試:")
        print("1. API文檔")
        print("2. 登入功能")
        print("3. Session檢查")
        print("4. 檔案列表")
        print("5. 後台任務")
        print("6. Debug切換")
        print("7. 登出功能")
        
        test_choice = input("請選擇測試編號: ").strip()
        
        test_methods = {
            "1": tester.test_api_docs,
            "2": tester.test_login,
            "3": tester.test_session_check,
            "4": tester.test_list_files,
            "5": tester.test_background_tasks,
            "6": tester.test_debug_toggle,
            "7": tester.test_logout
        }
        
        if test_choice in test_methods:
            test_methods[test_choice]()
        else:
            print("❌ 無效的選擇")
    else:
        print("❌ 無效的選擇")

if __name__ == "__main__":
    main() 