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
    
    def test_create_folder(self, parent_path=None, folder_name=None):
        """測試建立資料夾功能"""
        print("🧪 測試建立資料夾功能...")
        
        # 檢查是否登入 (隱含地，如果 session 無效，後端 API 會拒絕)
        # 為了更明確，可以先調用 self.test_session_check() 或確保在登入後執行此測試

        if not parent_path:
            parent_path = input(f"請輸入父路徑 (預設: /home/www): ") or "/home/www"
        if not folder_name:
            folder_name = input(f"請輸入新資料夾名稱 (例如: test_folder_{int(time.time())}): ")
            if not folder_name:
                print("❌ 未輸入資料夾名稱，測試中止")
                return False
        
        print(f"   嘗試在 '{parent_path}' 下建立資料夾 '{folder_name}'")

        try:
            create_folder_data = {
                "parent_path": parent_path,
                "folder_name": folder_name,
                "force_parent": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/folder",
                json=create_folder_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 建立資料夾成功: {data.get('message')}")
                    # 如果 API 回應中有新資料夾的詳細資訊，可以在這裡印出
                    # print(f"   詳細資料: {data.get('data')}")
                    return True
                else:
                    print(f"❌ 建立資料夾失敗: {data.get('message')}")
                    return False
            elif response.status_code == 401: # 未登入的情況
                print(f"❌ 建立資料夾失敗: 未登入或 Session 無效 (狀態碼: {response.status_code})")
                print(f"   請先執行登入測試。")
                return False
            else:
                print(f"❌ 建立資料夾請求失敗: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   錯誤訊息: {error_data.get('message')}")
                except json.JSONDecodeError:
                    print("   無法解析錯誤回應")
                return False
        except Exception as e:
            print(f"❌ 建立資料夾測試錯誤: {e}")
            return False
    
    def test_share_file(self, file_paths=None, with_password=False, with_expiry=False):
        """測試檔案分享功能 (包含 QR Code)"""
        print("🧪 測試檔案分享功能...")
        
        if not file_paths:
            # 先獲取檔案列表來選擇要分享的檔案
            print("   獲取可用檔案列表...")
            files_response = self.session.get(f"{self.base_url}/api/files?path=/home/www")
            
            if files_response.status_code == 200:
                files_data = files_response.json()
                if files_data.get("success"):
                    files = files_data["data"].get("files", [])
                    available_files = [f for f in files if not f.get("isdir")]  # 只顯示檔案，不顯示資料夾
                    
                    if available_files:
                        print("   可用的檔案:")
                        for i, file_info in enumerate(available_files[:5]):
                            print(f"     {i+1}. {file_info.get('name')}")
                        
                        # 使用第一個檔案作為測試
                        test_file = available_files[0]["name"]
                        file_paths = [f"/home/www/{test_file}"]
                        print(f"   自動選擇測試檔案: {test_file}")
                    else:
                        print("❌ 目錄中沒有可用的檔案進行分享測試")
                        return False
                else:
                    print(f"❌ 無法獲取檔案列表: {files_data.get('message')}")
                    return False
            else:
                print("❌ 無法連接到檔案列表 API")
                return False
        
        try:
            share_data = {
                "paths": file_paths
            }
            
            # 添加可選參數
            if with_password:
                share_data["password"] = "test123"
                print("   🔒 使用密碼保護: test123")
            
            if with_expiry:
                # 設定30天後過期
                from datetime import datetime, timedelta
                expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                share_data["date_expired"] = expiry_date
                print(f"   ⏰ 設定過期時間: {expiry_date}")
            
            print(f"   📤 嘗試分享檔案: {file_paths}")
            
            response = self.session.post(
                f"{self.base_url}/api/share",
                json=share_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 檔案分享成功: {data.get('message')}")
                    
                    # 分析分享數據
                    share_info = data.get("data", {})
                    links = share_info.get("links", [])
                    
                    if links:
                        for i, link in enumerate(links):
                            print(f"   📋 分享連結 {i+1}:")
                            print(f"      🔗 URL: {link.get('url', 'N/A')}")
                            print(f"      🆔 ID: {link.get('id', 'N/A')}")
                            print(f"      📄 檔案名: {link.get('name', 'N/A')}")
                            print(f"      📅 過期時間: {link.get('date_expired', '無限期')}")
                            print(f"      🔐 密碼保護: {'是' if link.get('has_password') else '否'}")
                            print(f"      📊 狀態: {link.get('status', 'N/A')}")
                            
                            # 檢查 QR Code
                            qr_code = link.get('qrcode')
                            if qr_code:
                                if qr_code.startswith('data:image/png;base64,'):
                                    # 計算 base64 長度來確認 QR Code 存在
                                    base64_part = qr_code.split(',')[1] if ',' in qr_code else ''
                                    qr_size = len(base64_part)
                                    print(f"      📱 QR Code: ✅ 已生成 (大小: {qr_size} 字元)")
                                    
                                    # 可選：儲存 QR Code 到檔案 (用於調試)
                                    if input("   是否要儲存 QR Code 到檔案? (y/N): ").lower() == 'y':
                                        try:
                                            import base64
                                            qr_filename = f"qr_code_{link.get('id', 'unknown')}.png"
                                            qr_binary = base64.b64decode(base64_part)
                                            with open(qr_filename, 'wb') as f:
                                                f.write(qr_binary)
                                            print(f"      💾 QR Code 已儲存至: {qr_filename}")
                                        except Exception as e:
                                            print(f"      ❌ QR Code 儲存失敗: {e}")
                                else:
                                    print(f"      📱 QR Code: ⚠️ 格式異常: {qr_code[:50]}...")
                            else:
                                print(f"      📱 QR Code: ❌ 未提供")
                            
                            print()  # 空行分隔
                        
                        print(f"   📊 總計分享連結數量: {len(links)}")
                        return True
                    else:
                        print("❌ 分享成功但沒有返回連結資訊")
                        return False
                else:
                    print(f"❌ 檔案分享失敗: {data.get('message')}")
                    return False
            elif response.status_code == 401:
                print(f"❌ 檔案分享失敗: 未登入或 Session 無效")
                return False
            else:
                print(f"❌ 檔案分享請求失敗: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   錯誤訊息: {error_data.get('message')}")
                except json.JSONDecodeError:
                    print("   無法解析錯誤回應")
                return False
        except Exception as e:
            print(f"❌ 檔案分享測試錯誤: {e}")
            return False
    
    def test_share_multiple_files(self):
        """測試多檔案分享功能"""
        print("🧪 測試多檔案分享功能...")
        
        try:
            # 獲取檔案列表
            files_response = self.session.get(f"{self.base_url}/api/files?path=/home/www")
            
            if files_response.status_code == 200:
                files_data = files_response.json()
                if files_data.get("success"):
                    files = files_data["data"].get("files", [])
                    available_files = [f for f in files if not f.get("isdir")]
                    
                    if len(available_files) >= 2:
                        # 選擇前兩個檔案進行測試
                        test_files = [f"/home/www/{f['name']}" for f in available_files[:2]]
                        print(f"   選擇測試檔案: {[f.split('/')[-1] for f in test_files]}")
                        
                        return self.test_share_file(
                            file_paths=test_files,
                            with_password=True,
                            with_expiry=True
                        )
                    else:
                        print("❌ 沒有足夠的檔案進行多檔案分享測試 (需要至少2個檔案)")
                        return False
                else:
                    print(f"❌ 無法獲取檔案列表: {files_data.get('message')}")
                    return False
            else:
                print("❌ 無法連接到檔案列表 API")
                return False
        except Exception as e:
            print(f"❌ 多檔案分享測試錯誤: {e}")
            return False
    
    def test_share_folder(self):
        """測試資料夾分享功能"""
        print("🧪 測試資料夾分享功能...")
        
        try:
            # 獲取檔案列表尋找資料夾
            files_response = self.session.get(f"{self.base_url}/api/files?path=/home/www")
            
            if files_response.status_code == 200:
                files_data = files_response.json()
                if files_data.get("success"):
                    files = files_data["data"].get("files", [])
                    available_folders = [f for f in files if f.get("isdir")]
                    
                    if available_folders:
                        # 選擇第一個資料夾進行測試
                        test_folder = available_folders[0]["name"]
                        folder_path = f"/home/www/{test_folder}"
                        print(f"   選擇測試資料夾: {test_folder}")
                        
                        return self.test_share_file(
                            file_paths=[folder_path],
                            with_password=False,
                            with_expiry=False
                        )
                    else:
                        print("❌ 目錄中沒有可用的資料夾進行分享測試")
                        return False
                else:
                    print(f"❌ 無法獲取檔案列表: {files_data.get('message')}")
                    return False
            else:
                print("❌ 無法連接到檔案列表 API")
                return False
        except Exception as e:
            print(f"❌ 資料夾分享測試錯誤: {e}")
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
            # 為了避免自動測試時產生過多垃圾資料夾，可以考慮預設路徑和隨機名稱
            default_test_folder_name = f"autotest_folder_{int(time.time()) % 1000}"
            results.append(("建立資料夾", self.test_create_folder(parent_path="/home/www", folder_name=default_test_folder_name)))
            # 新增分享測試
            results.append(("檔案分享", self.test_share_file()))
            results.append(("多檔案分享", self.test_share_multiple_files()))
            results.append(("資料夾分享", self.test_share_folder()))
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
    print("4. 僅測試分享功能")
    
    choice = input("\n請選擇 (1-4): ").strip()
    
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
        print("8. 建立資料夾")
        print("9. 檔案分享")
        print("10. 多檔案分享")
        print("11. 資料夾分享")
        
        test_choice = input("請選擇測試編號: ").strip()
        
        test_methods = {
            "1": tester.test_api_docs,
            "2": tester.test_login,
            "3": tester.test_session_check,
            "4": tester.test_list_files,
            "5": tester.test_background_tasks,
            "6": tester.test_debug_toggle,
            "7": tester.test_logout,
            "8": tester.test_create_folder,
            "9": tester.test_share_file,
            "10": tester.test_share_multiple_files,
            "11": tester.test_share_folder
        }
        
        if test_choice in test_methods:
            # 對於分享測試，先確保已登入
            if test_choice in ["9", "10", "11"]:
                print("分享測試需要先登入...")
                if tester.test_login():
                    test_methods[test_choice]()
                else:
                    print("❌ 登入失敗，無法執行分享測試")
            else:
                test_methods[test_choice]()
        else:
            print("❌ 無效的選擇")
    elif choice == "4":
        print("🧪 執行分享功能測試套件...")
        if tester.test_login():
            print("\n" + "-" * 30)
            tester.test_share_file()
            print("\n" + "-" * 30)
            tester.test_share_multiple_files()
            print("\n" + "-" * 30)
            tester.test_share_folder()
        else:
            print("❌ 登入失敗，無法執行分享測試")
    else:
        print("❌ 無效的選擇")

if __name__ == "__main__":
    main()