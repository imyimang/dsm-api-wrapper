# Synology DSM API Wrapper - API 文檔

本文檔詳細說明了 Synology DSM API Wrapper 提供的所有 RESTful API 端點。所有 API 端點都使用 JSON 格式進行資料交換，並遵循統一的回應格式。

## 基本資訊

- **Base URL**: `http://localhost:5000` (開發環境)
- **Content-Type**: `application/json`
- **認證方式**: Session-based (需先登入獲取 SID)
- **網頁應用**: `http://localhost:5000/app` (完整的 NAS 管理介面)

## 統一回應格式

所有 API 端點都遵循以下回應格式：

### 成功回應
```json
{
  "success": true,
  "message": "操作描述",
  "data": {
    // 實際資料內容
  }
}
```

### 錯誤回應
```json
{
  "success": false,
  "message": "錯誤描述",
  "error": {
    "code": "ERROR_CODE",
    "details": "詳細錯誤資訊"
  }
}
```

## 身份驗證端點

### POST /api/login
登入 NAS 系統，獲取 Session ID

**請求體:**
```json
{
  "account": "your_username",
  "password": "your_password"
}
```

**回應:**
```json
{
  "success": true,
  "message": "登入成功",
  "data": {
    "sid": "xxxxxxxx...",
    "login_time": "2024-01-01 12:00:00"
  }
}
```

**錯誤代碼:**
- `INVALID_CREDENTIALS`: 帳號或密碼錯誤
- `LOGIN_FAILED`: 登入失敗
- `CONNECTION_ERROR`: 連線錯誤

---

### POST /api/logout
登出 NAS 系統，清除 Session

**回應:**
```json
{
  "success": true,
  "message": "登出成功"
}
```

---

### GET /api/session/check
檢查當前 Session 狀態

**回應:**
```json
{
  "success": true,
  "message": "Session有效",
  "data": {
    "valid": true,
    "login_time": "2024-01-01 12:00:00",
    "elapsed_hours": 1.5
  }
}
```

**Session 無效時:**
```json
{
  "success": false,
  "message": "Session無效或已過期",
  "data": {
    "valid": false
  }
}
```

## 檔案管理端點

### GET /api/files
獲取指定目錄的檔案和資料夾列表

**查詢參數:**
- `path` (選填): 目錄路徑，預設為 `/home/www`

**範例請求:**
```
GET /api/files?path=/home/documents
```

**回應:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "name": "example.txt",
        "isdir": false,
        "additional": {
          "size": 1024,
          "time": {
            "atime": 1704067200,
            "mtime": 1704067200,
            "ctime": 1704067200,
            "crtime": 1704067200
          },
          "perm": {
            "posix": 644,
            "is_acl_mode": false,
            "acl": {
              "append": false,
              "del": true,
              "exec": false,
              "read": true,
              "write": true
            }
          },
          "owner": {
            "user": "admin",
            "group": "administrators",
            "uid": 1024,
            "gid": 100
          }
        }
      },
      {
        "name": "folder",
        "isdir": true,
        "additional": {
          "size": 0,
          "time": {...},
          "perm": {...},
          "owner": {...}
        }
      }
    ]
  }
}
```

---

### POST /api/upload
上傳檔案到指定路徑

**請求格式:** `multipart/form-data`

**表單欄位:**
- `file`: 檔案物件 (必填)
- `path` (選填): 目標路徑，預設為 `/home/www`
- `overwrite` (選填): 是否覆蓋現有檔案 (true/false)，預設為 false

**範例請求:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/local/file.txt" \
  -F "path=/home/documents" \
  -F "overwrite=true"
```

**回應:**
```json
{
  "success": true,
  "message": "檔案上傳成功",
  "data": {
    "filename": "file.txt",
    "path": "/home/documents/file.txt",
    "size": 1024
  }
}
```

**錯誤代碼:**
- `NO_FILE`: 沒有提供檔案
- `UPLOAD_FAILED`: 上傳失敗
- `FILE_EXISTS`: 檔案已存在且未設定覆蓋
- `PERMISSION_DENIED`: 權限不足

---

### DELETE /api/delete
刪除檔案或資料夾（支援批量刪除）

**請求體:**
```json
{
  "paths": ["/path/to/file1.txt", "/path/to/folder", "/path/to/file2.txt"]
}
```

**回應:**
```json
{
  "success": true,
  "message": "刪除任務已啟動",
  "data": {
    "taskid": "task_12345"
  }
}
```

**錯誤代碼:**
- `INVALID_PATHS`: 路徑格式錯誤
- `DELETE_FAILED`: 刪除失敗
- `PERMISSION_DENIED`: 權限不足

---

### GET /api/delete/status/<taskid>
查詢刪除任務執行狀態

**路徑參數:**
- `taskid`: 刪除任務 ID

**範例請求:**
```
GET /api/delete/status/task_12345
```

**回應:**
```json
{
  "success": true,
  "data": {
    "finished": true,
    "progress": 100,
    "total": 3,
    "processed": 3,
    "errors": []
  }
}
```

