# Synology DSM API Wrapper - API 文檔

本文檔詳細說明了 Synology DSM API Wrapper 提供的所有 RESTful API 端點。所有 API 端點都使用 JSON 格式進行資料交換，並遵循統一的回應格式。

## 基本資訊

- **Base URL**: `http://localhost:5000` (開發環境)
- **Content-Type**: `application/json`
- **認證方式**: Cookie-based Session (Flask Session)
- **CORS**: 支援跨域請求，需設定 `credentials: 'include'`
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
  "message": "錯誤描述"
}
```

## 身份驗證端點

### POST /api/login
登入 NAS 系統，建立 Flask Session

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

**錯誤範例:**
```json
{
  "success": false,
  "message": "登入失敗：帳號或密碼錯誤"
}
```

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
  "message": "Session已過期",
  "data": {
    "valid": false
  }
}
```

---

### GET /api/debug/session
除錯 Flask session 狀態 (開發用)

**回應:**
```json
{
  "success": true,
  "debug_info": {
    "flask_session_exists": true,
    "flask_session_data": {...},
    "nas_service_state": {...}
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
        "path": "/home/documents/example.txt",
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
          },
          "real_path": "/volume1/homes/admin/documents/example.txt",
          "type": "TXT"
        }
      }
    ],
    "offset": 0,
    "total": 1
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
- `overwrite` (選填): 是否覆蓋現有檔案 (true/false)，預設為 true

**範例請求:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/local/file.txt" \
  -F "path=/home/documents" \
  -F "overwrite=true" \
  -b cookies.txt
```

**回應:**
```json
{
  "success": true,
  "message": "上傳成功",
  "data": {
    "blSkip": false,
    "file": "file.txt",
    "pid": 12345
  }
}
```

**錯誤範例:**
```json
{
  "success": false,
  "message": "上傳失敗：沒有檔案"
}
```

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

### 常見錯誤範例

```json
{
  "success": false,
  "message": "未登入"
}
```

```json
{
  "success": false,
  "message": "獲取檔案列表失敗：權限不足"
}
```

```json
{
  "success": false,
  "message": "上傳失敗：沒有檔案"
}
```

## 使用範例

### JavaScript 範例 (正確的 Cookie-based 認證)
```javascript
// 登入
fetch('http://localhost:5000/api/login', {
    method: 'POST',
    credentials: 'include',  // 重要！必須設定
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        account: 'your_username',
        password: 'your_password'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // 登入成功，後續請求會自動帶上 cookie
        return fetch('http://localhost:5000/api/files', {
            credentials: 'include'  // 必須設定
        });
    }
});

// 獲取檔案列表
fetch('http://localhost:5000/api/files?path=/home', {
    credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));

// 上傳檔案
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('path', '/home/uploads');
formData.append('overwrite', 'true');

fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    credentials: 'include',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Python 範例
```python
import requests

# 創建session以保持cookie
session = requests.Session()

# 登入
login_data = {
    "account": "your_username", 
    "password": "your_password"
}
response = session.post("http://localhost:5000/api/login", json=login_data)

if response.json()['success']:
    # 獲取檔案列表
    files = session.get("http://localhost:5000/api/files?path=/home")
    print(files.json())
    
    # 上傳檔案
    with open("test.txt", "rb") as f:
        upload_response = session.post(
            "http://localhost:5000/api/upload",
            files={"file": f},
            data={"path": "/home/uploads", "overwrite": "true"}
        )
    print(upload_response.json())
```

### cURL 範例
```bash
# 登入並保存cookie
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
  -F "path=/home/uploads" \
  -F "overwrite=true"

# 刪除檔案
curl -X DELETE http://localhost:5000/api/delete \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"paths":["/home/uploads/test.txt"]}'
```

## 重要注意事項

1. **認證方式**: 使用 Cookie-based Session，前端必須設定 `credentials: 'include'`
2. **上傳檔案**: 預設 `overwrite=true`，會覆蓋同名檔案
3. **檔案列表**: 回應包含 `offset` 和 `total` 欄位，支援分頁
4. **錯誤處理**: 統一使用 `success` 和 `message` 欄位
5. **路徑格式**: 使用絕對路徑，如 `/home/www/file.txt`