#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檔案管理相關路由 - 簡化版
"""

from flask import Blueprint, request, jsonify, session as flask_session
from ..services import NASApiService

file_bp = Blueprint('file', __name__, url_prefix='/api')

# 創建全域NAS服務實例
nas_service = NASApiService()

def get_nas_session():
    """獲取NAS session (支援 Cookie 和 Token 認證)"""
    # 1. 優先嘗試 Token 認證
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        from .auth_routes import active_tokens, cleanup_expired_tokens
        
        cleanup_expired_tokens()
        token_data = active_tokens.get(token)
        if token_data:
            nas_service.sid = token_data.get('sid')
            nas_service.syno_token = token_data.get('syno_token')
            return nas_service
    
    # 2. 回退到 Cookie Session 認證
    session_data = flask_session.get('nas_session')
    nas_service.debug_log("獲取 Flask session", {
        "session_exists": bool(session_data),
        "session_data": session_data,
        "flask_session_keys": list(flask_session.keys())
    })
    
    if not session_data:
        nas_service.debug_log("無 Flask session 資料")
        return None
    
    # 🔥 恢復 NAS 服務狀態
    nas_service.sid = session_data.get('sid')
    nas_service.syno_token = session_data.get('syno_token')
    
    nas_service.debug_log("恢復 NAS session 狀態", {
        "sid_exists": bool(nas_service.sid),
        "syno_token_exists": bool(nas_service.syno_token),
        "sid_preview": nas_service.sid[:20] + "..." if nas_service.sid else None,
        "syno_token_preview": nas_service.syno_token[:8] + "..." if nas_service.syno_token else None
    })
    
    # 🔥 關鍵修正：不要在這裡驗證 Session 有效性！
    # 這會導致剛登入的 Session 被錯誤判斷為無效
    return nas_service

@file_bp.route('/files', methods=['GET'])
def api_list_files():
    """列出檔案"""
    try:
        # 🔥 嘗試三種方式獲取 session
        service = get_nas_session()
        
        # 1. 從 cookie 獲取
        session_data = flask_session.get('nas_session')
        nas_service.debug_log("獲取 Flask session", {
            "session_exists": bool(session_data),
            "session_data": session_data,
            "flask_session_keys": list(flask_session.keys())
        })
        
        # 2. 從 URL 參數獲取
        if not service and request.args.get('sid') and request.args.get('token'):
            nas_service.sid = request.args.get('sid')
            nas_service.syno_token = request.args.get('token')
            service = nas_service
            nas_service.debug_log("從 URL 參數恢復 session", {
                "sid_exists": bool(nas_service.sid),
                "token_exists": bool(nas_service.syno_token)
            })
        
        # 3. 如果都沒有，則返回未登入
        if not service:
            nas_service.debug_log("無法獲取 NAS session")
            return jsonify({"success": False, "message": "未登入"}), 401
        
        # 🔥 在實際調用時才驗證 Session，而不是在獲取時驗證
        if not service.sid or not service.syno_token:
            nas_service.debug_log("NAS session 資料不完整", {
                "sid_exists": bool(service.sid),
                "syno_token_exists": bool(service.syno_token)
            })
            return jsonify({"success": False, "message": "登入資訊不完整"}), 401
        
        path = request.args.get('path', '/home/www')
        nas_service.debug_log("開始獲取檔案列表", {"path": path})
        
        # 🔥 使用 nas_service 中的自動重登機制
        result = service.list_directory(path)
        
        return jsonify({
            "success": True,
            "data": result,
            "current_path": path,
            # 🔥 返回 sid 和 token，供前端保存
            "sid": service.sid,
            "token": service.syno_token
        })
        
    except Exception as e:
        error_msg = str(e)
        nas_service.debug_log("檔案列表錯誤", error_msg)
        
        # 檢查是否為 Session 相關錯誤
        if "Session" in error_msg or "登入" in error_msg or "119" in error_msg:
            return jsonify({
                "success": False,
                "message": error_msg
            }), 401
        else:
            return jsonify({
                "success": False,
                "message": f"載入失敗：{error_msg}"
            }), 400

@file_bp.route('/upload', methods=['POST'])
def api_upload():
    """上傳檔案"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "沒有檔案"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "沒有選擇檔案"}), 400
        
        target_path = request.form.get('path', '/home/www')
        overwrite = request.form.get('overwrite', 'true').lower() == 'true'
        
        result = service.upload_file(file.read(), file.filename, target_path, overwrite)
        
        return jsonify({
            "success": True,
            "message": "上傳成功",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"上傳失敗：{str(e)}"
        }), 400