**進行中任務回應:**
```json
{
  "success": true,
  "data": {
    "finished": false,
    "progress": 66,
    "total": 3,
    "processed": 2,
    "current_file": "/path/to/file3.txt"
  }
}
```

## 🛠️ 檔案操作端點

### POST /api/compress
壓縮檔案或資料夾

**請求體:**
```json
{
  "source_paths": ["/path/to/file1.txt", "/path/to/folder"],
  "dest_path": "/path/to/archive.zip",
  "options": {
    "level": "normal",
    "format": "zip",
    "password": null
  }
}
```

**選項說明:**
- `level`: 壓縮等級 (`store`, `fastest`, `normal`, `maximum`)
- `format`: 壓縮格式 (`zip`, `7z`)
- `password`: 壓縮密碼 (選填)

**回應:**
```json
{
  "success": true,
  "message": "壓縮任務已啟動",
  "data": {
    "taskid": "compress_12345"
  }
}
```

---

### GET /api/download
生成檔案下載連結

**查詢參數:**
- `path`: 檔案路徑 (必填)

**範例請求:**
```
GET /api/download?path=/home/documents/file.txt
```

**回應:**
```json
{
  "success": true,
  "data": {
    "url": "https://nas.example.com/webapi/entry.cgi?api=SYNO.FileStation.Download&...",
    "method": "direct_with_sid"
  }
}
```

**錯誤代碼:**
- `FILE_NOT_FOUND`: 檔案不存在
- `DOWNLOAD_FAILED`: 下載連結生成失敗
- `PERMISSION_DENIED`: 權限不足

## 系統管理端點

### GET /api/tasks
獲取 NAS 系統後台任務列表

**回應:**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task_001",
        "name": "檔案複製",
        "status": "running",
        "progress": 75,
        "start_time": "2024-01-01 10:00:00",
        "estimated_time": 300
      },
      {
        "id": "task_002",
        "name": "資料備份",
        "status": "completed",
        "progress": 100,
        "start_time": "2024-01-01 09:00:00",
        "end_time": "2024-01-01 09:30:00"
      }
    ],
    "total": 2,
    "running": 1,
    "completed": 1
  }
}
```

**任務狀態:**
- `waiting`: 等待中
- `running`: 執行中
- `completed`: 已完成
- `error`: 錯誤
- `cancelled`: 已取消

---

### POST /api/debug/toggle
切換 Debug 模式

**回應:**
```json
{
  "success": true,
  "debug_mode": true,
  "message": "Debug模式已開啟"
}
```

**Debug 模式關閉時:**
```json
{
  "success": true,
  "debug_mode": false,
  "message": "Debug模式已關閉"
}
```

## 權限說明

### 檔案操作權限
- 檔案讀取: 需要檔案的讀取權限
- 檔案上傳: 需要目標目錄的寫入權限
- 檔案刪除: 需要檔案的刪除權限
- 檔案壓縮: 需要來源檔案的讀取權限和目標路徑的寫入權限

### 系統操作權限
- 系統任務查看: 需要管理者權限
- Debug 模式切換: 需要管理者權限

## 錯誤處理

### 常見錯誤代碼

| 代碼 | 說明 | 解決方案 |
|------|------|----------|
| `AUTHENTICATION_REQUIRED` | 需要先登入 | 呼叫 `/api/login` 進行登入 |
| `SESSION_EXPIRED` | Session 已過期 | 重新登入 |
| `PERMISSION_DENIED` | 權限不足 | 檢查檔案/目錄權限 |
| `FILE_NOT_FOUND` | 檔案不存在 | 確認檔案路徑正確 |
| `INVALID_PATH` | 路徑格式錯誤 | 使用正確的絕對路徑格式 |
| `QUOTA_EXCEEDED` | 儲存空間不足 | 清理空間或聯絡管理員 |
| `OPERATION_TIMEOUT` | 操作逾時 | 重試操作或檢查網路連線 |

### 錯誤回應範例
```json
{
  "success": false,
  "message": "檔案不存在",
  "error": {
    "code": "FILE_NOT_FOUND",
    "details": "指定的檔案路徑 '/home/test.txt' 不存在",
    "path": "/home/test.txt"
  }
}
```

## 使用範例

### Python 範例
```python
import requests

# 登入
login_data = {
    "account": "your_username", 
    "password": "your_password"
}
response = requests.post("http://localhost:5000/api/login", json=login_data)
session = requests.Session()

# 獲取檔案列表
files = session.get("http://localhost:5000/api/files?path=/home")
print(files.json())

# 上傳檔案
with open("test.txt", "rb") as f:
    upload_response = session.post(
        "http://localhost:5000/api/upload",
        files={"file": f},
        data={"path": "/home/uploads"}
    )
```

### cURL 範例
```bash
# 登入
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"account":"your_username","password":"your_password"}' \
  -c cookies.txt

# 獲取檔案列表
curl -X GET "http://localhost:5000/api/files?path=/home" \
  -b cookies.txt

# 上傳檔案
curl -X POST http://localhost:5000/api/upload \
  -b cookies.txt \
  -F "file=@test.txt" \
  -F "path=/home/uploads"
```