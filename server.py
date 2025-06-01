from flask import Flask, session
import requests
import json
import time
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from router import register_routes

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()  # type: ignore

load_dotenv()

with open("config.json", "r", encoding="utf-8") as f:
    config_data = json.load(f)

app = Flask(__name__, static_folder='.')
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # 用於 Flask session

# 簡易設定
class Config:
    NAS_BASE_URL = config_data["NAS"]["NAS_BASE_URL"] 
    NAS_TIMEOUT = config_data["NAS"]["NAS_TIMEOUT"]
    SESSION_FILE = config_data["SESSION"]["SESSION_FILE"] 
    SESSION_EXPIRE_DAYS = config_data["SESSION"]["SESSION_EXPIRE_DAYS"] 

# Session 管理類別
class SessionManager:
    def __init__(self, session_file, expire_days=365):
        self.session_file = session_file
        self.expire_days = expire_days
        self.sessions = self.load_sessions()

    def load_sessions(self):
        """從檔案載入 sessions"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 確保 data 是字典類型
                    if not isinstance(data, dict):
                        print(f"[WARNING] Session 檔案格式錯誤，重新初始化")
                        return {}
                    # 清理過期的 sessions
                    self.cleanup_expired_sessions(data)
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] 載入 session 檔案失敗: {e}")
        return {}

    def save_sessions(self):
        """儲存 sessions 到檔案"""
        try:
            # 確保 self.sessions 是字典
            if not isinstance(self.sessions, dict):
                self.sessions = {}
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[ERROR] 儲存 session 檔案失敗: {e}")

    def cleanup_expired_sessions(self, sessions=None):
        """清理過期的 sessions"""
        if sessions is None:
            sessions = self.sessions
        
        # 確保 sessions 是字典類型
        if not isinstance(sessions, dict):
            print(f"[WARNING] Sessions 資料類型錯誤，重新初始化")
            if sessions is None:
                self.sessions = {}
            return
        
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in sessions.items():
            if isinstance(session_data, dict) and session_data.get('expires_at', 0) < current_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del sessions[session_id]
        
        if expired_sessions:
            print(f"[INFO] 清理了 {len(expired_sessions)} 個過期 session")

    def get_current_user_session_id(self):
        """獲取當前用戶的 session ID"""
        if 'user_session_id' not in session:
            session['user_session_id'] = str(uuid.uuid4())
        return session['user_session_id']

    def get_user_session(self, session_id=None):
        """獲取用戶的 session 資料"""
        # 確保 self.sessions 是字典
        if not isinstance(self.sessions, dict):
            self.sessions = {}
        
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        user_session = self.sessions.get(session_id, {})
        
        # 檢查是否過期
        if user_session and isinstance(user_session, dict) and user_session.get('expires_at', 0) < time.time():
            self.remove_session(session_id)
            return {}
        
        return user_session

    def set_user_session(self, session_data, session_id=None):
        """設定用戶的 session 資料"""
        # 確保 self.sessions 是字典
        if not isinstance(self.sessions, dict):
            self.sessions = {}
        
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        # 設定過期時間（一年後）
        expires_at = time.time() + (self.expire_days * 24 * 60 * 60)
        session_data['expires_at'] = expires_at
        session_data['last_activity'] = time.time()
        session_data['session_id'] = session_id
        
        self.sessions[session_id] = session_data
        self.save_sessions()

    def remove_session(self, session_id=None):
        """移除用戶的 session"""
        # 確保 self.sessions 是字典
        if not isinstance(self.sessions, dict):
            self.sessions = {}
            return
        
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_sessions()

    def is_logged_in(self, session_id=None):
        """檢查用戶是否已登入"""
        user_session = self.get_user_session(session_id)
        return (isinstance(user_session, dict) and 
                user_session.get('sid') is not None and 
                user_session.get('syno_token') is not None)

    def update_last_activity(self, session_id=None):
        """更新最後活動時間"""
        # 確保 self.sessions 是字典
        if not isinstance(self.sessions, dict):
            self.sessions = {}
            return
        
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        if session_id in self.sessions and isinstance(self.sessions[session_id], dict):
            self.sessions[session_id]['last_activity'] = time.time()
            self.save_sessions()

    def get_all_sessions_info(self):
        """獲取所有 sessions 的資訊（用於調試）"""
        # 確保 self.sessions 是字典
        if not isinstance(self.sessions, dict):
            self.sessions = {}
            return []
        
        info = []
        for session_id, session_data in self.sessions.items():
            if not isinstance(session_data, dict):
                continue
                
            info.append({
                'session_id': session_id[:8] + '...',
                'account': session_data.get('credentials', {}).get('account', 'Unknown') if isinstance(session_data.get('credentials'), dict) else 'Unknown',
                'login_time': datetime.fromtimestamp(session_data.get('login_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if session_data.get('login_time') else 'Unknown',
                'last_activity': datetime.fromtimestamp(session_data.get('last_activity', 0)).strftime('%Y-%m-%d %H:%M:%S') if session_data.get('last_activity') else 'Unknown',
                'expires_at': datetime.fromtimestamp(session_data.get('expires_at', 0)).strftime('%Y-%m-%d %H:%M:%S') if session_data.get('expires_at') else 'Unknown',
                'is_expired': session_data.get('expires_at', 0) < time.time()
            })
        return info

# 初始化 Session 管理器
session_manager = SessionManager(Config.SESSION_FILE, Config.SESSION_EXPIRE_DAYS)
# 啟動時清理過期 sessions
session_manager.cleanup_expired_sessions()
session_manager.save_sessions()

# 建立requests session
requests_session = requests.Session()
requests_session.verify = False

# 工具類別
class Utils:
    def __init__(self, session_manager, requests_session, config):
        self.session_manager = session_manager
        self.requests_session = requests_session
        self.config = config
        self.timeout = (10, config.NAS_TIMEOUT)

    def string_to_hex(self, input_string):
        """將字串轉換為十六進制"""
        return input_string.encode('utf-8').hex()

    def debug_log(self, message, data=None):
        """Debug日誌"""
        if data:
            print(f"[DEBUG] {message}: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"[DEBUG] {message}")

    def is_logged_in(self, session_id=None):
        """檢查是否已登入"""
        return self.session_manager.is_logged_in(session_id)

    def get_user_session(self, session_id=None):
        """獲取用戶 session"""
        return self.session_manager.get_user_session(session_id)

    def nas_login(self, account, password):
        """登入NAS系統"""
        login_params = {
            "api": "SYNO.API.Auth",
            "version": "7",
            "method": "login",
            "session": "webui",
            "tabid": str(int(time.time())),  # 使用時間戳作為 tabid
            "enable_syno_token": "yes",
            "account": account,
            "passwd": password,
            "logintype": "local",
            "otp_code": "",
            "enable_device_token": "no",
            "timezone": "+08:00",
            "rememberme": "1",
            "client": "browser"
        }
        
        response = self.requests_session.get(
            self.config.NAS_BASE_URL,
            params=login_params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        if not result.get("success"):
            error_code = result.get("error", {}).get("code", "未知錯誤")
            raise Exception(f"登入失敗: {error_code}")
        
        # 儲存session資訊到檔案
        session_data = {
            'sid': result["data"]["sid"],
            'syno_token': result["data"]["synotoken"],
            'login_time': time.time(),
            'credentials': {'account': account, 'password': password}
        }
        
        self.session_manager.set_user_session(session_data)
        
        self.debug_log("登入成功", {
            "account": account,
            "session_id": self.session_manager.get_current_user_session_id()[:8] + "...",
            "sid": session_data['sid'][:20] + "...",
            "syno_token": session_data['syno_token'][:20] + "..."
        })
        
        return {
            "success": True,
            "sid": session_data['sid'],
            "syno_token": session_data['syno_token'],
            "session_id": self.session_manager.get_current_user_session_id()
        }

    def logout(self):
        """登出NAS系統"""
        user_session = self.get_user_session()
        
        if not user_session:
            return {"success": True, "message": "已經是登出狀態"}
        
        try:
            # 呼叫 Synology 登出 API
            params = {
                "api": "SYNO.API.Auth",
                "version": "7",
                "method": "logout",
                "session": "webui",
                "_sid": user_session['sid']
            }
            
            headers = {"X-SYNO-TOKEN": user_session['syno_token']}
            
            self.requests_session.get(self.config.NAS_BASE_URL, params=params, headers=headers)
            
        except Exception as e:
            self.debug_log("登出 API 呼叫失敗", str(e))
        
        # 移除本地 session
        self.session_manager.remove_session()
        
        return {"success": True, "message": "登出成功"}

    def generate_download_link_with_sid(self, file_path):
        """生成包含_sid的下載連結"""
        user_session = self.get_user_session()
        
        if not user_session or not user_session.get('syno_token') or not user_session.get('sid'):
            raise Exception("請先登入")
        
        # 更新最後活動時間
        self.session_manager.update_last_activity()
        
        # 確保路徑以 / 開頭
        if not file_path.startswith('/'):
            file_path = '/' + file_path
            
        hex_path = self.string_to_hex(file_path)
        file_name = file_path.split("/")[-1]
        
        # 使用 _sid 參數的版本，移除 SynoHash
        base_url = self.config.NAS_BASE_URL.replace('/webapi/entry.cgi', '')
        download_url = (
            f"{base_url}/fbdownload/{file_name}?"
            f"dlink=%22{hex_path}%22&"
            f"noCache={int(time.time() * 1000)}&"
            f"mode=download&"
            f"stdhtml=false&"
            f"_sid={user_session['sid']}&"
            f"SynoToken={user_session['syno_token']}"
        )
        
        self.debug_log("生成下載連結（含_sid）", {
            "file_path": file_path,
            "hex_path": hex_path,
            "download_url": download_url,
            "session_id": self.session_manager.get_current_user_session_id()[:8] + "...",
            "sid": user_session['sid'][:20] + "...",
            "syno_token": user_session['syno_token'][:20] + "..."
        })
        
        return download_url

    def get_session_info(self):
        """獲取當前用戶的 session 資訊"""
        user_session = self.get_user_session()
        if not user_session:
            return None
        
        return {
            'session_id': self.session_manager.get_current_user_session_id(),
            'account': user_session.get('credentials', {}).get('account'),
            'login_time': user_session.get('login_time'),
            'last_activity': user_session.get('last_activity'),
            'expires_at': user_session.get('expires_at'),
            'is_logged_in': self.is_logged_in()
        }

# 初始化工具
utils = Utils(session_manager, requests_session, Config)

# 註冊路由
register_routes(app, session_manager, requests_session, Config, utils)