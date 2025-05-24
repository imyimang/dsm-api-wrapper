#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NAS API 服務類別
"""

import requests
import json
import time
import urllib.parse
import logging
from ..config import Config, logger
from ..utils.helpers import string_to_hex

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()

class NASApiService:
    def __init__(self):
        self.base_url = Config.NAS_BASE_URL
        self.session = None
        self.sid = None
        self.syno_token = None
        self.debug_mode = True
        
        # 創建session忽略SSL證書警告
        self.client = requests.Session()
        self.client.verify = False
        self.client.timeout = Config.NAS_TIMEOUT
    
    def debug_log(self, message, data=None):
        """Debug日誌方法"""
        if self.debug_mode:
            if data and isinstance(data, (dict, list)):
                logger.info(f"[DEBUG] {message}: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                logger.info(f"[DEBUG] {message}: {data if data is not None else ''}")
    
    def toggle_debug(self):
        """切換debug模式"""
        self.debug_mode = not self.debug_mode
        logger.info(f"Debug模式: {'開啟' if self.debug_mode else '關閉'}")
        return self.debug_mode
    
    def login(self, account, password):
        """登入NAS系統"""
        try:
            login_params = {
                "api": "SYNO.API.Auth",
                "version": "7",
                "method": "login",
                "session": "webui",
                "tabid": "14667",
                "enable_syno_token": "yes",
                "account": account,
                "passwd": password,
                "logintype": "local",
                "otp_code": "",
                "enable_device_token": "no",
                "timezone": "+08:00",
                "rememberme": "1",
                "client": "browser"
            }
            
            response = self.client.get(self.base_url, params=login_params)
            response.raise_for_status()
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"登入失敗: {error_code}")
            
            self.sid = response.json()["data"]["sid"]
            self.syno_token = response.json()["data"]["synotoken"]
            
            logger.info(f"登入成功 sid={self.sid} syno_token={self.syno_token}")
            
            return {
                "success": True,
                "sid": self.sid,
                "syno_token": self.syno_token
            }
        except Exception as e:
            logger.error(f"登入錯誤: {str(e)}")
            raise e
    
    def list_directory(self, path="/home/www"):
        """獲取目錄列表"""
        if not self.sid or not self.syno_token:
            raise Exception("請先登入")
        
        try:
            self.debug_log("開始獲取目錄", {"path": path})
            
            params = {
                "api": "SYNO.FileStation.List",
                "version": "2",
                "method": "list",
                "folder_path": path,
                "filetype": "all",
                "sort_by": "type",
                "sort_direction": "ASC",
                "offset": 0,
                "limit": 1000,
                "check_dir": "true",
                "action": "list",
                "additional": '["real_path","size","owner","time","perm","type","mount_point_type","description","indexed"]',
                "_sid": self.sid
            }
            
            headers = {
                "X-SYNO-TOKEN": self.syno_token,
                "X-Requested-With": "XMLHttpRequest"
            }
            
            response = self.client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            self.debug_log("完整additional參數調用回應", response.json())
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"獲取目錄失敗: {error_code}")
            
            return response.json()["data"]
        except Exception as e:
            self.debug_log("獲取目錄錯誤", str(e))
            raise e
    
    def upload_file(self, file_data, file_name, target_path="/home/www", overwrite=True):
        """上傳檔案"""
        if not self.syno_token or not self.sid:
            raise Exception("請先登入")
        
        try:
            upload_url = f"{self.base_url}?api=SYNO.FileStation.Upload&method=upload&version=2&_sid={self.sid}"
            
            files = {'file': (file_name, file_data)}
            data = {
                'mtime': str(int(time.time() * 1000)),
                'overwrite': str(overwrite).lower(),
                'path': target_path,
                'size': str(len(file_data))
            }
            
            headers = {
                "X-SYNO-TOKEN": self.syno_token,
                "Origin": "https://cwds.taivs.tp.edu.tw:5001",
                "Referer": "https://cwds.taivs.tp.edu.tw:5001/"
            }
            
            response = self.client.post(upload_url, files=files, data=data, headers=headers)
            response.raise_for_status()
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"上傳失敗: {error_code}")
            
            return response.json()
        except Exception as e:
            logger.error(f"上傳錯誤: {str(e)}")
            raise e
    
    def logout(self):
        """登出"""
        if not self.sid or not self.syno_token:
            return
        
        try:
            params = {
                "api": "SYNO.API.Auth",
                "version": "7",
                "method": "logout",
                "session": "webui",
                "_sid": self.sid
            }
            
            headers = {"X-SYNO-TOKEN": self.syno_token}
            
            self.client.get(self.base_url, params=params, headers=headers)
            
            self.sid = None
            self.syno_token = None
            logger.info("登出成功")
        except Exception as e:
            logger.error(f"登出錯誤: {str(e)}")
    
    def is_logged_in(self):
        """檢查是否已登入並驗證session有效性"""
        if not (self.syno_token and self.sid):
            return False
        
        try:
            # 使用簡單的API呼叫來驗證session是否有效
            # 這裡我們使用 SYNO.API.Info 來檢查，這是最輕量的驗證方法
            params = {
                "api": "SYNO.API.Info",
                "version": "1",
                "method": "query",
                "query": "SYNO.API.Auth",
                "_sid": self.sid
            }
            
            headers = {"X-SYNO-TOKEN": self.syno_token}
            
            response = self.client.get(self.base_url, params=params, headers=headers, timeout=5)
            
            # 如果收到401，表示session無效
            if response.status_code == 401:
                self.debug_log("Session驗證失敗 - 401 Unauthorized")
                return False
            
            # 檢查回應是否成功
            response_data = response.json()
            if response_data.get("success"):
                self.debug_log("Session驗證成功")
                return True
            else:
                self.debug_log("Session驗證失敗", response_data)
                return False
                
        except Exception as e:
            self.debug_log("Session驗證出現錯誤", str(e))
            return False
    
    def compress_files(self, source_paths, dest_path, options=None):
        """壓縮檔案或資料夾"""
        if not self.sid or not self.syno_token:
            raise Exception("請先登入")
        
        try:
            default_options = {
                "level": "normal",
                "mode": "replace",
                "format": "zip",
                "password": None,
                "codepage": "cht"
            }
            
            if options:
                default_options.update(options)
            
            self.debug_log("開始壓縮", {
                "source_paths": source_paths,
                "dest_path": dest_path,
                "options": default_options
            })
            
            params = {
                "api": "SYNO.FileStation.Compress",
                "method": "start",
                "version": "3",
                "path": json.dumps(source_paths),
                "dest_file_path": json.dumps(dest_path),
                "level": json.dumps(default_options["level"]),
                "mode": json.dumps(default_options["mode"]),
                "format": json.dumps(default_options["format"]),
                "password": default_options["password"],
                "codepage": json.dumps(default_options["codepage"]),
                "_sid": self.sid
            }
            
            headers = {"X-SYNO-TOKEN": self.syno_token}
            
            response = self.client.post(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            self.debug_log("壓縮回應", response.json())
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"壓縮失敗: {error_code}")
            
            return response.json()["data"]
        except Exception as e:
            self.debug_log("壓縮錯誤", str(e))
            raise e
    
    def generate_download_link(self, file_path):
        """生成下載連結（主要方法）"""
        if not self.syno_token or not self.sid:
            raise Exception("請先登入")
        
        hex_path = string_to_hex(file_path)
        file_name = file_path.split("/")[-1]
        
        # 構建下載URL，移除SynoHash參數
        download_url = (
            f"{self.base_url.replace('/webapi/entry.cgi', '')}/fbdownload/{file_name}?"
            f"dlink=%22{hex_path}%22&"  # URL編碼雙引號
            f"noCache={int(time.time() * 1000)}&"
            f"mode=download&"
            f"stdhtml=false&"
            f"SynoToken={self.syno_token}"
        )
        
        self.debug_log("生成下載連結", {
            "file_path": file_path,
            "hex_path": hex_path,
            "download_url": download_url
        })
        
        return download_url
    
    def generate_download_link_with_sid(self, file_path):
        """生成包含_sid的下載連結（備用方法）"""
        if not self.syno_token or not self.sid:
            raise Exception("請先登入")
        
        hex_path = string_to_hex(file_path)
        file_name = file_path.split("/")[-1]
        
        # 添加_sid參數的版本，移除SynoHash
        download_url = (
            f"{self.base_url.replace('/webapi/entry.cgi', '')}/fbdownload/{file_name}?"
            f"dlink=%22{hex_path}%22&"
            f"noCache={int(time.time() * 1000)}&"
            f"mode=download&"
            f"stdhtml=false&"
            f"_sid={self.sid}&"
            f"SynoToken={self.syno_token}"
        )
        
        self.debug_log("生成下載連結（含_sid）", {
            "file_path": file_path,
            "hex_path": hex_path,
            "download_url": download_url,
            "sid": self.sid,
            "syno_token": self.syno_token
        })
        
        return download_url
    
    def download_file_with_api(self, file_path):
        """使用FileStation API下載檔案"""
        if not self.syno_token or not self.sid:
            raise Exception("請先登入")
        
        try:
            self.debug_log("使用API下載檔案", {"file_path": file_path})
            
            download_url = (
                f"{self.base_url}?"
                f"api=SYNO.FileStation.Download&"
                f"version=2&"
                f"method=download&"
                f"path={urllib.parse.quote(file_path)}&"
                f"mode=download&"
                f"_sid={self.sid}"
            )
            
            self.debug_log("API下載連結", {
                "file_path": file_path,
                "download_url": download_url,
                "sid": self.sid,
                "syno_token": self.syno_token
            })
            
            return {"success": True, "url": download_url, "method": "api"}
        except Exception as e:
            self.debug_log("API下載錯誤", str(e))
            raise e
    
    def download_file(self, file_path):
        """下載檔案 - 實現多種策略"""
        try:
            self.debug_log("開始下載檔案", {"file_path": file_path})
            
            # 策略1：嘗試使用FileStation API下載
            try:
                result = self.download_file_with_api(file_path)
                self.debug_log("API下載成功", result)
                return result
            except Exception as api_error:
                self.debug_log("API下載失敗，嘗試直接連結", str(api_error))
            
            # 策略2：嘗試直接下載連結（無SynoHash）
            try:
                download_url = self.generate_download_link(file_path)
                return {"success": True, "url": download_url, "method": "direct"}
            except Exception as direct_error:
                self.debug_log("直接下載失敗，嘗試含_sid的連結", str(direct_error))
            
            # 策略3：嘗試包含_sid的下載連結
            download_url_with_sid = self.generate_download_link_with_sid(file_path)
            return {"success": True, "url": download_url_with_sid, "method": "direct_with_sid"}
            
        except Exception as e:
            self.debug_log("下載錯誤", str(e))
            raise e
    
    def start_delete_task(self, file_paths, options=None):
        """啟動刪除檔案/資料夾任務"""
        if not self.sid or not self.syno_token:
            raise Exception("請先登入")
        
        try:
            default_options = {"accurate_progress": "true"}
            if options:
                default_options.update(options)
            
            self.debug_log("開始刪除任務", {
                "file_paths": file_paths,
                "options": default_options
            })
            
            params = {
                "api": "SYNO.FileStation.Delete",
                "method": "start",
                "version": "2",
                "path": json.dumps(file_paths),
                "accurate_progress": default_options["accurate_progress"],
                "_sid": self.sid
            }
            
            headers = {"X-SYNO-TOKEN": self.syno_token}
            
            response = self.client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            self.debug_log("刪除任務回應", response.json())
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"啟動刪除任務失敗: {error_code}")
            
            return response.json()["data"]
        except Exception as e:
            self.debug_log("啟動刪除任務錯誤", str(e))
            raise e
    
    def get_delete_task_status(self, taskid):
        """查詢刪除任務狀態"""
        if not self.sid or not self.syno_token:
            raise Exception("請先登入")
        
        try:
            self.debug_log("查詢刪除任務狀態", {"taskid": taskid})
            
            params = {
                "api": "SYNO.FileStation.Delete",
                "method": "status",
                "version": "1",
                "taskid": json.dumps(taskid),
                "_sid": self.sid
            }
            
            headers = {"X-SYNO-TOKEN": self.syno_token}
            
            response = self.client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            self.debug_log("刪除任務狀態回應", response.json())
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"查詢刪除狀態失敗: {error_code}")
            
            return response.json()["data"]
        except Exception as e:
            self.debug_log("查詢刪除狀態錯誤", str(e))
            raise e
    
    def get_background_tasks(self, options=None):
        """獲取後台任務列表"""
        if not self.sid or not self.syno_token:
            raise Exception("請先登入")
        
        try:
            default_options = {
                "is_list_sharemove": "true",
                "is_vfs": "true",
                "bkg_info": "true"
            }
            
            # 合併選項，與JavaScript版本保持一致
            task_options = {**default_options, **(options or {})}
            
            self.debug_log("獲取後台任務列表", task_options)
            
            params = {
                "api": "SYNO.FileStation.BackgroundTask",
                "method": "list",
                "version": "3",
                "is_list_sharemove": task_options["is_list_sharemove"],
                "is_vfs": task_options["is_vfs"],
                "bkg_info": task_options["bkg_info"],
                "_sid": self.sid
            }
            
            headers = {"X-SYNO-TOKEN": self.syno_token}
            
            response = self.client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            self.debug_log("後台任務列表回應", response.json())
            
            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                raise Exception(f"獲取後台任務列表失敗: {error_code}")
            
            return response.json()["data"]
        except Exception as e:
            self.debug_log("獲取後台任務列表錯誤", str(e))
            raise e
    
    def create_folder(self, folder_path, name, force_parent=False):
        """新增資料夾"""
        if not self.sid or not self.syno_token:
            raise Exception("請先登入")

        try:
            self.debug_log("開始新增資料夾", {
                "folder_path": folder_path,
                "name": name,
                "force_parent": force_parent
            })

            params = {
                "api": "SYNO.FileStation.CreateFolder",
                "method": "create",
                "version": "2",
                "folder_path": json.dumps(folder_path), # API文件通常要求路徑是JSON字串
                "name": json.dumps(name), # 資料夾名稱也可能是JSON字串
                "force_parent": str(force_parent).lower(), # 布林值轉為字串 'true'/'false'
                "_sid": self.sid
            }

            headers = {
                "X-SYNO-TOKEN": self.syno_token,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" # 根據請求範例
            }

            # POST請求，參數放在data部分
            response = self.client.post(self.base_url, data=params, headers=headers)
            response.raise_for_status()

            self.debug_log("新增資料夾回應", response.json())

            if not response.json().get("success"):
                error_code = response.json().get("error", {}).get("code", "未知錯誤")
                # 嘗試從更深層結構獲取錯誤訊息
                if "errors" in response.json().get("error", {}) and response.json()["error"]["errors"]:
                    error_details = response.json()["error"]["errors"][0]
                    if "code" in error_details:
                         error_code = error_details["code"]
                    elif "reason" in error_details:
                         error_code = error_details["reason"]

                # Synology API 錯誤碼參考:
                # 400: Bad Parameter - The value of parameter is not valid.
                # 401: Parameter is not a JSON string - The value of parameter is not a JSON string.
                # 403: The logged in session does not have permission.
                # 404: The path is not found.
                # 406: The folder or file name is empty or includes invalid characters.
                # 407: A file or folder of the same name already exists in the destination folder.
                # 408: The logged in user session is not validated.
                # 409: The volume status is abnormal.
                # 412: The parent folder is not specified or is invalid.
                # 413: The folder path is too long.
                # 416: Failed to create a folder. The error is undefined.
                # 417: The number of folders in the parent folder has reached the system's maximum limit.
                # 418: Failed to create a folder. The error is undefined.
                raise Exception(f"新增資料夾失敗: {error_code}")

            return response.json() # 通常成功時，data欄位可能不直接包含資料夾資訊，而是成功訊息
        except Exception as e:
            self.debug_log("新增資料夾錯誤", str(e))
            raise e
    
    def delete_files(self, file_paths, on_progress=None):
        """刪除檔案或資料夾（完整流程）"""
        try:
            self.debug_log("開始刪除檔案", {"file_paths": file_paths})
            
            task_result = self.start_delete_task(file_paths)
            taskid = task_result["taskid"]
            
            self.debug_log("刪除任務已啟動", {"taskid": taskid})
            
            return {
                "success": True,
                "taskid": taskid,
                "message": "刪除任務已啟動，請監控進度"
            }
        except Exception as e:
            self.debug_log("刪除檔案錯誤", str(e))
            raise e 