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
    """獲取NAS session"""
    session_data = flask_session.get('nas_session')
    if not session_data:
        return None
    
    nas_service.sid = session_data.get('sid')
    nas_service.syno_token = session_data.get('syno_token')
    return nas_service

@file_bp.route('/files', methods=['GET'])
def api_list_files():
    """列出檔案"""
    try:
        service = get_nas_session()
        if not service:
            return jsonify({"success": False, "message": "未登入"}), 401
        
        path = request.args.get('path', '/home/www')
        result = service.list_directory(path)
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"獲取檔案列表失敗：{str(e)}"
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