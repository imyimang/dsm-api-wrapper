import requests
import json
import time
import os
from datetime import datetime, timedelta
from io import BytesIO

class SimpleNASApiTester:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.base_url = self.get_base_url()
        self.session = requests.Session()
        self.login_credentials = None
        
        print(f"📋 配置信息:")
        print(f"   伺服器地址: {self.base_url}")
        print(f"   NAS 地址: {self.config['NAS']['NAS_BASE_URL']}")
        print(f"   Session 檔案: {self.config['SESSION']['SESSION_FILE']}")
        print(f"   Session 過期天數: {self.config['SESSION']['SESSION_EXPIRE_DAYS']}")
        
    def load_config(self):
        """載入配置檔案"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 驗證必要的配置項目
            required_keys = {
                'NAS': ['NAS_BASE_URL', 'NAS_TIMEOUT'],
                'SESSION': ['SESSION_FILE', 'SESSION_EXPIRE_DAYS'],
                'FLASK': ['HOST', 'PORT', 'DEBUG']
            }
            
            for section, keys in required_keys.items():
                if section not in config:
                    raise ValueError(f"配置檔案缺少 {section} 段落")
                for key in keys:
                    if key not in config[section]:
                        raise ValueError(f"配置檔案 {section} 段落缺少 {key}")
            
            print(f"✅ 成功載入配置檔案: {self.config_file}")
            return config
            
        except FileNotFoundError:
            print(f"❌ 找不到配置檔案: {self.config_file}")
            print("請確認 config.json 檔案存在於當前目錄")
            exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 配置檔案格式錯誤: {e}")
            print("請檢查 config.json 檔案的 JSON 格式")
            exit(1)
        except ValueError as e:
            print(f"❌ 配置檔案內容錯誤: {e}")
            exit(1)
    
    def get_base_url(self):
        """根據配置生成基礎 URL"""
        host = self.config['FLASK']['HOST']
        port = self.config['FLASK']['PORT']
        
        # 如果 HOST 是 0.0.0.0，則使用 localhost 進行測試
        if host == "0.0.0.0":
            host = "localhost"
        elif host == "127.0.0.1":
            host = "localhost"
        
        return f"http://{host}:{port}"
    
    def log_test(self, test_name, status, message="", data=None):
        """統一的測試日誌格式"""
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {test_name: <20}: {message}")
        if data and isinstance(data, dict):
            print(f"   詳細: {json.dumps(data, indent=4, ensure_ascii=False)}")
        elif data:
            print(f"   詳細: {data}")
    
    def check_server_connection(self):
        """檢查服務器連線"""
        print("🔗 檢查服務器連線...")
        try:
            timeout = self.config['NAS']['NAS_TIMEOUT']
            response = self.session.get(f"{self.base_url}/", timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "服務器連線", 
                    True, 
                    f"連線成功 - {data.get('title', 'SimpleNAS API')}"
                )
                return True
            else:
                self.log_test("服務器連線", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test(
                "服務器連線", 
                False, 
                f"無法連接到服務器，請確認服務器是否運行在 {self.base_url}"
            )
            return False
        except Exception as e:
            self.log_test("服務器連線", False, f"連線錯誤: {str(e)}")
            return False

    def test_health_check(self):
        """測試 GET /health - 健康檢查"""
        print("\n🧪 測試健康檢查...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test(
                        "健康檢查", 
                        True, 
                        f"系統健康 - 版本: {data.get('version', 'Unknown')}"
                    )
                    
                    # 檢查系統檢查項目
                    system_checks = data.get("system_checks", {})
                    session_stats = data.get("session_stats", {})
                    
                    print(f"   📊 系統狀態:")
                    print(f"      配置檔案: {system_checks.get('config_file', 'Unknown')}")
                    print(f"      Session 檔案: {system_checks.get('session_file', 'Unknown')}")
                    print(f"      NAS 地址: {system_checks.get('nas_base_url', 'Unknown')}")
                    print(f"      Session 過期天數: {system_checks.get('session_expire_days', 'Unknown')}")
                    
                    print(f"   📈 Session 統計:")
                    print(f"      總 Sessions: {session_stats.get('total_sessions', 0)}")
                    print(f"      活躍 Sessions: {session_stats.get('active_sessions', 0)}")
                    print(f"      過期 Sessions: {session_stats.get('expired_sessions', 0)}")
                    
                    return True
                else:
                    self.log_test("健康檢查", False, f"系統狀態: {data.get('status', 'Unknown')}")
                    if 'error' in data:
                        print(f"   錯誤: {data['error']}")
                    return False
            else:
                self.log_test("健康檢查", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康檢查", False, f"錯誤: {str(e)}")
            return False

    # ============= 身份驗證測試 =============
    
    def test_api_docs(self):
        """測試 GET / - API 文檔首頁"""
        print("\n🧪 測試 API 文檔首頁...")
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["title", "description", "version", "endpoints"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test(
                        "API 文檔結構", 
                        False, 
                        f"缺少必要欄位: {missing_fields}"
                    )
                    return False
                
                # 驗證配置資訊是否正確
                system_info = data.get('system_info', {})
                expected_session_file = self.config['SESSION']['SESSION_FILE']
                expected_expire_days = self.config['SESSION']['SESSION_EXPIRE_DAYS']
                
                if (system_info.get('session_file') == expected_session_file and 
                    system_info.get('session_expire_days') == expected_expire_days):
                    config_match = True
                else:
                    config_match = False
                    print(f"   ⚠️ 配置不匹配:")
                    print(f"      期望 Session 檔案: {expected_session_file}")
                    print(f"      實際 Session 檔案: {system_info.get('session_file')}")
                    print(f"      期望過期天數: {expected_expire_days}")
                    print(f"      實際過期天數: {system_info.get('session_expire_days')}")
                
                self.log_test(
                    "API 文檔", 
                    True, 
                    f"{data['title']} v{data['version']} {'(配置匹配)' if config_match else '(配置不匹配)'}"
                )
                return True
            else:
                self.log_test("API 文檔", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API 文檔", False, f"錯誤: {str(e)}")
            return False
    
    def test_login_invalid(self):
        """測試 POST /api/login - 無效登入"""
        print("\n🧪 測試無效登入...")
        
        # 測試1: 缺少帳號密碼
        try:
            response = self.session.post(
                f"{self.base_url}/api/login",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 400:
                data = response.json()
                if not data.get("success") and "帳號和密碼" in data.get("error", ""):
                    self.log_test("缺少帳號密碼", True, "正確返回 400 錯誤")
                else:
                    self.log_test("缺少帳號密碼", False, "錯誤訊息不正確")
                    return False
            else:
                self.log_test("缺少帳號密碼", False, f"期望 400，實際 {response.status_code}")
                return False
        except Exception as e:
            self.log_test("缺少帳號密碼", False, f"錯誤: {str(e)}")
            return False
        
        # 測試2: 錯誤帳號密碼
        try:
            response = self.session.post(
                f"{self.base_url}/api/login",
                json={"account": "invalid_user", "password": "invalid_pass"},
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code in [400, 500]:
                data = response.json()
                if not data.get("success"):
                    self.log_test("錯誤帳號密碼", True, "正確返回登入失敗")
                else:
                    self.log_test("錯誤帳號密碼", False, "意外的成功回應")
                    return False
            else:
                self.log_test("錯誤帳號密碼", False, f"意外的狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("錯誤帳號密碼", False, f"錯誤: {str(e)}")
            return False
        
        return True
    
    def test_login_valid(self, account=None, password=None):
        """測試 POST /api/login - 有效登入"""
        print("\n🧪 測試有效登入...")
        
        if not account:
            account = input("請輸入 NAS 帳號: ")
        if not password:
            password = input("請輸入 NAS 密碼: ")
        
        self.login_credentials = {"account": account, "password": password}
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/login",
                json=self.login_credentials,
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    required_fields = ["sid", "syno_token", "session_id"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(
                            "登入回應格式", 
                            False, 
                            f"缺少必要欄位: {missing_fields}"
                        )
                        return False
                    
                    self.log_test(
                        "有效登入", 
                        True, 
                        f"登入成功，Session ID: {data['session_id'][:8]}..."
                    )
                    
                    # 檢查是否成功創建 session 檔案
                    session_file = self.config['SESSION']['SESSION_FILE']
                    if os.path.exists(session_file):
                        print(f"   ✅ Session 檔案已創建: {session_file}")
                    else:
                        print(f"   ⚠️ Session 檔案未找到: {session_file}")
                    
                    return True
                else:
                    self.log_test("有效登入", False, data.get("error", "未知錯誤"))
                    return False
            else:
                self.log_test("有效登入", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("有效登入", False, f"錯誤: {str(e)}")
            return False
    
    def test_status_logged_in(self):
        """測試 GET /api/status - 已登入狀態"""
        print("\n🧪 測試登入狀態檢查...")
        try:
            response = self.session.get(
                f"{self.base_url}/api/status",
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("logged_in"):
                    required_fields = ["account", "session_id", "login_time", "last_activity", "expires_at"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(
                            "登入狀態格式", 
                            False, 
                            f"缺少必要欄位: {missing_fields}"
                        )
                        return False
                    
                    self.log_test(
                        "登入狀態檢查", 
                        True, 
                        f"已登入用戶: {data['account']}"
                    )
                    return True
                else:
                    self.log_test("登入狀態檢查", False, "顯示為未登入狀態")
                    return False
            else:
                self.log_test("登入狀態檢查", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("登入狀態檢查", False, f"錯誤: {str(e)}")
            return False

    # ============= 檔案管理測試 =============
    
    def test_list_files(self, path="/home/www"):
        """測試 GET /api/files - 列出檔案和資料夾"""
        print(f"\n🧪 測試檔案列表 (路徑: {path})...")
        try:
            response = self.session.get(
                f"{self.base_url}/api/files",
                params={"path": path},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    files_data = data["data"]
                    required_fields = ["files", "total", "offset"]
                    missing_fields = [field for field in required_fields if field not in files_data]
                    
                    if missing_fields:
                        self.log_test(
                            "檔案列表格式", 
                            False, 
                            f"缺少必要欄位: {missing_fields}"
                        )
                        return False
                    
                    files = files_data["files"]
                    self.log_test(
                        "檔案列表", 
                        True, 
                        f"成功獲取 {len(files)} 個項目"
                    )
                    
                    # 顯示前幾個檔案的詳細資訊
                    for i, file_info in enumerate(files[:3]):
                        file_type = "📁 資料夾" if file_info.get("isdir") else "📄 檔案"
                        print(f"   {file_type}: {file_info.get('name')}")
                        
                        # 檢查檔案資訊結構
                        if file_info.get("additional"):
                            additional = file_info["additional"]
                            size = additional.get("size", 0)
                            if not file_info.get("isdir") and size > 0:
                                print(f"      大小: {size} bytes")
                    
                    return True
                else:
                    self.log_test("檔案列表", False, data.get("error", "未知錯誤"))
                    return False
            elif response.status_code == 401:
                self.log_test("檔案列表", False, "未授權 - 可能需要重新登入")
                return False
            else:
                self.log_test("檔案列表", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("檔案列表", False, f"錯誤: {str(e)}")
            return False
    
    def test_upload_file(self, target_path="/home/www", test_filename="test_upload.txt"):
        """測試 POST /api/upload - 上傳檔案"""
        print(f"\n🧪 測試檔案上傳 (目標: {target_path}/{test_filename})...")
        
        # 創建測試檔案內容
        test_content = f"測試檔案內容\n建立時間: {datetime.now()}\n測試用途: API 自動化測試\n配置檔案: {self.config_file}"
        test_file_data = test_content.encode('utf-8')
        
        try:
            files = {'file': (test_filename, BytesIO(test_file_data), 'text/plain')}
            data = {
                'path': target_path,
                'overwrite': 'true'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files,
                data=data,
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    self.log_test(
                        "檔案上傳", 
                        True, 
                        f"成功上傳 {test_filename}"
                    )
                    return True
                else:
                    self.log_test("檔案上傳", False, response_data.get("error", "未知錯誤"))
                    return False
            elif response.status_code == 401:
                self.log_test("檔案上傳", False, "未授權 - 可能需要重新登入")
                return False
            else:
                self.log_test("檔案上傳", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("檔案上傳", False, f"錯誤: {str(e)}")
            return False
    
    def test_create_folder(self, parent_path="/home/www", folder_name=None):
        """測試 POST /api/create-folder - 建立新資料夾"""
        if not folder_name:
            folder_name = f"test_folder_{int(time.time())}"
        
        print(f"\n🧪 測試建立資料夾 ({parent_path}/{folder_name})...")
        
        try:
            request_data = {
                "folder_path": parent_path,
                "name": folder_name,
                "force_parent": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/create-folder",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "建立資料夾", 
                        True, 
                        f"成功建立資料夾 {folder_name}"
                    )
                    return True, folder_name
                else:
                    self.log_test("建立資料夾", False, data.get("error", "未知錯誤"))
                    return False, None
            elif response.status_code == 401:
                self.log_test("建立資料夾", False, "未授權 - 可能需要重新登入")
                return False, None
            else:
                self.log_test("建立資料夾", False, f"HTTP 狀態碼: {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test("建立資料夾", False, f"錯誤: {str(e)}")
            return False, None

    def test_download_file(self, file_path=None):
        """測試 GET /api/download - 取得下載連結"""
        if not file_path:
            file_path = "/home/www/test_upload.txt"  # 使用上傳測試的檔案
        
        print(f"\n🧪 測試檔案下載 ({file_path})...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/download",
                params={"path": file_path},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    download_data = data.get("data", {})
                    download_url = download_data.get("url")
                    
                    if download_url:
                        # 驗證下載連結是否包含正確的 NAS 基礎 URL
                        nas_base = self.config['NAS']['NAS_BASE_URL'].replace('/webapi/entry.cgi', '')
                        if nas_base in download_url:
                            nas_match = True
                        else:
                            nas_match = False
                            print(f"   ⚠️ 下載連結 NAS 地址不匹配:")
                            print(f"      期望包含: {nas_base}")
                            print(f"      實際連結: {download_url[:100]}...")
                        
                        self.log_test(
                            "檔案下載連結", 
                            True, 
                            f"成功生成下載連結 {'(NAS地址匹配)' if nas_match else '(NAS地址不匹配)'}"
                        )
                        print(f"   連結: {download_url[:100]}...")
                        return True
                    else:
                        self.log_test("檔案下載連結", False, "回應中沒有下載連結")
                        return False
                else:
                    self.log_test("檔案下載連結", False, data.get("error", "未知錯誤"))
                    return False
            elif response.status_code == 401:
                self.log_test("檔案下載連結", False, "未授權 - 可能需要重新登入")
                return False
            elif response.status_code == 404:
                self.log_test("檔案下載連結", False, "檔案不存在")
                return False
            else:
                self.log_test("檔案下載連結", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("檔案下載連結", False, f"錯誤: {str(e)}")
            return False

    def test_delete_files(self, paths_to_delete=None):
        """測試 POST /api/delete - 刪除檔案/資料夾"""
        if not paths_to_delete:
            paths_to_delete = ["/home/www/test_upload.txt"]  # 刪除測試上傳的檔案
        
        print(f"\n🧪 測試檔案刪除...")
        
        try:
            request_data = {
                "paths": paths_to_delete
            }
            
            response = self.session.post(
                f"{self.base_url}/api/delete",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "檔案刪除", 
                        True, 
                        f"成功刪除 {len(paths_to_delete)} 個項目"
                    )
                    return True
                else:
                    self.log_test("檔案刪除", False, data.get("error", "未知錯誤"))
                    return False
            elif response.status_code == 401:
                self.log_test("檔案刪除", False, "未授權 - 可能需要重新登入")
                return False
            else:
                self.log_test("檔案刪除", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("檔案刪除", False, f"錯誤: {str(e)}")
            return False

    # ============= 進階功能測試 =============
    
    def test_create_share(self, file_paths=None, with_password=False, with_expiry=False):
        """測試 POST /api/share - 建立分享連結"""
        if not file_paths:
            # 先上傳一個測試檔案用於分享
            test_file = "share_test.txt"
            if self.test_upload_file(test_filename=test_file):
                file_paths = [f"/home/www/{test_file}"]
            else:
                self.log_test("分享測試準備", False, "無法上傳測試檔案")
                return False
        
        print(f"\n🧪 測試建立分享連結...")
        
        try:
            request_data = {
                "paths": file_paths
            }
            
            if with_password:
                request_data["password"] = "test123"
                print("   🔒 使用密碼保護: test123")
            
            if with_expiry:
                expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                request_data["date_expired"] = expiry_date
                print(f"   ⏰ 設定過期時間: {expiry_date}")
            
            response = self.session.post(
                f"{self.base_url}/api/share",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    share_data = data.get("data", {})
                    links = share_data.get("links", [])
                    
                    if links:
                        self.log_test(
                            "建立分享連結", 
                            True, 
                            f"成功建立 {len(links)} 個分享連結"
                        )
                        
                        for i, link in enumerate(links):
                            print(f"   📋 分享連結 {i+1}:")
                            print(f"      🔗 URL: {link.get('url', 'N/A')}")
                            print(f"      🆔 ID: {link.get('id', 'N/A')}")
                            print(f"      📄 檔案名: {link.get('name', 'N/A')}")
                            
                            # 檢查 QR Code
                            qr_code = link.get('qrcode')
                            if qr_code and qr_code.startswith('data:image/png;base64,'):
                                base64_part = qr_code.split(',')[1] if ',' in qr_code else ''
                                qr_size = len(base64_part)
                                print(f"      📱 QR Code: ✅ 已生成 (大小: {qr_size} 字元)")
                            else:
                                print(f"      📱 QR Code: ❌ 未提供或格式錯誤")
                        
                        return True
                    else:
                        self.log_test("建立分享連結", False, "成功但沒有返回連結資訊")
                        return False
                else:
                    self.log_test("建立分享連結", False, data.get("error", "未知錯誤"))
                    return False
            elif response.status_code == 401:
                self.log_test("建立分享連結", False, "未授權 - 可能需要重新登入")
                return False
            else:
                self.log_test("建立分享連結", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("建立分享連結", False, f"錯誤: {str(e)}")
            return False

    def test_compress_files(self, source_paths=None, dest_path=None):
        """測試 POST /api/compress - 壓縮檔案"""
        if not source_paths:
            # 創建一些測試檔案用於壓縮
            test_files = []
            for i in range(2):
                filename = f"compress_test_{i}.txt"
                if self.test_upload_file(test_filename=filename):
                    test_files.append(f"/home/www/{filename}")
            
            if not test_files:
                self.log_test("壓縮測試準備", False, "無法上傳測試檔案")
                return False
            
            source_paths = test_files
        
        if not dest_path:
            dest_path = f"/home/www/test_archive_{int(time.time())}.zip"
        
        print(f"\n🧪 測試檔案壓縮...")
        
        try:
            request_data = {
                "source_paths": source_paths,
                "dest_path": dest_path,
                "options": {
                    "level": "normal",
                    "mode": "add",
                    "format": "zip"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/compress",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    task_info = data.get("data", {})
                    task_id = task_info.get("taskid", "Unknown")
                    self.log_test(
                        "檔案壓縮", 
                        True, 
                        f"壓縮任務已啟動，任務ID: {task_id}"
                    )
                    return True
                else:
                    self.log_test("檔案壓縮", False, data.get("error", "未知錯誤"))
                    return False
            elif response.status_code == 401:
                self.log_test("檔案壓縮", False, "未授權 - 可能需要重新登入")
                return False
            else:
                self.log_test("檔案壓縮", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("檔案壓縮", False, f"錯誤: {str(e)}")
            return False

    # ============= 系統功能測試 =============
    
    def test_list_sessions(self):
        """測試 GET /api/sessions - 檢視所有 sessions"""
        print(f"\n🧪 測試 Sessions 列表...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/sessions",
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    total_sessions = data.get("total_sessions", 0)
                    sessions = data.get("sessions", [])
                    
                    self.log_test(
                        "Sessions 列表", 
                        True, 
                        f"成功獲取 {total_sessions} 個 session"
                    )
                    
                    # 檢查 session 檔案
                    session_file = self.config['SESSION']['SESSION_FILE']
                    if os.path.exists(session_file):
                        print(f"   ✅ Session 檔案存在: {session_file}")
                        
                        # 檢查檔案內容
                        try:
                            with open(session_file, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                                file_sessions = len(file_data) if isinstance(file_data, dict) else 0
                                print(f"   📊 檔案中的 Session 數量: {file_sessions}")
                        except:
                            print(f"   ⚠️ 無法讀取 Session 檔案內容")
                    else:
                        print(f"   ❌ Session 檔案不存在: {session_file}")
                    
                    for i, session_info in enumerate(sessions[:3]):  # 顯示前3個
                        print(f"   📋 Session {i+1}:")
                        print(f"      🆔 ID: {session_info.get('session_id', 'N/A')}")
                        print(f"      👤 帳號: {session_info.get('account', 'N/A')}")
                        print(f"      📅 登入時間: {session_info.get('login_time', 'N/A')}")
                        print(f"      🕒 最後活動: {session_info.get('last_activity', 'N/A')}")
                        print(f"      ⏰ 過期時間: {session_info.get('expires_at', 'N/A')}")
                        print(f"      ✅ 狀態: {'過期' if session_info.get('is_expired') else '有效'}")
                    
                    return True
                else:
                    self.log_test("Sessions 列表", False, data.get("error", "未知錯誤"))
                    return False
            else:
                self.log_test("Sessions 列表", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Sessions 列表", False, f"錯誤: {str(e)}")
            return False
    
    def test_logout(self):
        """測試 POST /api/logout - 登出"""
        print(f"\n🧪 測試登出功能...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/logout",
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "登出功能", 
                        True, 
                        data.get("message", "登出成功")
                    )
                    return True
                else:
                    self.log_test("登出功能", False, data.get("error", "未知錯誤"))
                    return False
            else:
                self.log_test("登出功能", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("登出功能", False, f"錯誤: {str(e)}")
            return False
    
    def test_status_logged_out(self):
        """測試登出後的狀態檢查"""
        print(f"\n🧪 測試登出後狀態...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/status",
                timeout=self.config['NAS']['NAS_TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and not data.get("logged_in"):
                    self.log_test(
                        "登出後狀態", 
                        True, 
                        "確認為登出狀態"
                    )
                    return True
                else:
                    self.log_test("登出後狀態", False, "仍顯示為登入狀態")
                    return False
            else:
                self.log_test("登出後狀態", False, f"HTTP 狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("登出後狀態", False, f"錯誤: {str(e)}")
            return False

    # ============= 錯誤處理測試 =============
    
    def test_unauthorized_access(self):
        """測試未授權訪問"""
        print(f"\n🧪 測試未授權訪問...")
        
        # 清除 session cookie 來模擬未登入狀態
        self.session.cookies.clear()
        
        unauthorized_endpoints = [
            ("GET", "/api/files", {"path": "/home/www"}),
            ("POST", "/api/upload", None),
            ("POST", "/api/create-folder", {"folder_path": "/test", "name": "test"}),
            ("POST", "/api/delete", {"paths": ["/test"]}),
            ("GET", "/api/download", {"path": "/test"}),
            ("POST", "/api/share", {"paths": ["/test"]}),
            ("POST", "/api/compress", {"source_paths": ["/test"], "dest_path": "/test.zip"})
        ]
        
        all_passed = True
        
        for method, endpoint, params in unauthorized_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(
                        f"{self.base_url}{endpoint}", 
                        params=params,
                        timeout=self.config['NAS']['NAS_TIMEOUT']
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=params,
                        headers={"Content-Type": "application/json"},
                        timeout=self.config['NAS']['NAS_TIMEOUT']
                    )
                
                if response.status_code == 401:
                    print(f"   ✅ {method} {endpoint}: 正確返回 401")
                else:
                    print(f"   ❌ {method} {endpoint}: 期望 401，實際 {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ {method} {endpoint}: 錯誤 {str(e)}")
                all_passed = False
        
        self.log_test(
            "未授權訪問測試", 
            all_passed, 
            "所有需要認證的端點都正確拒絕未授權訪問" if all_passed else "部分端點未正確處理未授權訪問"
        )
        return all_passed
    
    def test_invalid_endpoints(self):
        """測試無效端點"""
        print(f"\n🧪 測試無效端點...")
        
        invalid_endpoints = [
            "/api/nonexistent",
            "/api/invalid/path",
            "/invalid",
            "/api/"
        ]
        
        all_passed = True
        
        for endpoint in invalid_endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=self.config['NAS']['NAS_TIMEOUT']
                )
                
                if response.status_code == 404:
                    print(f"   ✅ {endpoint}: 正確返回 404")
                else:
                    print(f"   ❌ {endpoint}: 期望 404，實際 {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ {endpoint}: 錯誤 {str(e)}")
                all_passed = False
        
        self.log_test(
            "無效端點測試", 
            all_passed, 
            "所有無效端點都正確返回 404" if all_passed else "部分無效端點未正確處理"
        )
        return all_passed

    # ============= 完整測試套件 =============
    
    def run_authentication_tests(self):
        """執行認證相關測試"""
        print("\n" + "="*60)
        print("🔐 身份驗證測試")
        print("="*60)
        
        results = []
        
        # 健康檢查測試
        results.append(("健康檢查", self.test_health_check()))
        
        # API 文檔測試
        results.append(("API 文檔", self.test_api_docs()))
        
        # 無效登入測試
        results.append(("無效登入", self.test_login_invalid()))
        
        # 有效登入測試
        login_result = self.test_login_valid()
        results.append(("有效登入", login_result))
        
        if login_result:
            # 登入狀態檢查
            results.append(("登入狀態檢查", self.test_status_logged_in()))
        
        return results
    
    def run_file_management_tests(self):
        """執行檔案管理測試"""
        print("\n" + "="*60)
        print("📁 檔案管理測試")
        print("="*60)
        
        results = []
        created_items = []  # 追蹤創建的項目以便清理
        
        # 檔案列表測試
        results.append(("檔案列表", self.test_list_files()))
        
        # 檔案上傳測試
        upload_result = self.test_upload_file()
        results.append(("檔案上傳", upload_result))
        if upload_result:
            created_items.append("/home/www/test_upload.txt")
        
        # 資料夾建立測試
        folder_result, folder_name = self.test_create_folder()
        results.append(("建立資料夾", folder_result))
        if folder_result and folder_name:
            created_items.append(f"/home/www/{folder_name}")
        
        # 下載連結測試
        if upload_result:
            results.append(("下載連結", self.test_download_file()))
        
        # 檔案刪除測試（清理測試檔案）
        if created_items:
            results.append(("檔案刪除", self.test_delete_files(created_items)))
        
        return results
    
    def run_advanced_feature_tests(self):
        """執行進階功能測試"""
        print("\n" + "="*60)
        print("🚀 進階功能測試")
        print("="*60)
        
        results = []
        
        # 分享功能測試
        results.append(("建立分享連結", self.test_create_share()))
        results.append(("密碼保護分享", self.test_create_share(with_password=True)))
        results.append(("時效分享", self.test_create_share(with_expiry=True)))
        
        # 壓縮功能測試
        results.append(("檔案壓縮", self.test_compress_files()))
        
        return results
    
    def run_system_tests(self):
        """執行系統功能測試"""
        print("\n" + "="*60)
        print("⚙️ 系統功能測試")
        print("="*60)
        
        results = []
        
        # Sessions 列表測試
        results.append(("Sessions 列表", self.test_list_sessions()))
        
        # 登出測試
        results.append(("登出功能", self.test_logout()))
        
        # 登出後狀態檢查
        results.append(("登出後狀態", self.test_status_logged_out()))
        
        return results
    
    def run_error_handling_tests(self):
        """執行錯誤處理測試"""
        print("\n" + "="*60)
        print("🛡️ 錯誤處理測試")
        print("="*60)
        
        results = []
        
        # 未授權訪問測試
        results.append(("未授權訪問", self.test_unauthorized_access()))
        
        # 無效端點測試
        results.append(("無效端點", self.test_invalid_endpoints()))
        
        return results
    
    def run_complete_test_suite(self):
        """執行完整測試套件"""
        print("🎯 SimpleNAS API 完整測試套件")
        print("="*60)
        
        # 檢查服務器連線
        if not self.check_server_connection():
            print("❌ 無法連接到服務器，測試中止")
            return False
        
        all_results = []
        
        # 1. 認證測試
        auth_results = self.run_authentication_tests()
        all_results.extend(auth_results)
        
        # 檢查登入是否成功，如果失敗則跳過需要認證的測試
        login_success = any(result[1] for result in auth_results if "登入" in result[0] and "無效" not in result[0])
        
        if login_success:
            # 2. 檔案管理測試
            file_results = self.run_file_management_tests()
            all_results.extend(file_results)
            
            # 3. 進階功能測試
            advanced_results = self.run_advanced_feature_tests()
            all_results.extend(advanced_results)
            
            # 4. 系統功能測試
            system_results = self.run_system_tests()
            all_results.extend(system_results)
        else:
            print("\n⚠️ 登入失敗，跳過需要認證的測試")
        
        # 5. 錯誤處理測試
        error_results = self.run_error_handling_tests()
        all_results.extend(error_results)
        
        # 測試結果摘要
        self.print_test_summary(all_results)
        
        return all(result[1] for result in all_results)
    
    def print_test_summary(self, results):
        """打印測試結果摘要"""
        print("\n" + "="*60)
        print("📊 測試結果摘要")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        failed = len(results) - passed
        
        print(f"\n📋 測試配置:")
        print(f"   配置檔案: {self.config_file}")
        print(f"   伺服器地址: {self.base_url}")
        print(f"   NAS 地址: {self.config['NAS']['NAS_BASE_URL']}")
        print(f"   超時設定: {self.config['NAS']['NAS_TIMEOUT']} 秒")
        print(f"   Session 檔案: {self.config['SESSION']['SESSION_FILE']}")
        print(f"   Session 過期: {self.config['SESSION']['SESSION_EXPIRE_DAYS']} 天")
        
        print(f"\n📈 測試結果:")
        print(f"   總測試數: {len(results)}")
        print(f"   ✅ 通過: {passed}")
        print(f"   ❌ 失敗: {failed}")
        print(f"   📊 成功率: {(passed/len(results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ 失敗的測試:")
            for test_name, result in results:
                if not result:
                    print(f"   • {test_name}")
        
        print("\n" + "="*60)
        
        if failed == 0:
            print("🎉 所有測試都通過了！API 服務器運作正常。")
        else:
            print("⚠️ 有部分測試失敗，請檢查服務器狀態和配置。")

def main():
    print("🧪 SimpleNAS Flask API 完整測試工具")
    print("基於 API.md 文檔和 config.json 配置進行全面測試")
    print("-" * 60)
    
    # 檢查配置檔案是否存在
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"❌ 找不到配置檔案: {config_file}")
        print("請確認 config.json 檔案存在於當前目錄")
        return
    
    try:
        tester = SimpleNASApiTester(config_file)
    except SystemExit:
        return
    
    print("選擇測試模式:")
    print("1. 執行完整測試套件 (推薦)")
    print("2. 僅認證測試")
    print("3. 僅檔案管理測試")
    print("4. 僅進階功能測試")
    print("5. 僅系統功能測試")
    print("6. 僅錯誤處理測試")
    print("7. 自定義測試")
    
    choice = input("\n請選擇 (1-7): ").strip()
    
    if choice == "1":
        tester.run_complete_test_suite()
    elif choice == "2":
        if tester.check_server_connection():
            results = tester.run_authentication_tests()
            tester.print_test_summary(results)
    elif choice == "3":
        if tester.check_server_connection():
            # 需要先登入
            if tester.test_login_valid():
                results = tester.run_file_management_tests()
                tester.print_test_summary(results)
            else:
                print("❌ 登入失敗，無法執行檔案管理測試")
    elif choice == "4":
        if tester.check_server_connection():
            if tester.test_login_valid():
                results = tester.run_advanced_feature_tests()
                tester.print_test_summary(results)
            else:
                print("❌ 登入失敗，無法執行進階功能測試")
    elif choice == "5":
        if tester.check_server_connection():
            if tester.test_login_valid():
                results = tester.run_system_tests()
                tester.print_test_summary(results)
            else:
                print("❌ 登入失敗，無法執行系統功能測試")
    elif choice == "6":
        if tester.check_server_connection():
            results = tester.run_error_handling_tests()
            tester.print_test_summary(results)
    elif choice == "7":
        print("\n可用的個別測試:")
        test_methods = {
            "1": ("健康檢查", tester.test_health_check),
            "2": ("API 文檔", tester.test_api_docs),
            "3": ("無效登入", tester.test_login_invalid),
            "4": ("有效登入", tester.test_login_valid),
            "5": ("登入狀態檢查", tester.test_status_logged_in),
            "6": ("檔案列表", tester.test_list_files),
            "7": ("檔案上傳", tester.test_upload_file),
            "8": ("建立資料夾", tester.test_create_folder),
            "9": ("下載連結", tester.test_download_file),
            "10": ("檔案刪除", tester.test_delete_files),
            "11": ("建立分享連結", tester.test_create_share),
            "12": ("檔案壓縮", tester.test_compress_files),
            "13": ("Sessions 列表", tester.test_list_sessions),
            "14": ("登出功能", tester.test_logout),
            "15": ("未授權訪問", tester.test_unauthorized_access),
            "16": ("無效端點", tester.test_invalid_endpoints)
        }
        
        for key, (name, _) in test_methods.items():
            print(f"{key}. {name}")
        
        test_choice = input("請選擇測試編號: ").strip()
        
        if test_choice in test_methods:
            test_name, test_method = test_methods[test_choice]
            if tester.check_server_connection():
                # 對於需要登入的測試，先檢查登入狀態
                if test_choice in ["5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]:
                    print("此測試需要先登入...")
                    if tester.test_login_valid():
                        result = test_method()
                        tester.print_test_summary([(test_name, result)])
                    else:
                        print("❌ 登入失敗，無法執行測試")
                else:
                    result = test_method()
                    tester.print_test_summary([(test_name, result)])
        else:
            print("❌ 無效的選擇")
    else:
        print("❌ 無效的選擇")

if __name__ == "__main__":
    main()