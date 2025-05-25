# SimpleNAS API 文件

本文檔介紹 SimpleNAS 系統的 API 接口及其使用方法。

## 總覽

- **基礎 URL**：所有 API 請求的基礎 URL 預設為執行服務器的主機和端口。
- **認證**：除了 `/api/login` 和 `/api/status` (未登入時)，所有 API 請求都需要在 Header 中傳遞有效的 `session_id` (通常由客戶端自動處理，例如通過 Cookie)。部分直接與 Synology NAS 通信的 API 會使用內部管理的 `_sid` 和 `SynoToken`。
- **請求格式**：POST 請求的 Body 應為 JSON 格式，`Content-Type` 設為 `application/json`。檔案上傳使用 `multipart/form-data`。
- **回應格式**：所有 API 回應均為 JSON 格式。成功的回應通常包含 `"success": true`，失敗則包含 `"success": false` 和一個 `error` 訊息。

## API 端點

### 身份驗證 (Authentication)

#### 1. 登入 NAS 系統

- **Endpoint**: `POST /api/login`
- **說明**: 使用者通過此接口登入 Synology NAS。成功登入後，伺服器會建立一個 session 並返回 session ID。
- **請求 Body** (application/json):
  ```json
  {
      "account": "your_nas_username",
      "password": "your_nas_password"
  }
  ```
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "sid": "Synology_DSM_Session_ID",
      "syno_token": "Synology_CSRF_Token",
      "session_id": "simpleNAS_internal_session_id"
  }
  ```
- **失敗回應** (400 Bad Request / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請提供帳號和密碼 或 登入失敗: 錯誤碼"
  }
  ```

#### 2. 檢查登入狀態

- **Endpoint**: `GET /api/status`
- **說明**: 檢查目前用戶的登入狀態。
- **成功回應 (已登入)** (200 OK):
  ```json
  {
      "success": true,
      "logged_in": true,
      "account": "current_logged_in_username",
      "session_id": "simpleNAS_internal_session_id_prefix...",
      "login_time": "YYYY-MM-DD HH:MM:SS",
      "last_activity": "YYYY-MM-DD HH:MM:SS",
      "expires_at": "YYYY-MM-DD HH:MM:SS"
  }
  ```
- **成功回應 (未登入)** (200 OK):
  ```json
  {
      "success": true,
      "logged_in": false
  }
  ```

#### 3. 登出 NAS 系統

- **Endpoint**: `POST /api/logout`
- **說明**: 登出目前用戶的 NAS session，並清除伺服器端的 session 資訊。
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "message": "成功登出" // 或 "已經是登出狀態"
  }
  ```
- **失敗回應** (500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "登出過程中發生錯誤"
  }
  ```

### 檔案管理 (File Management)

#### 1. 列出檔案和資料夾

- **Endpoint**: `GET /api/files`
- **說明**: 獲取指定路徑下的檔案和資料夾列表。
- **Query 參數**:
    - `path` (string, 必填): 要列出內容的資料夾路徑，例如 `/home` 或 `/photo/travel`。
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "data": {
          "files": [
              {
                  "isdir": false,
                  "name": "example.jpg",
                  "path": "/photo/travel/example.jpg",
                  "additional": {
                      "real_path": "/volume1/photo/travel/example.jpg",
                      "size": 102400, // bytes
                      "owner": { "user": "admin", "group": "users", "uid": 1024, "gid": 100 },
                      "time": { "atime": 1678886400, "mtime": 1678886400, "ctime": 1678886400, "crtime": 1678886400 },
                      "perm": { "acl": { "append": true, "del": true, "exec": false, "read": true, "write": true }, "is_acl_mode": true, "posix": 777 },
                      "type": "file"
                  }
              },
              {
                  "isdir": true,
                  "name": "Subfolder",
                  "path": "/photo/travel/Subfolder",
                  "additional": { ... }
              }
          ],
          "total": 2,
          "offset": 0
      }
  }
  ```
- **失敗回應** (401 Unauthorized / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請先登入 或 獲取檔案列表失敗: 錯誤碼"
  }
  ```

