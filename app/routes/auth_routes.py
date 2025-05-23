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

def get_nas_session_by_token():
    """透過 token 獲取 NAS session"""
    # 檢查 Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # 移除 "Bearer " 前綴
    else:
        # 檢查 query parameter
        token = request.args.get('token')
    
    if not token:
        return None
    
    # 清理過期 tokens
    cleanup_expired_tokens()
    
    # 檢查 token 是否存在且有效
    token_data = active_tokens.get(token)
    if not token_data:
        return None
    
    # 恢復 NAS 服務狀態
    nas_service.sid = token_data.get('sid')
    nas_service.syno_token = token_data.get('syno_token')
    
    nas_service.debug_log("透過 token 恢復 session", {
        "token_preview": token[:8] + "...",
        "sid_exists": bool(nas_service.sid),
        "account": token_data.get('account')
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

@auth_bp.route('/debug/headers', methods=['GET', 'POST'])
def debug_headers():
    """除錯：檢查請求標頭"""
    try:
        headers_info = {
            "method": request.method,
            "all_headers": dict(request.headers),
            "cookies": dict(request.cookies),
            "origin": request.headers.get('Origin'),
            "user_agent": request.headers.get('User-Agent'),
            "cookie_header": request.headers.get('Cookie'),
            "flask_session_keys": list(flask_session.keys()) if flask_session else [],
            "flask_session_data": dict(flask_session) if flask_session else {}
        }
        
        return jsonify({
            "success": True,
            "debug_info": headers_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@auth_bp.route('/debug/session/test', methods=['POST'])
def debug_session_test():
    """除錯：測試 Flask session 設置"""
    try:
        # 強制設置一個測試 session
        test_data = {
            'test_key': 'test_value',
            'timestamp': time.time(),
            'count': flask_session.get('count', 0) + 1
        }
        
        flask_session['test_data'] = test_data
        flask_session['count'] = test_data['count']
        flask_session.permanent = True
        
        # 立即檢查是否設置成功
        verification = flask_session.get('test_data')
        
        nas_service.debug_log("Session 測試", {
            "test_data_set": test_data,
            "verification": verification,
            "session_keys": list(flask_session.keys()),
            "session_permanent": flask_session.permanent
        })
        
        return jsonify({
            "success": True,
            "message": "Session 測試完成",
            "debug_info": {
                "test_data_set": test_data,
                "verification_success": bool(verification),
                "session_keys": list(flask_session.keys()),
                "session_permanent": flask_session.permanent,
                "app_secret_key_exists": bool(app.secret_key) if 'app' in globals() else 'unknown'
            }
        })
    except Exception as e:
        nas_service.debug_log("Session 測試錯誤", str(e))
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Session 測試失敗"
        }), 500

@auth_bp.route('/session/check/token', methods=['GET'])
def api_check_session_token():
    """檢查 token session 狀態"""
    try:
        service = get_nas_session_by_token()
        if not service:
            return jsonify({
                "success": False,
                "message": "Token 無效或已過期"
            }), 401
        
        # 獲取 token 資訊
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else request.args.get('token')
        token_data = active_tokens.get(token)
        
        # 驗證 DSM session 有效性
        is_logged_in = service.is_logged_in()
        
        if is_logged_in:
            login_time = token_data.get('created_at', time.time())
            elapsed_time = time.time() - login_time
            
            nas_service.debug_log("Token Session驗證成功", {
                "token_preview": token[:8] + "...",
                "account": token_data.get('account'),
                "elapsed_hours": round(elapsed_time / 3600, 1)
            })
            
            return jsonify({
                "success": True,
                "message": "Token Session有效",
                "data": {
                    "valid": True,
                    "account": token_data.get('account'),
                    "login_time": datetime.datetime.fromtimestamp(login_time).strftime('%Y-%m-%d %H:%M:%S'),
                    "elapsed_hours": round(elapsed_time / 3600, 1),
                    "token_preview": token[:8] + "..."
                }
            })
        else:
            # Token 對應的 DSM session 已過期，清理 token
            nas_service.debug_log("Token 對應的 DSM session 已過期", {
                "token_preview": token[:8] + "..."
            })
            if token in active_tokens:
                del active_tokens[token]
            
            return jsonify({
                "success": False,
                "message": "DSM Session已過期",
                "data": {"valid": False}
            }), 401
    except Exception as e:
        nas_service.debug_log("Token Session檢查發生錯誤", str(e))
        return jsonify({
            "success": False,
            "message": f"檢查token session失敗：{str(e)}"
        }), 400

@auth_bp.route('/logout/token', methods=['POST'])
def api_logout_token():
    """Token-based 登出API"""
    try:
        # 獲取 token
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else request.args.get('token')
        
        if not token:
            return jsonify({
                "success": False,
                "message": "未提供 token"
            }), 400
        
        # 清理 token
        if token in active_tokens:
            account = active_tokens[token].get('account', 'unknown')
            del active_tokens[token]
            
            nas_service.debug_log("Token 登出成功", {
                "token_preview": token[:8] + "...",
                "account": account,
                "remaining_tokens": len(active_tokens)
            })
            
            return jsonify({
                "success": True,
                "message": "Token登出成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Token 不存在或已過期"
            }), 400
    except Exception as e:
        nas_service.debug_log("Token登出錯誤", str(e))
        return jsonify({
            "success": False,
            "message": f"登出錯誤：{str(e)}"
        }), 400 