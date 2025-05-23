#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模組
"""

from .auth_routes import auth_bp
from .file_routes import file_bp
from .system_routes import system_bp

__all__ = ['auth_bp', 'file_bp', 'system_bp'] 