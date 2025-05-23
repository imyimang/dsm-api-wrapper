#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份驗證相關路由
"""

from flask import Blueprint, request, jsonify, session as flask_session
import time
import datetime
from ..services import NASApiService

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# 創建全域NAS服務實例
nas_service = NASApiService()

def get_nas_session():
    """獲取NAS session"""
    session_data = flask_session.get('nas_session')
    if not session_data:
        return None
    
    # 恢復實例狀態
    nas_service.sid = session_data.get('sid')
    nas_service.syno_token = session_data.get('syno_token')
    
    # 添加調試資訊
    nas_service.debug_log("恢復session狀態", {
        "sid_exists": bool(nas_service.sid),
        "syno_token_exists": bool(nas_service.syno_token),
        "sid_preview": nas_service.sid[:8] + "..." if nas_service.sid else None,
        "syno_token_preview": nas_service.syno_token[:8] + "..." if nas_service.syno_token else None
    })
    
    return nas_service

@auth_bp.route('/login', methods=['POST'])
def api_login():
    """登入API"""
    try:
        data = request.get_json() or {}
        account = data.get('account')
        password = data.get('password')
        
        if not account or not password:
            return jsonify({
                "success": False,
                "message": "請提供帳號和密碼"
            }), 400
        
        # 登入到 DSM
        result = nas_service.login(account, password)
        
        nas_service.debug_log("DSM 登入成功，準備設置 Flask session", {
            "sid_exists": bool(nas_service.sid),
            "syno_token_exists": bool(nas_service.syno_token)
        })
        
        # 將登入資訊存入Flask session
        flask_session['nas_session'] = {
            'sid': nas_service.sid,
            'syno_token': nas_service.syno_token,
            'login_time': time.time()
        }
        
        # 確保 session 永久化（在 session 存活期內）
        flask_session.permanent = True
        
        # 驗證 session 是否被正確設置
        verification = flask_session.get('nas_session')
        nas_service.debug_log("Flask session 設置驗證", {
            "session_set_success": bool(verification),
            "session_data": verification,
            "session_keys": list(flask_session.keys())
        })
        
        return jsonify({
            "success": True,
            "message": "登入成功",
            "data": {
                "sid": result["sid"][:8] + "...",
                "login_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        nas_service.debug_log("登入錯誤", str(e))
        return jsonify({
            "success": False,
            "message": f"登入失敗：{str(e)}"
        }), 400

@auth_bp.route('/logout', methods=['POST'])
def api_logout():
    """登出API"""
    try:
        service = get_nas_session()
        if service:
            service.logout()
        flask_session.pop('nas_session', None)
        
        return jsonify({
            "success": True,
            "message": "登出成功"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"登出錯誤：{str(e)}"
        }), 400

@auth_bp.route('/session/check', methods=['GET'])
def api_check_session():
    """檢查session狀態"""
    try:
        # 首先檢查 Flask session 中是否有資料
        session_data = flask_session.get('nas_session')
        nas_service.debug_log("檢查Flask session", {
            "session_exists": bool(session_data),
            "session_keys": list(session_data.keys()) if session_data else None
        })
        
        service = get_nas_session()
        if not service:
            nas_service.debug_log("無法獲取NAS service實例")
            return jsonify({
                "success": False,
                "message": "未登入"
            }), 401
        
        nas_service.debug_log("開始驗證session有效性", {
            "sid_exists": bool(service.sid),
            "syno_token_exists": bool(service.syno_token)
        })
        
        is_logged_in = service.is_logged_in()
        
        if is_logged_in:
            session_data = flask_session.get('nas_session')
            login_time = session_data.get('login_time', time.time())
            elapsed_time = time.time() - login_time
            
            nas_service.debug_log("Session驗證成功", {
                "elapsed_hours": round(elapsed_time / 3600, 1)
            })
            
            return jsonify({
                "success": True,
                "message": "Session有效",
                "data": {
                    "valid": True,
                    "login_time": datetime.datetime.fromtimestamp(login_time).strftime('%Y-%m-%d %H:%M:%S'),
                    "elapsed_hours": round(elapsed_time / 3600, 1)
                }
            })
        else:
            nas_service.debug_log("Session驗證失敗，清除Flask session")
            flask_session.pop('nas_session', None)
            return jsonify({
                "success": False,
                "message": "Session已過期",
                "data": {"valid": False}
            }), 401
    except Exception as e:
        nas_service.debug_log("Session檢查發生錯誤", str(e))
        return jsonify({
            "success": False,
            "message": f"檢查session失敗：{str(e)}"
        }), 400

@auth_bp.route('/debug/session', methods=['GET'])
def debug_session():
    """除錯：檢查 Flask session 狀態"""
    try:
        session_data = flask_session.get('nas_session')
        
        debug_info = {
            "flask_session_exists": bool(session_data),
            "flask_session_data": session_data,
            "flask_session_keys": list(flask_session.keys()) if flask_session else [],
            "nas_service_state": {
                "sid_exists": bool(nas_service.sid),
                "syno_token_exists": bool(nas_service.syno_token),
                "sid_preview": nas_service.sid[:20] + "..." if nas_service.sid else None,
                "syno_token_preview": nas_service.syno_token[:20] + "..." if nas_service.syno_token else None
            }
        }
        
        return jsonify({
            "success": True,
            "debug_info": debug_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 