#### 2. 上傳檔案

- **Endpoint**: `POST /api/upload`
- **說明**: 上傳一個或多個檔案到指定的 NAS 路徑。
- **請求 Body** (multipart/form-data):
    - `file`: 要上傳的檔案 (一個或多個)。
    - `path` (string, 必填): 檔案在 NAS 上的目標存放路徑，例如 `/home/uploads`。
    - `overwrite` (string, 可選, 預設 `true`): 如果檔案已存在是否覆蓋，可為 `"true"` 或 `"false"`。
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "message": "上傳成功",
      "data": {
          // Synology API 的原始回應
      }
  }
  ```
- **失敗回應** (400 Bad Request / 401 Unauthorized / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：未選擇檔案 或 上傳失敗: 錯誤碼"
  }
  ```

#### 3. 建立新資料夾

- **Endpoint**: `POST /api/create-folder`
- **說明**: 在指定的 NAS 路徑下建立新的資料夾。
- **請求 Body** (application/json):
  ```json
  {
      "folder_path": "/home/documents", // 父資料夾路徑
      "name": "New Folder Name",      // 新資料夾名稱
      "force_parent": false           // 可選，如果父路徑不存在是否建立，預設 false
  }
  ```
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "message": "資料夾建立成功",
      "data": {
          "folders": [
              {
                  "isdir": true,
                  "name": "New Folder Name",
                  "path": "/home/documents/New Folder Name"
                  // ... 其他 Synology API 回應的詳細資訊
              }
          ]
      }
  }
  ```
- **失敗回應** (400 Bad Request / 401 Unauthorized / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請提供folder_path和name 或 資料夾建立失敗: 錯誤碼"
  }
  ```

#### 4. 刪除檔案/資料夾

- **Endpoint**: `POST /api/delete`
- **說明**: 刪除 NAS 上的指定檔案或資料夾。可以批量刪除。
- **請求 Body** (application/json):
  ```json
  {
      "paths": [
          "/home/documents/file_to_delete.txt",
          "/home/temporary/folder_to_delete"
      ]
  }
  ```
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "message": "刪除成功"
  }
  ```
- **失敗回應** (400 Bad Request / 401 Unauthorized / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請提供要刪除的路徑 或 刪除失敗: 錯誤碼"
  }
  ```

#### 5. 取得下載連結

- **Endpoint**: `GET /api/download`
- **說明**: 獲取指定 NAS 檔案的直接下載連結。此連結通常包含 session 資訊，具有時效性或特定權限。
- **Query 參數**:
    - `path` (string, 必填): 要下載的檔案在 NAS 上的完整路徑，例如 `/photo/image.jpg`。
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "download_url": "NAS_generated_direct_download_link"
  }
  ```
- **失敗回應** (401 Unauthorized / 404 Not Found / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請先登入 或 找不到檔案 或 生成下載連結失敗"
  }
  ```

### 進階功能 (Advanced Features)

#### 1. 建立分享連結

- **Endpoint**: `POST /api/share`
- **說明**: 為 NAS 上的檔案或資料夾建立公開的分享連結。
- **請求 Body** (application/json):
  ```json
  {
      "paths": ["/photo/album_to_share"], // 要分享的檔案/資料夾路徑列表
      "password": "optional_password",    // 可選：分享連結的密碼
      "date_expired": "YYYY-MM-DD",       // 可選：連結過期日期
      "date_available": "YYYY-MM-DD"      // 可選：連結生效日期
  }
  ```
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "data": {
          "links": [
              {
                  "id": "sharing_id_string",
                  "link": "http://your_nas_address/sharing/sharing_id_string",
                  "name": "album_to_share",
                  "path": "/photo/album_to_share",
                  "isFolder": true,
                  "qrcode": "data:image/png;base64,QR_CODE_IMAGE_DATA",
                  // ... 其他 Synology API 回應的詳細資訊
              }
          ]
      }
  }
  ```
- **失敗回應** (400 Bad Request / 401 Unauthorized / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請提供要分享的路徑 或 建立分享連結失敗: 錯誤碼"
  }
  ```

