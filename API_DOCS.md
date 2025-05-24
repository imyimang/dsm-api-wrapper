# Synology DSM API Wrapper - API 文檔

本文檔詳細說明了 Synology DSM API Wrapper 提供的所有 RESTful API 端點。所有 API 端點都使用 JSON 格式進行資料交換，並遵循統一的回應格式。

## 基本資訊

- **Base URL**: `http://localhost:5000` (開發環境)
- **Content-Type**: `application/json`
- **認證方式**: 
  - **主要方式**: Cookie-based Session (Flask Session)
  - **替代方式**: Token-based Authentication (Bearer Token)
- **CORS**: ✅ 完整支援跨域請求
  - 支援的 Origins: `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:8080`, `null`
  - Cookie 設置: `SameSite=None; HttpOnly=True`
  - 前端必須設定: `credentials: 'include'`
- **網頁應用**: `http://localhost:5000/app` (完整的 NAS 管理介面)

## 🔧 跨域配置更新 (2025-01-24)

### ✅ 已修復的跨域問題
- **SameSite 設置**: 從 `Lax` 改為 `None`，支援跨域 Cookie 傳送
- **CORS Origin**: 明確指定允許的 origins，不使用通配符 `*`
- **Credentials 支援**: 正確處理 `Access-Control-Allow-Credentials: true`
- **邊緣案例處理**: 支援 `file://` 協議和 `null` origin

### 🌐 支援的 Origins
```
- http://localhost:3000 (開發前端)
- http://127.0.0.1:3000 (本地 IP)
- http://localhost:8080 (替代端口)
- null (file:// 協議)
```

### 📋 前端配置要求
```javascript
// 所有 API 請求必須包含
fetch('http://localhost:5000/api/endpoint', {
    credentials: 'include',  // 🔥 必須設定！
    // ... 其他設置
});
```

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

### 🍪 Cookie-based 認證 (推薦)

#### POST /api/login
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

**重要設置:**
- Cookie 自動設置: `session=xxx; SameSite=None; HttpOnly=True`
- 前端必須使用: `credentials: 'include'`

---

#### POST /api/logout
登出 NAS 系統，清除 Session

**回應:**
```json
{
  "success": true,
  "message": "登出成功"
}
```

---

#### GET /api/session/check
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

### 🔑 Token-based 認證 (跨域友善)

