#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 應用程式初始化模組
"""

from flask import Flask, jsonify, send_from_directory, redirect, url_for, request
from flask_cors import CORS
from .config import Config
from .routes import auth_bp, file_bp, system_bp
import os

def create_app(config_class=Config):
    """應用程式工廠函數"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 確保 session 配置正確
    app.config['SESSION_COOKIE_SECURE'] = False  # 開發環境不使用 HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 啟用CORS，並配置支持 credentials
    CORS(app, 
         supports_credentials=True,
         origins=['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:3000', 'http://127.0.0.1:5000'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         expose_headers=['Access-Control-Allow-Credentials'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # 自定義 CORS 標頭處理
    @app.after_request
    def after_request(response):
        """確保每個回應都包含正確的 CORS 標頭"""
        origin = request.headers.get('Origin')
        if origin in ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:3000', 'http://127.0.0.1:5000']:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return response
    
    # 註冊藍圖
    app.register_blueprint(auth_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(system_bp)
    
    # 註冊錯誤處理器
    register_error_handlers(app)
    
    # 靜態文件路由
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """提供靜態文件"""
        return send_from_directory('../static', filename)
    
    # 網頁應用路由
    @app.route('/app')
    def web_app():
        """網頁應用主頁"""
        return send_from_directory('../static', 'index.html')
    
    # 註冊主頁路由 - API 文檔
    @app.route('/', methods=['GET'])
    def index():
        """API文檔首頁"""
        api_docs = {
            "title": "Synology NAS Flask API Server",
            "description": "完整重構自 nasApi.js 的 Python Flask API",
            "version": "1.0.0",
            "web_app": {
                "url": "/app",
                "description": "網頁版 NAS 管理介面"
            },
            "endpoints": {
                "Authentication": {
                    "POST /api/login": "登入NAS系統",
                    "POST /api/logout": "登出NAS系統",
                    "GET /api/session/check": "檢查session狀態"
                },
                "File Management": {
                    "GET /api/files": "列出檔案和資料夾",
                    "POST /api/upload": "上傳檔案",
                    "DELETE /api/delete": "刪除檔案/資料夾",
                    "GET /api/delete/status/<taskid>": "查詢刪除任務狀態"
                },
                "File Operations": {
                    "POST /api/compress": "壓縮檔案/資料夾",
                    "GET /api/download": "生成下載連結 (使用直接連結+SID方法)"
                },
                "System": {
                    "GET /api/tasks": "獲取後台任務列表",
                    "POST /api/debug/toggle": "切換debug模式"
                }
            }
        }
        
        return jsonify(api_docs)

    return app

def register_error_handlers(app):
    """註冊錯誤處理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "API端點不存在",
            "error": {
                "code": "NOT_FOUND",
                "details": "請檢查API路徑是否正確"
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "message": "伺服器內部錯誤",
            "error": {
                "code": "INTERNAL_ERROR",
                "details": "請稍後再試或聯絡管理員"
            }
        }), 500
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "message": "HTTP方法不允許",
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "details": "請檢查HTTP方法是否正確"
            }
        }), 405 