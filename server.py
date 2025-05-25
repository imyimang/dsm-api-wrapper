from flask import Flask, session
import requests
import json
import time
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from router import register_routes

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()  # type: ignore

app = Flask(__name__, static_folder='.')
app.secret_key = 'your-secret-key-change-this-in-production'  # 用於 Flask session

# 簡易設定
class Config:
    NAS_BASE_URL = "https://cwds.taivs.tp.edu.tw:5001/webapi/entry.cgi"
    NAS_TIMEOUT = 30
    SESSION_FILE = "session.json"
    SESSION_EXPIRE_DAYS = 365  # 預設一年過期

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
                    # 清理過期的 sessions
                    self.cleanup_expired_sessions(data)
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] 載入 session 檔案失敗: {e}")
        return {}

    def save_sessions(self):
        """儲存 sessions 到檔案"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[ERROR] 儲存 session 檔案失敗: {e}")

    def cleanup_expired_sessions(self, sessions=None):
        """清理過期的 sessions"""
        if sessions is None:
            sessions = self.sessions
        
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in sessions.items():
            if session_data.get('expires_at', 0) < current_time:
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
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        user_session = self.sessions.get(session_id, {})
        
        # 檢查是否過期
        if user_session and user_session.get('expires_at', 0) < time.time():
            self.remove_session(session_id)
            return {}
        
        return user_session

    def set_user_session(self, session_data, session_id=None):
        """設定用戶的 session 資料"""
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
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_sessions()

    def is_logged_in(self, session_id=None):
        """檢查用戶是否已登入"""
        user_session = self.get_user_session(session_id)
        return (user_session.get('sid') is not None and 
                user_session.get('syno_token') is not None)

    def update_last_activity(self, session_id=None):
        """更新最後活動時間"""
        if session_id is None:
            session_id = self.get_current_user_session_id()
        
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = time.time()
            self.save_sessions()

    def get_all_sessions_info(self):
        """獲取所有 sessions 的資訊（用於調試）"""
        info = []
        for session_id, session_data in self.sessions.items():
            info.append({
                'session_id': session_id[:8] + '...',
                'account': session_data.get('credentials', {}).get('account', 'Unknown'),
                'login_time': datetime.fromtimestamp(session_data.get('login_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if session_data.get('login_time') else 'Unknown',
                'last_activity': datetime.fromtimestamp(session_data.get('last_activity', 0)).strftime('%Y-%m-%d %H:%M:%S') if session_data.get('last_activity') else 'Unknown',
                'expires_at': datetime.fromtimestamp(session_data.get('expires_at', 0)).strftime('%Y-%m-%d %H:%M:%S') if session_data.get('expires_at') else 'Unknown',
                'is_expired': session_data.get('expires_at', 0) < time.time()
            })
        return info

# 初始化 Session 管理器
session_manager = SessionManager(Config.SESSION_FILE, Config.SESSION_EXPIRE_DAYS)

# 建立requests session
requests_session = requests.Session()
requests_session.verify = False
requests_session.timeout = Config.NAS_TIMEOUT  # type: ignore

# 工具類別
class Utils:
    def __init__(self, session_manager, requests_session, config):
        self.session_manager = session_manager
        self.requests_session = requests_session
        self.config = config

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
        
        response = self.requests_session.get(self.config.NAS_BASE_URL, params=login_params)
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

if __name__ == '__main__':
    print("=== SimpleNAS Flask API Server ===")
    print("伺服器啟動中...")
    print("網頁介面: http://127.0.0.1:5000/app")
    print("API 文檔: http://127.0.0.1:5000/")
    print(f"Session 檔案: {Config.SESSION_FILE}")
    print(f"Session 過期時間: {Config.SESSION_EXPIRE_DAYS} 天")
    print("=====================================")
    
    # 顯示現有 sessions 資訊
    sessions_info = session_manager.get_all_sessions_info()
    if sessions_info:
        print(f"現有 Sessions: {len(sessions_info)} 個")
        for info in sessions_info:
            print(f"  - {info['session_id']} ({info['account']}) - 最後活動: {info['last_activity']}")
    
    app.run(host='127.0.0.1', port=5000, debug=True)

