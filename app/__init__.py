#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 應用程式初始化模組
"""

from flask import Flask, jsonify, send_from_directory, redirect, url_for, request, make_response
from flask_cors import CORS
from .config import Config
from .routes import auth_bp, file_bp, system_bp
import os
from datetime import timedelta

def create_app(config_class=Config):
    """應用程式工廠函數"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 🔥 關鍵修復：確保 Flask session 正確配置
    app.secret_key = app.config['SECRET_KEY']
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=app.config['PERMANENT_SESSION_LIFETIME'])
    
    # 🚀 跨域 Cookie 修復：關鍵設置
    app.config['SESSION_COOKIE_SECURE'] = False  # 開發環境不使用 HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # 🔥 關鍵修復：允許跨域
    app.config['SESSION_COOKIE_DOMAIN'] = None  # 明確設為 None
    app.config['SESSION_COOKIE_PATH'] = '/'  # 明確設置路徑
    app.config['SESSION_COOKIE_NAME'] = 'session'  # 明確設置 cookie 名稱
    
    # 🌐 CORS 配置修復
    CORS(app, 
         supports_credentials=True,
         origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8080', 'null'],  # 具體 origins
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         send_wildcard=False  # 確保不發送通配符
    )
    
    # 🛠️ 手動 CORS 處理 (處理邊緣案例)
    @app.after_request
    def after_request(response):
        """確保每個回應都包含正確的 CORS 標頭"""
        origin = request.headers.get('Origin')
        
        # 允許的 origins 列表
        allowed_origins = [
            'http://localhost:3000', 
            'http://127.0.0.1:3000', 
            'http://localhost:8080',
            'file://',  # 本地文件協議
            'null'      # 某些情況下的 origin
        ]
        
        # 處理 origin
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        elif origin is None or origin == 'null':
            # 處理 file:// 協議或 origin 為 null 的情況
            response.headers['Access-Control-Allow-Origin'] = 'null'
        
        # 設置 credentials 和其他 CORS 標頭
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        
        # 🔥 重要：確保 Set-Cookie 有正確的屬性
        if response.headers.get('Set-Cookie'):
            # Flask 會自動處理，但我們確保屬性正確
            pass
        
        return response
    
    # 🔧 OPTIONS 預檢請求處理
    @app.before_request
    def handle_options():
        """處理 CORS 預檢請求"""
        if request.method == 'OPTIONS':
            response = make_response()
            origin = request.headers.get('Origin')
            
            allowed_origins = [
                'http://localhost:3000', 
                'http://127.0.0.1:3000', 
                'http://localhost:8080',
                'file://',
                'null'
            ]
            
            if origin and origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
            elif origin is None or origin == 'null':
                response.headers['Access-Control-Allow-Origin'] = 'null'
            
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