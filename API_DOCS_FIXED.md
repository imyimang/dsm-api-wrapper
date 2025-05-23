# Synology DSM API Wrapper - API 文檔 (修正版)

本文檔詳細說明了 Synology DSM API Wrapper 提供的所有 RESTful API 端點。

## 基本資訊

- **Base URL**: `http://localhost:5000` (開發環境)
- **Content-Type**: `application/json`
- **認證方式**: Cookie-based Session (Flask Session)
- **CORS**: 支援跨域請求，需設定 `credentials: 'include'`
- **網頁應用**: `http://localhost:5000/app`

## 修正項目

### 1. 認證方式說明
- ✅ **實際方式**: Cookie-based Session
- ❌ **錯誤說明**: Session-based (需先登入獲取 SID)

### 2. 上傳檔案預設覆蓋設定
- ✅ **實際預設**: `overwrite=true`
- ❌ **文檔錯誤**: 說是 `false`

### 3. 檔案列表回應格式
```json
// ✅ 實際格式 (DSM API 原始結構)
{
  "success": true,
  "data": {
    "files": [
      {
        "name": "example.txt",
        "isdir": false,
        "additional": {
          "size": 1024,
          "time": {...},
          "perm": {...},
          "owner": {...}
        }
      }
    ],
    "offset": 0,
    "total": 1
  }
}

// ❌ 文檔錯誤格式
{
  "data": {
    "files": [...]  // 多了一層包裝
  }
}
```

### 4. 上傳檔案實際回應
```json
// ✅ 實際回應 (DSM API 格式)
{
  "success": true,
  "message": "上傳成功",
  "data": {
    "blSkip": false,
    "file": "example.txt",
    "pid": 12345
  }
}

// ❌ 文檔錯誤格式
{
  "data": {
    "filename": "file.txt",
    "path": "/home/documents/file.txt",
    "size": 1024
  }
}
```

### 5. 錯誤處理實際格式
```json
// ✅ 實際錯誤格式
{
  "success": false,
  "message": "登入失敗：詳細錯誤訊息"
}

// ❌ 文檔顯示但未實現
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "details": "..."
  }
}
```

### 6. 新增的 API 端點
```
GET /api/debug/session - 除錯 Flask session 狀態
```

## 前端使用範例修正

### JavaScript (正確版本)
```javascript
// ✅ 正確方式 - 使用 credentials
fetch('http://localhost:5000/api/login', {
    method: 'POST',
    credentials: 'include',  // 重要！
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        account: 'username',
        password: 'password'
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
```

### cURL 範例修正
```bash
# ✅ 正確的 cookie 處理
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"account":"username","password":"password"}' \
  -c cookies.txt

curl -X GET "http://localhost:5000/api/files?path=/home" \
  -b cookies.txt
```

## 建議
1. 更新原始 API_DOCS.md 文件
2. 統一錯誤處理格式（如果需要）
3. 添加遺漏的 API 端點文檔
4. 強調 Cookie-based 認證的使用方式 