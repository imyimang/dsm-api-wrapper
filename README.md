# SimpleNAS - Synology NAS 管理系統

一個基於 Flask 的 Synology NAS 檔案管理系統，提供完整的網頁介面和 REST API。

## 主要功能

### 身份驗證
- Synology DSM 帳號登入
- Session 管理（檔案儲存，支援多用戶）
- 自動登入狀態檢查
- Session 過期機制（預設一年）

### 檔案管理
- 目錄瀏覽與導航
- 檔案上傳（支援拖放、多檔案）
- 檔案下載
- 檔案/資料夾刪除
- 建立新資料夾
- ~~檔案壓縮~~

### 分享功能
- 建立分享連結
- 密碼保護
- 過期時間設定
- QR Code 生成（base64 格式）
- 一鍵複製分享連結

### 使用者介面
- 響應式設計（支援手機、平板）
- 現代化 UI 設計
- 麵包屑導航
- 即時操作回饋
- 拖放上傳

## 系統架構

```
SimpleNAS/
├── server.py          # Flask 應用程式主體與工具類別
├── router.py          # API 路由定義
├── run.py             # 啟動腳本
├── test.py            # 測試腳本(需先開啟伺服器)
├── index.html         # 前端網頁應用程式
├── session.json       # Session 持久化儲存檔案
├── README.md          # 專案說明文件
└── API.md             # API 接口說明文件
```

## 技術特色

### 多用戶 Session 管理
- **檔案儲存**：Session 資料持久化到 `session.json`
- **多用戶支援**：同時支援多個用戶登入不同帳號
- **自動過期**：預設一年後自動過期
- **活動追蹤**：記錄最後活動時間
- **自動清理**：啟動時自動清理過期 sessions
- **服務器重啟存活**：服務器重啟後 session 仍然有效

### 安全機制
- 使用 Synology 官方 API
- CSRF Token 驗證
- Session ID 驗證
- 多用戶 Session 隔離
- 自動 Session 過期機制

### 檔案下載優化
- 使用 Synology fbdownload 端點
- 十六進制路徑編碼
- 防止快取機制
- 用戶專屬 Session 驗證

## 快速開始

### 環境需求
- Python 3.7+
- Flask
- requests

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 啟動服務
```bash
python run.py
```

### 訪問應用
- **網頁介面**：http://127.0.0.1:5000/app
- **API 總覽**：http://127.0.0.1:5000/
- **API 文件**：[API.md](API.md)

## 系統配置

### 預設設定
```python
class Config:
    NAS_BASE_URL = "https://your-nas.example.com:5001/webapi/entry.cgi"
    NAS_TIMEOUT = 30
    SESSION_FILE = "session.json"
    SESSION_EXPIRE_DAYS = 365
```

### 環境變數
```bash
# NAS 設定
export NAS_BASE_URL="https://your-nas.example.com:5001/webapi/entry.cgi"
export NAS_TIMEOUT=30

# 服務器設定
export FLASK_HOST="0.0.0.0"
export FLASK_PORT=5000
export FLASK_DEBUG=True

# Session 設定
export SESSION_FILE="session.json"
export SESSION_EXPIRE_DAYS=365
```

## 部署方式

### 標準部署
```bash
git clone https://github.com/your-repo/simpleNAS.git
cd simpleNAS
pip install flask requests
python run.py
```

### Docker 部署
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install flask requests
EXPOSE 5000
VOLUME ["/app/session.json"]
CMD ["python", "run.py"]
```

## 故障排除

### 常見問題

#### Session Hash Invalid
- **原因**：Session 過期或無效
- **解決**：重新登入或檢查 session.json 檔案

#### 下載失敗
- **原因**：Session 過期或路徑編碼問題
- **解決**：檢查登入狀態，確認檔案路徑正確

#### 多用戶衝突
- **原因**：Session 管理錯誤
- **解決**：清除瀏覽器 cookies，檢查 Flask secret_key

## Session 管理說明

### 檔案結構
```json
{
  "session_id": {
    "sid": "Synology Session ID",
    "syno_token": "CSRF Token",
    "login_time": 1748181602.859816,
    "last_activity": 1748181729.356549,
    "expires_at": 1779717602.859816,
    "credentials": {
      "account": "username",
      "password": "password"
    },
    "session_id": "session_id"
  }
}
```

### 管理功能
- 自動載入和儲存
- 過期 session 清理
- 多用戶並發支援
- 活動時間更新

## 授權條款

MIT License - 詳見 LICENSE 檔案

## 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 推送到分支
5. 建立 Pull Request

---

**注意**：本專案僅供學習和內部使用，請確保符合您的安全需求後再部署到生產環境。