#### POST /api/login/token
Token-based 登入，適合跨域應用

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
  "message": "Token登入成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "sid": "xxxxxxxx...",
    "login_time": "2024-01-01 12:00:00",
    "expires_in": 86400
  }
}
```

**使用方式:**
```javascript
// 在後續請求中使用 Authorization header
fetch('/api/files', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

---

#### GET /api/session/check/token
檢查 Token session 狀態

**請求標頭:**
```
Authorization: Bearer <your_token>
```

**回應:**
```json
{
  "success": true,
  "message": "Token Session有效",
  "data": {
    "valid": true,
    "account": "username",
    "login_time": "2024-01-01 12:00:00",
    "elapsed_hours": 1.5,
    "token_preview": "eyJ0eXAi..."
  }
}
```

---

#### POST /api/logout/token
Token-based 登出

**請求標頭:**
```
Authorization: Bearer <your_token>
```

**回應:**
```json
{
  "success": true,
  "message": "Token登出成功"
}
```

## 🔍 Debug 端點 (開發用)

### GET /api/debug/session
檢查 Flask session 狀態

**回應:**
```json
{
  "success": true,
  "debug_info": {
    "flask_session_exists": true,
    "flask_session_data": {
      "nas_session": {
        "sid": "xxx",
        "syno_token": "xxx",
        "login_time": 1704067200
      }
    },
    "flask_session_keys": ["_permanent", "nas_session"],
    "nas_service_state": {
      "sid_exists": true,
      "syno_token_exists": true,
      "sid_preview": "xxxxxxxx...",
      "syno_token_preview": "xxxxxxxx..."
    }
  }
}
```

---

### GET /POST /api/debug/headers
檢查請求標頭和 CORS 設置

**回應:**
```json
{
  "success": true,
  "debug_info": {
    "method": "GET",
    "all_headers": {
      "Origin": "http://localhost:3000",
      "User-Agent": "Mozilla/5.0...",
      "Cookie": "session=xxx"
    },
    "cookies": {
      "session": "xxx"
    },
    "origin": "http://localhost:3000",
    "cookie_header": "session=xxx",
    "flask_session_keys": ["_permanent", "nas_session"],
    "flask_session_data": {...}
  }
}
```

---

### POST /api/debug/session/test
測試 Flask session 設置功能

**回應:**
```json
{
  "success": true,
  "message": "Session 測試完成",
  "debug_info": {
    "test_data_set": {
      "test_key": "test_value",
      "timestamp": 1704067200,
      "count": 1
    },
    "verification_success": true,
    "session_keys": ["_permanent", "test_data", "count"],
    "session_permanent": true,
    "app_secret_key_exists": true
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

### POST /api/folder
建立新的資料夾

**請求體:**
```json
{
  "parent_path": "/home/www",
  "folder_name": "MyNewFolder",
  "force_parent": false 
}
```
- `parent_path` (必填): 字串，新資料夾的父路徑。
- `folder_name` (必填): 字串，新資料夾的名稱 (不應包含路徑分隔符 `/` 或 `\`)。
- `force_parent` (選填): 布林值，如果父路徑不存在時是否自動建立。預設為 `false`。

**回應 (成功):**
```json
{
  "success": true,
  "message": "建立資料夾成功",
  "data": {
    // 根據 NAS API 的實際回應，這裡可能包含新資料夾的資訊或僅是成功狀態
    // 例如: "folder_path": "/home/www/MyNewFolder"
  }
}
```

**回應 (失敗 - 例如名稱無效):**
```json
{
  "success": false,
  "message": "建立資料夾失敗：資料夾名稱不能包含斜線 (/) 或反斜線 (\\)"
}
```

**回應 (失敗 - 例如 NAS API 錯誤):**
```json
{
  "success": false,
  "message": "建立資料夾失敗：新增資料夾失敗: 407" // 407 表示同名資料夾已存在
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

### POST /api/share
建立檔案或資料夾的分享連結

**請求體:**
```json
{
  "paths": ["/path/to/file.txt", "/path/to/folder"],
  "password": "optional_password",
  "date_expired": "2024-12-31",
  "date_available": "2024-01-01",
  "permissions": "read"
}
```

**參數說明:**
- `paths` (必填): 字串陣列，要分享的檔案或資料夾路徑列表
- `password` (選填): 字串，分享連結的密碼保護
- `date_expired` (選填): 字串，分享連結的過期日期 (格式: YYYY-MM-DD)
- `date_available` (選填): 字串，分享連結的生效日期 (格式: YYYY-MM-DD)
- `permissions` (選填): 字串，分享權限設定

**回應 (成功):**
```json
{
  "success": true,
  "message": "分享連結建立成功",
  "data": {
    "links": [
      {
        "id": "Au5S1mxjY",
        "url": "https://your-nas.com:5001/sharing/Au5S1mxjY",
        "name": "檔案名稱.pdf",
        "path": "/home/www/nas/檔案名稱.pdf",
        "qrcode": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJMA...",
        "date_expired": "",
        "date_available": "",
        "has_password": false,
        "status": "valid",
        "isFolder": false,
        "link_owner": "admin",
        "uid": 1682,
        "app": {
          "enable_upload": false,
          "is_folder": false
        }
      }
    ],
    "offset": 0,
    "total": 1
  }
}
```

**回應欄位說明:**
- `links`: 分享連結陣列，每個檔案/資料夾會產生一個分享連結
- `id`: 分享連結的唯一識別碼
- `url`: 完整的分享連結 URL
- `qrcode`: QR Code 圖片的 base64 編碼 (data URI 格式)
- `name`: 檔案或資料夾名稱
- `path`: 原始檔案路徑
- `date_expired`: 過期時間 (空字串表示無限期)
- `has_password`: 是否設有密碼保護
- `status`: 分享狀態 ("valid" 表示有效)
- `isFolder`: 是否為資料夾

**錯誤回應範例:**
```json
{
  "success": false,
  "message": "建立分享連結失敗: 407"
}
```

**前端使用範例:**
```javascript
// 分享單一檔案
fetch('/api/share', {
    method: 'POST',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        paths: ['/home/www/document.pdf']
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        const link = data.data.links[0];
        console.log('分享連結:', link.url);
        console.log('QR Code:', link.qrcode);
        console.log('分享 ID:', link.id);
    }
});

// 分享多個檔案並設定密碼保護
fetch('/api/share', {
    method: 'POST',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        paths: ['/home/www/file1.txt', '/home/www/folder'],
        password: 'mypassword123',
        date_expired: '2024-12-31'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        data.data.links.forEach(link => {
            console.log(`${link.name}: ${link.url}`);
        });
    }
});
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
      }
    ],
    "total": 1,
    "running": 1,
    "completed": 0
  }
}
```

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

## 使用範例

### JavaScript 範例

#### 🍪 Cookie-based 認證 (推薦，支援跨域)
```javascript
// 登入 - 支援跨域 (localhost:3000 → localhost:5000)
fetch('http://localhost:5000/api/login', {
    method: 'POST',
    credentials: 'include',  // 🔥 必須設定！支援跨域 Cookie
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
        console.log('✅ 登入成功，Cookie 已設置 (SameSite=None)');
        // 後續請求會自動帶上 cookie
        return fetch('http://localhost:5000/api/files', {
            credentials: 'include'  // 必須設定
        });
    }
});

// 檢查 session 狀態
fetch('http://localhost:5000/api/session/check', {
    credentials: 'include'
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('✅ Session 有效:', data.data.valid);
    } else {
        console.log('❌ Session 無效，需要重新登入');
    }
});
```

#### 🔑 Token-based 認證
```javascript
let authToken = null;

// Token 登入
fetch('http://localhost:5000/api/login/token', {
    method: 'POST',
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
        authToken = data.data.token;
        console.log('✅ Token 登入成功');
        localStorage.setItem('nas_token', authToken);
    }
});

// 使用 Token 進行 API 請求
fetch('http://localhost:5000/api/files?path=/home', {
    headers: {
        'Authorization': `Bearer ${authToken}`
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

#### 🔍 Debug 檢查 (開發用)
```javascript
// 檢查 Flask Session 狀態
fetch('http://localhost:5000/api/debug/session', {
    credentials: 'include'
})
.then(response => response.json())
.then(data => {
    console.log('Flask Session 狀態:', data.debug_info);
});

// 檢查請求標頭
fetch('http://localhost:5000/api/debug/headers', {
    credentials: 'include'
})
.then(response => response.json())
.then(data => {
    console.log('請求標頭信息:', data.debug_info);
});
```

### Python 範例
```python
import requests

# Cookie-based 認證
session = requests.Session()
login_data = {
    "account": "your_username", 
    "password": "your_password"
}
response = session.post("http://localhost:5000/api/login", json=login_data)

if response.json()['success']:
    # 獲取檔案列表
    files = session.get("http://localhost:5000/api/files?path=/home")
    print(files.json())

# Token-based 認證
token_response = requests.post("http://localhost:5000/api/login/token", json=login_data)
if token_response.json()['success']:
    token = token_response.json()['data']['token']
    
    # 使用 token 請求
    files = requests.get("http://localhost:5000/api/files?path=/home", 
                        headers={'Authorization': f'Bearer {token}'})
    print(files.json())
```

### cURL 範例
```bash
# Cookie-based 認證
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"account":"your_username","password":"your_password"}' \
  -c cookies.txt

# 獲取檔案列表
curl -X GET "http://localhost:5000/api/files?path=/home" \
  -b cookies.txt

# Token-based 認證
TOKEN=$(curl -X POST http://localhost:5000/api/login/token \
  -H "Content-Type: application/json" \
  -d '{"account":"your_username","password":"your_password"}' \
  | jq -r '.data.token')

# 使用 token 獲取檔案列表
curl -X GET "http://localhost:5000/api/files?path=/home" \
  -H "Authorization: Bearer $TOKEN"
```

## 重要注意事項

### 🔧 2025-01-24 跨域修復更新

1. **跨域 Cookie 支援**: ✅ 已完全修復
   - Cookie 設置: `SameSite=None; HttpOnly=True`
   - 支援從 `localhost:3000` 訪問 `localhost:5000`
   - 前端**必須**設定 `credentials: 'include'`

2. **認證方式選擇**:
   - **推薦**: Cookie-based Session (支援跨域)
   - **替代**: Token-based Authentication (Bearer Token)

3. **CORS 配置**:
   - 支援的 Origins: `localhost:3000`, `localhost:8080`, `null`
   - 自動處理 OPTIONS 預檢請求
   - 正確設置 `Access-Control-Allow-Credentials: true`

4. **Debug 工具**:
   - `/api/debug/session` - 檢查 Flask session 狀態
   - `/api/debug/headers` - 檢查請求標頭
   - `/api/debug/session/test` - 測試 session 設置

### 📋 技術細節

5. **上傳檔案**: 預設 `overwrite=true`，會覆蓋同名檔案
6. **檔案列表**: 回應包含 `offset` 和 `total` 欄位，支援分頁
7. **錯誤處理**: 統一使用 `success` 和 `message` 欄位
8. **路徑格式**: 使用絕對路徑，如 `/home/www/file.txt`

### 🚀 測試建議

**修復驗證步驟**:
1. 重啟 Flask 伺服器
2. 清除瀏覽器 cookies
3. 重新載入前端應用 (localhost:3000)
4. 測試登入流程
5. 檢查 `/api/debug/session` 顯示 `flask_session_exists: true`

**常見問題排除**:
- 如果 session 仍無效，檢查是否設定 `credentials: 'include'`
- 跨域請求失敗，確認 Origin 在允許列表中
- Token 認證可作為 Cookie 的替代方案