#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 應用程式初始化模組
"""

from flask import Flask, jsonify, send_from_directory, redirect, url_for, request, make_response
from flask_cors import CORS
from flask_session import Session  # 🔥 引入 Flask-Session
import os
import logging
from .config import Config

def create_app(config_class=Config):
    """應用程式工廠函數"""
    app = Flask(__name__, static_folder='../static', static_url_path='')
    
    # 🔥 確保 SECRET_KEY 設置
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    
    # 🔥 配置 Session
    app.config['SESSION_TYPE'] = Config.SESSION_TYPE
    app.config['SESSION_FILE_DIR'] = Config.SESSION_FILE_DIR
    app.config['SESSION_COOKIE_NAME'] = Config.SESSION_COOKIE_NAME
    app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
    app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME
    app.config['SESSION_COOKIE_DOMAIN'] = Config.SESSION_COOKIE_DOMAIN
    app.config['SESSION_FILE_THRESHOLD'] = Config.SESSION_FILE_THRESHOLD
    
    # 🔥 初始化 Flask-Session
    os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)  # 確保目錄存在
    Session(app)
    
    # 🔥 配置 CORS 允許憑證 (credentials)
    CORS(app, supports_credentials=True)
    
    # 註冊藍圖
    from .routes import auth_bp, file_bp, system_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(system_bp)
    
    # 主頁路由

    @app.route('/', methods=['GET'])
    def index():
        """API文檔首頁"""
        api_docs = {
            "title": "Synology NAS Flask API Server",
            "description": "完整重構自 nasApi.js 的 Python Flask API",
            "version": "1.4.0",
            "web_app": {
                "url": "/app",
                "description": "網頁版 NAS 管理介面 (含分享功能)"
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
                    "POST /api/folder": "建立新的資料夾",
                    "DELETE /api/delete": "刪除檔案/資料夾",
                    "GET /api/delete/status/<taskid>": "查詢刪除任務狀態"
                },
                "File Operations": {
                    "POST /api/compress": "壓縮檔案/資料夾",
                    "GET /api/download": "生成下載連結 (使用直接連結+SID方法)",
                    "POST /api/share": "建立檔案/資料夾分享連結 (含QR Code)"
                },
                "System": {
                    "GET /api/tasks": "獲取後台任務列表",
                    "POST /api/debug/toggle": "切換debug模式"
                }
            },
            "features": {
                "sharing": {
                    "description": "檔案分享功能",
                    "supports": [
                        "QR Code 生成 (base64 格式)",
                        "密碼保護",
                        "過期時間設定",
                        "多檔案批次分享",
                        "資料夾分享"
                    ],
                    "qr_code_format": "data:image/png;base64,..."
                },
                "web_interface": {
                    "description": "完整的網頁管理介面",
                    "features": [
                        "響應式設計",
                        "拖放上傳",
                        "即時分享對話框",
                        "QR Code 顯示",
                        "一鍵複製分享連結"
                    ]
                }
            },
            "documentation": {
                "api_docs": "/api (本頁面)",
                "detailed_docs": "查看 API_DOCS.md 檔案",
                "readme": "查看 README.md 檔案"
            }
        }
        
        return jsonify(api_docs)
    
    @app.route('/app')
    def app_route():
        return app.send_static_file('index.html')
        
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