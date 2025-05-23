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
    PERMANENT_SESSION_LIFETIME = 86400  # 24小時

# 日誌配置
def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging() 