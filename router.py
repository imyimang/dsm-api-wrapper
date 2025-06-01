from flask import request, jsonify, send_from_directory
import datetime
import time
import json
from io import BytesIO
import os

def register_routes(app, session_manager, requests_session, config, utils):
    """註冊所有路由"""
    
    # ============= 健康檢查路由 =============
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康檢查端點"""
        try:
            # 檢查系統狀態
            sessions_info = session_manager.get_all_sessions_info()
            active_sessions = len([s for s in sessions_info if not s['is_expired']])
            
            # 檢查配置檔案
            config_status = "OK"
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    json.load(f)
            except:
                config_status = "ERROR"
            
            # 檢查 session 檔案
            session_file_status = "OK"
            try:
                if os.path.exists(config.SESSION_FILE):
                    with open(config.SESSION_FILE, "r", encoding="utf-8") as f:
                        json.load(f)
                else:
                    session_file_status = "NOT_FOUND"
            except:
                session_file_status = "ERROR"
            
            health_data = {
                "status": "healthy",
                "timestamp": datetime.datetime.now().isoformat(),
                "version": "2.0.0",
                "uptime": "運行中",
                "system_checks": {
                    "config_file": config_status,
                    "session_file": session_file_status,
                    "nas_base_url": config.NAS_BASE_URL,
                    "session_expire_days": config.SESSION_EXPIRE_DAYS
                },
                "session_stats": {
                    "total_sessions": len(sessions_info),
                    "active_sessions": active_sessions,
                    "expired_sessions": len(sessions_info) - active_sessions
                },
                "services": {
                    "flask": "running",
                    "session_manager": "running",
                    "requests_session": "running"
                }
            }
            
            return jsonify(health_data), 200
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            }), 500

    # ============= 主頁和應用程式路由 =============
    
    @app.route('/', methods=['GET'])
    def index():
        """API文檔首頁"""
        # 獲取系統統計資訊
        sessions_info = session_manager.get_all_sessions_info()
        active_sessions = len([s for s in sessions_info if not s['is_expired']])
        
        api_docs = {
            "title": "SimpleNAS Flask API Server",
            "description": "簡易的 Synology NAS 管理 API - 支援多用戶",
            "version": "2.0.0",
            "author": "SimpleNAS Project",
            "system_info": {
                "total_sessions": len(sessions_info),
                "active_sessions": active_sessions,
                "session_file": config.SESSION_FILE,
                "session_expire_days": config.SESSION_EXPIRE_DAYS
            },
            "web_app": {
                "url": "/app",
                "description": "網頁版 NAS 管理介面 (完整功能含分享)"
            },
            "endpoints": {
                "System": {
                    "GET /health": "系統健康檢查",
                    "GET /": "API 總覽文件",
                    "GET /app": "網頁應用程式"
                },
                "Authentication": {
                    "POST /api/login": "登入NAS系統 - {account, password}",
                    "POST /api/logout": "登出NAS系統",
                    "GET /api/status": "檢查登入狀態"
                },
                "File Management": {
                    "GET /api/files": "列出檔案和資料夾 - ?path=/home/www",
                    "POST /api/upload": "上傳檔案 - FormData{file, path, overwrite}",
                    "POST /api/create-folder": "建立新資料夾 - {folder_path, name}",
                    "POST /api/delete": "刪除檔案/資料夾 - {paths: []}",
                    "GET /api/download": "取得下載連結 - ?path=/path/to/file"
                },
                "Advanced Features": {
                    "POST /api/share": "建立分享連結 - {paths, password?, date_expired?, date_available?}",
                    "POST /api/compress": "壓縮檔案 - {source_paths, dest_path, options?}"
                },
                "Debug": {
                    "GET /api/sessions": "檢視所有 sessions (調試用)"
                }
            },
            "session_management": {
                "description": "多用戶 Session 管理",
                "features": [
                    "支援多個用戶同時登入",
                    "Session 持久化到檔案",
                    "自動過期機制（預設1年）",
                    "自動清理過期 Sessions",
                    "基於 Flask Session 的用戶識別"
                ],
                "file_storage": config.SESSION_FILE,
                "expire_time": f"{config.SESSION_EXPIRE_DAYS} 天"
            }
        }
        
        return jsonify(api_docs)

    @app.route('/app')
    def app_route():
        """提供網頁應用程式"""
        return send_from_directory('.', 'index.html')

    # ============= API 端點 =============

    @app.route('/api/login', methods=['POST'])
    def login():
        """登入API"""
        try:
            data = request.get_json()
            if not data or 'account' not in data or 'password' not in data:
                return jsonify({"success": False, "error": "請提供帳號和密碼"}), 400
            
            result = utils.nas_login(data['account'], data['password'])
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/status', methods=['GET'])
    def status():
        """檢查登入狀態"""
        session_info = utils.get_session_info()
        
        if session_info and session_info['is_logged_in']:
            login_time = datetime.datetime.fromtimestamp(session_info['login_time'])
            last_activity = datetime.datetime.fromtimestamp(session_info['last_activity'])
            expires_at = datetime.datetime.fromtimestamp(session_info['expires_at'])
            
            return jsonify({
                "success": True,
                "logged_in": True,
                "account": session_info['account'],
                "session_id": session_info['session_id'][:8] + "...",
                "login_time": login_time.strftime('%Y-%m-%d %H:%M:%S'),
                "last_activity": last_activity.strftime('%Y-%m-%d %H:%M:%S'),
                "expires_at": expires_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({
                "success": True,
                "logged_in": False
            })

    @app.route('/api/sessions', methods=['GET'])
    def list_sessions():
        """列出所有 sessions（調試用）"""
        try:
            sessions_info = session_manager.get_all_sessions_info()
            return jsonify({
                "success": True,
                "total_sessions": len(sessions_info),
                "sessions": sessions_info
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/files', methods=['GET'])
    def list_files():
        """列出檔案"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            path = request.args.get('path', '/home/www')
            user_session = utils.get_user_session()
            
            # 更新最後活動時間
            session_manager.update_last_activity()
            
            params = {
                "api": "SYNO.FileStation.List",
                "version": "2",
                "method": "list",
                "folder_path": path,
                "filetype": "all",
                "sort_by": "name",
                "sort_direction": "ASC",
                "offset": 0,
                "limit": 1000,
                "additional": '["real_path","size","owner","time","perm","type"]',
                "_sid": user_session['sid']
            }
            
            headers = {"X-SYNO-TOKEN": user_session['syno_token']}
            
            response = requests_session.get(config.NAS_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("success"):
                error_code = result.get("error", {}).get("code", "未知錯誤")
                return jsonify({"success": False, "error": f"獲取檔案列表失敗: {error_code}"}), 500
            
            return jsonify({
                "success": True,
                "data": result["data"]
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """上傳檔案"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            if 'file' not in request.files:
                return jsonify({"success": False, "error": "未選擇檔案"}), 400
            
            file = request.files['file']
            target_path = request.form.get('path', '/home/www')
            overwrite = request.form.get('overwrite', 'true').lower() == 'true'
            user_session = utils.get_user_session()
            
            # 更新最後活動時間
            session_manager.update_last_activity()
            
            if file.filename == '':
                return jsonify({"success": False, "error": "檔案名稱為空"}), 400
            
            file_data = file.read()
            
            upload_url = f"{config.NAS_BASE_URL}?api=SYNO.FileStation.Upload&method=upload&version=2&_sid={user_session['sid']}"
            
            files = {'file': (file.filename, BytesIO(file_data))}
            data = {
                'mtime': str(int(time.time() * 1000)),
                'overwrite': str(overwrite).lower(),
                'path': target_path,
                'size': str(len(file_data))
            }
            
            headers = {"X-SYNO-TOKEN": user_session['syno_token']}
            
            response = requests_session.post(upload_url, files=files, data=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("success"):
                error_code = result.get("error", {}).get("code", "未知錯誤")
                return jsonify({"success": False, "error": f"上傳失敗: {error_code}"}), 500
            
            return jsonify({
                "success": True,
                "message": "上傳成功",
                "data": result
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/create-folder', methods=['POST'])
    def create_folder():
        """建立資料夾"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            data = request.get_json()
            if not data or 'folder_path' not in data or 'name' not in data:
                return jsonify({"success": False, "error": "請提供folder_path和name"}), 400
            
            user_session = utils.get_user_session()
            
            # 更新最後活動時間
            session_manager.update_last_activity()
            
            params = {
                "api": "SYNO.FileStation.CreateFolder",
                "method": "create",
                "version": "2",
                "folder_path": json.dumps(data['folder_path']),
                "name": json.dumps(data['name']),
                "force_parent": str(data.get('force_parent', False)).lower(),
                "_sid": user_session['sid']
            }
            
            headers = {
                "X-SYNO-TOKEN": user_session['syno_token'],
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }
            
            response = requests_session.post(config.NAS_BASE_URL, data=params, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("success"):
                error_code = result.get("error", {}).get("code", "未知錯誤")
                return jsonify({"success": False, "error": f"建立資料夾失敗: {error_code}"}), 500
            
            return jsonify({
                "success": True,
                "message": "資料夾建立成功",
                "data": result
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/delete', methods=['POST'])
    def delete_files():
        """刪除檔案或資料夾"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            data = request.get_json()
            if not data or 'paths' not in data:
                return jsonify({"success": False, "error": "請提供要刪除的路徑列表"}), 400
            
            user_session = utils.get_user_session()
            
            # 更新最後活動時間
            session_manager.update_last_activity()
            
            params = {
                "api": "SYNO.FileStation.Delete",
                "method": "start",
                "version": "2",
                "path": json.dumps(data['paths']),
                "accurate_progress": "true",
                "_sid": user_session['sid']
            }
            
            headers = {"X-SYNO-TOKEN": user_session['syno_token']}
            
            response = requests_session.get(config.NAS_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("success"):
                error_code = result.get("error", {}).get("code", "未知錯誤")
                return jsonify({"success": False, "error": f"刪除失敗: {error_code}"}), 500
            
            return jsonify({
                "success": True,
                "message": "刪除任務已啟動",
                "data": result["data"]
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/share', methods=['POST'])
    def create_share():
        """建立分享連結"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            data = request.get_json()
            if not data or 'paths' not in data:
                return jsonify({"success": False, "error": "請提供要分享的路徑列表"}), 400
            
            paths_to_share = data['paths']
            if not paths_to_share or not isinstance(paths_to_share, list):
                return jsonify({"success": False, "error": "paths 必須是一個包含至少一個路徑的列表"}), 400
            
            user_session = utils.get_user_session()
            
            # 更新最後活動時間
            session_manager.update_last_activity()
            
            utils.debug_log("開始建立分享連結", {
                "paths": paths_to_share,
                "password_protected": bool(data.get('password')),
                "date_expired": data.get('date_expired'),
                "date_available": data.get('date_available'),
                "user": user_session.get('credentials', {}).get('account')
            })
            
            api_params = {
                "api": "SYNO.FileStation.Sharing",
                "version": "3",
                "method": "create",
                "path": json.dumps(paths_to_share),
                "_sid": user_session['sid']
            }
            
            # 添加可選參數
            if data.get('password'):
                api_params["password"] = data['password']
            if data.get('date_expired'):
                api_params["date_expired"] = data['date_expired']
            if data.get('date_available'):
                api_params["date_available"] = data['date_available']
            
            headers = {"X-SYNO-TOKEN": user_session['syno_token']}
            
            response = requests_session.post(config.NAS_BASE_URL, data=api_params, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            utils.debug_log("建立分享連結回應", response_data)
            
            if not response_data.get("success"):
                error_code = response_data.get("error", {}).get("code", "未知錯誤")
                if "errors" in response_data.get("error", {}) and response_data["error"]["errors"]:
                    first_error = response_data["error"]["errors"][0]
                    error_code = first_error.get("code", error_code)
                return jsonify({"success": False, "error": f"建立分享連結失敗: {error_code}"}), 500
            
            if "data" in response_data and "links" in response_data["data"] and response_data["data"]["links"]:
                share_data = response_data["data"]
                return jsonify({
                    "success": True,
                    "message": "分享連結建立成功",
                    "data": share_data
                })
            else:
                utils.debug_log("成功回應但未找到 links 欄位", response_data)
                return jsonify({"success": False, "error": "建立分享連結成功，但回應中未找到連結資訊"}), 500
            
        except Exception as e:
            utils.debug_log("建立分享連結錯誤", str(e))
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/compress', methods=['POST'])
    def compress_files():
        """壓縮檔案"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            data = request.get_json()
            if not data or 'source_paths' not in data or 'dest_path' not in data:
                return jsonify({"success": False, "error": "請提供source_paths和dest_path"}), 400
            
            user_session = utils.get_user_session()
            
            # 更新最後活動時間
            session_manager.update_last_activity()
            
            options = data.get('options', {})
            default_options = {
                "level": "normal",
                "mode": "replace",
                "format": "zip",
                "password": None,
                "codepage": "cht"
            }
            default_options.update(options)
            
            params = {
                "api": "SYNO.FileStation.Compress",
                "method": "start",
                "version": "3",
                "path": json.dumps(data['source_paths']),
                "dest_file_path": json.dumps(data['dest_path']),
                "level": json.dumps(default_options["level"]),
                "mode": json.dumps(default_options["mode"]),
                "format": json.dumps(default_options["format"]),
                "codepage": json.dumps(default_options["codepage"]),
                "_sid": user_session['sid']
            }
            
            if default_options["password"]:
                params["password"] = default_options["password"]
            
            headers = {"X-SYNO-TOKEN": user_session['syno_token']}
            
            response = requests_session.post(config.NAS_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("success"):
                error_code = result.get("error", {}).get("code", "未知錯誤")
                return jsonify({"success": False, "error": f"壓縮失敗: {error_code}"}), 500
            
            return jsonify({
                "success": True,
                "message": "壓縮任務已啟動",
                "data": result["data"]
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/logout', methods=['POST'])
    def logout():
        """登出"""
        try:
            result = utils.logout()
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/download', methods=['GET'])
    def download_file():
        """下載檔案"""
        if not utils.is_logged_in():
            return jsonify({"success": False, "error": "請先登入"}), 401
        
        try:
            file_path = request.args.get('path')
            if not file_path:
                return jsonify({"success": False, "error": "請提供檔案路徑"}), 400
            
            utils.debug_log("開始下載檔案", {"file_path": file_path})
            
            download_url = utils.generate_download_link_with_sid(file_path)
            
            return jsonify({
                "success": True,
                "data": {"url": download_url},
                "method": "fbdownload_with_sid"
            })
            
        except Exception as e:
            utils.debug_log("下載錯誤", str(e))
            return jsonify({"success": False, "error": str(e)}), 500

    # ============= 錯誤處理 =============
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "API端點不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "伺服器內部錯誤"}), 500