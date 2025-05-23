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
    
    nas_service.sid = session_data.get('sid')
    nas_service.syno_token = session_data.get('syno_token')
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
        
        result = nas_service.login(account, password)
        
        # 將登入資訊存入Flask session
        flask_session['nas_session'] = {
            'sid': nas_service.sid,
            'syno_token': nas_service.syno_token,
            'login_time': time.time()
        }
        
        return jsonify({
            "success": True,
            "message": "登入成功",
            "data": {
                "sid": result["sid"][:8] + "...",
                "login_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
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
        service = get_nas_session()
        if not service:
            return jsonify({
                "success": False,
                "message": "未登入"
            }), 401
        
        is_logged_in = service.is_logged_in()
        
        if is_logged_in:
            session_data = flask_session.get('nas_session')
            login_time = session_data.get('login_time', time.time())
            elapsed_time = time.time() - login_time
            
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
            flask_session.pop('nas_session', None)
            return jsonify({
                "success": False,
                "message": "Session已過期",
                "data": {"valid": False}
            }), 401
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"檢查session失敗：{str(e)}"
        }), 400 