#### 2. 壓縮檔案

- **Endpoint**: `POST /api/compress`
- **說明**: 將指定的檔案或資料夾壓縮成一個壓縮檔。
- **請求 Body** (application/json):
  ```json
  {
      "source_paths": ["/docs/report.docx", "/images/archive_folder"], // 要壓縮的來源檔案/資料夾路徑列表
      "dest_path": "/archives/my_archive.zip", // 壓縮檔的目標存放路徑和名稱
      "options": {                             // 可選：壓縮選項
          "level": "normal",                   // 壓縮等級 (e.g., "low", "normal", "high", "max")
          "mode": "add",                       // 模式 (e.g., "add", "update")
          "format": "zip",                     // 壓縮格式 (e.g., "zip", "7z")
          "password": "optional_archive_password" // 可選：壓縮檔密碼
      }
  }
  ```
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "message": "已開始壓縮任務",
      "task_id": "compression_task_id_from_nas"
  }
  ```
- **失敗回應** (400 Bad Request / 401 Unauthorized / 500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "錯誤訊息，例如：請提供來源路徑和目標路徑 或 壓縮失敗: 錯誤碼"
  }
  ```
  **注意**: 壓縮是一個非同步操作，此 API 僅啟動任務並返回任務 ID。用戶端可能需要另外的機制來查詢任務狀態。

### 系統 (System)

#### 1. 檢視所有 Sessions (調試用)

- **Endpoint**: `GET /api/sessions`
- **說明**: (僅供調試) 獲取目前伺服器上所有 active 和 expired 的 session 資訊。
- **成功回應** (200 OK):
  ```json
  {
      "success": true,
      "total_sessions": 2,
      "sessions": [
          {
              "session_id": "uuid_prefix...",
              "account": "user1_account",
              "login_time": "YYYY-MM-DD HH:MM:SS",
              "last_activity": "YYYY-MM-DD HH:MM:SS",
              "expires_at": "YYYY-MM-DD HH:MM:SS",
              "is_expired": false
          },
          {
              "session_id": "uuid_prefix...",
              "account": "user2_account",
              "login_time": "YYYY-MM-DD HH:MM:SS",
              "last_activity": "YYYY-MM-DD HH:MM:SS",
              "expires_at": "YYYY-MM-DD HH:MM:SS",
              "is_expired": true
          }
      ]
  }
  ```
- **失敗回應** (500 Internal Server Error):
  ```json
  {
      "success": false,
      "error": "獲取 Session 資訊失敗"
  }
  ```

## 錯誤處理

API 錯誤時，回應 Body 會包含 `"success": false` 及一個 `error` 欄位，其中包含錯誤的描述。
HTTP 狀態碼也會反映錯誤的類型：
- `400 Bad Request`: 客戶端請求無效 (例如，缺少必要參數)。
- `401 Unauthorized`: 未登入或 Session 無效。
- `403 Forbidden`: 權限不足。
- `404 Not Found`: 請求的資源不存在。
- `500 Internal Server Error`: 伺服器內部錯誤或 Synology NAS API 返回錯誤。

## 注意事項
-   `session_id` 的管理：用戶端應妥善保存和傳輸 `session_id`，通常透過瀏覽器的 Cookie 機制自動處理。
-   路徑格式：所有檔案和資料夾路徑應使用 Synology NAS 的標準格式 (例如 `/home`, `/photo/MyAlbum`)。
-   Synology API 依賴：本系統許多功能依賴 Synology NAS 提供的 API。若 NAS API 行為變更或不可用，可能會影響本系統功能。 