@file_bp.route('/compress', methods=['POST'])
def api_compress():
    """壓縮檔案"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        data = request.get_json()
        source_paths = data.get('source_paths', [])
        dest_path = data.get('dest_path')
        options = data.get('options', {})
        
        if not source_paths or not dest_path:
            return jsonify({"success": False, "message": "缺少必要參數"}), 400
        
        result = service.compress_files(source_paths, dest_path, options)
        
        return jsonify({
            "success": True,
            "message": "壓縮任務已啟動",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"壓縮失敗：{str(e)}"
        }), 400

@file_bp.route('/download', methods=['GET'])
def api_download():
    """生成下載連結 - 使用直接連結+SID方法"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        file_path = request.args.get('path')
        
        if not file_path:
            return jsonify({"success": False, "message": "缺少檔案路徑"}), 400
        
        # 直接使用direct_with_sid方法
        url = service.generate_download_link_with_sid(file_path)
        result = {"success": True, "url": url, "method": "direct_with_sid"}
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"生成下載連結失敗：{str(e)}"
        }), 400

@file_bp.route('/delete', methods=['DELETE'])
def api_delete():
    """刪除檔案"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        data = request.get_json()
        file_paths = data.get('paths', [])
        
        if not file_paths:
            return jsonify({"success": False, "message": "缺少檔案路徑"}), 400
        
        result = service.delete_files(file_paths)
        
        return jsonify({
            "success": True,
            "message": "刪除任務已啟動",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"刪除失敗：{str(e)}"
        }), 400

@file_bp.route('/delete/status/<taskid>', methods=['GET'])
def api_delete_status(taskid):
    """查詢刪除任務狀態"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        result = service.get_delete_task_status(taskid)
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"查詢刪除狀態失敗：{str(e)}"
        }), 400 

@file_bp.route('/folder', methods=['POST'])
def api_create_folder():
    """建立資料夾"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        data = request.get_json()
        parent_path = data.get('parent_path')
        folder_name = data.get('folder_name')
        force_parent = data.get('force_parent', False)

        if not parent_path or not folder_name:
            return jsonify({"success": False, "message": "缺少必要參數 parent_path 或 folder_name"}), 400
        
        # 新增：後端驗證 folder_name
        if '/' in folder_name or '\\' in folder_name:
            return jsonify({"success": False, "message": "資料夾名稱不能包含斜線 (/) 或反斜線 (\\)"}), 400

        result = service.create_folder(parent_path, folder_name, force_parent)
        return jsonify({
            "success": True,
            "message": "建立資料夾成功",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"建立資料夾失敗：{str(e)}"
        }), 400

@file_bp.route('/share', methods=['POST'])
def api_create_share_link():
    """建立檔案/資料夾的分享連結"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        data = request.get_json()
        paths_to_share = data.get('paths') # 預期是一個路徑字串的列表
        # password = data.get('password') # 可選
        # date_expired = data.get('date_expired') # 可選
        # ... 其他可選參數 ...

        if not paths_to_share or not isinstance(paths_to_share, list) or not all(isinstance(p, str) for p in paths_to_share):
            return jsonify({"success": False, "message": "缺少有效的 paths 參數 (必須是路徑字串列表)"}), 400
        
        # 目前服務層只接收 paths_to_share，未來可擴展
        result = service.create_sharing_link(paths_to_share)
        
        # API 成功時 result 包含 {"links": [...], "has_folder": ...}
        return jsonify({
            "success": True,
            "message": "分享連結建立成功",
            "data": result 
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"建立分享連結失敗：{str(e)}"
        }), 400