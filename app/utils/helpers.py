#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
輔助函數模組
"""

def string_to_hex(text):
    """字符串轉hex編碼"""
    return text.encode('utf-8').hex() 