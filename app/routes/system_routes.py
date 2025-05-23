#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統管理相關路由
"""

from flask import Blueprint, request, jsonify, session as flask_session
from ..services import NASApiService

system_bp = Blueprint('system', __name__, url_prefix='/api')

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

@system_bp.route('/tasks', methods=['GET'])
def api_background_tasks():
    """獲取後台任務列表"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        result = service.get_background_tasks()
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"獲取任務列表失敗：{str(e)}"
        }), 400

@system_bp.route('/debug/toggle', methods=['POST'])
def api_toggle_debug():
    """切換debug模式"""
    try:
        result = nas_service.toggle_debug()
        return jsonify({
            "success": True,
            "debug_mode": result,
            "message": f"Debug模式已{'開啟' if result else '關閉'}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"切換debug模式失敗：{str(e)}"
        }), 400 