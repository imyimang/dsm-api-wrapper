#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synology NAS Flask API Server - 主應用程式
重構後的模組化版本
"""
from app import create_app

# 創建應用程式實例
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 