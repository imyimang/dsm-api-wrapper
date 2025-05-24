#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置設定模組
"""

import os
import logging

# Flask 配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'synology_nas_secret_key_2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # NAS API 配置
    NAS_BASE_URL = "https://cwds.taivs.tp.edu.tw:5001/webapi/entry.cgi"
    NAS_TIMEOUT = 10
    
    # Session 配置
    SESSION_COOKIE_NAME = "dsm_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # 容器環境中可能需要設為 False
    SESSION_COOKIE_SAMESITE = None  # 允許跨站請求
    PERMANENT_SESSION_LIFETIME = 86400  # 24小時，秒為單位
    
    # 重要：如果在容器中使用，禁用 Flask 默認 SESSION_COOKIE_DOMAIN
    SESSION_COOKIE_DOMAIN = None  # 允許任何域名使用 cookie
    
    # 使用 FileSystem 而非默認的 cookie session
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "/tmp/flask_session"
    SESSION_FILE_THRESHOLD = 500  # 最多存储多少個 session

# 日誌配置
def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()