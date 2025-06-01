# DSM-API-Wrapper

一個基於 Flask 的 API 伺服器，用於封裝 Synology DSM 的 NAS API，提供自訂的 REST API 和網頁介面以存取與管理 NAS 檔案。

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

### 訪問應用
- **網頁介面**：http://127.0.0.1:5000/app
- **API 總覽**：http://127.0.0.1:5000/
- **API 文件**：[API.md](API.md)

## 部署

#### 安裝依賴
```bash
pip install -r requirements.txt
```

#### 設定環境變數
1. 複製 `.env.example` 並重新命名為 `.env`
2. 用記事本開啟 `.env` 檔案，修改內容：
```bash
FLASK_SECRET_KEY=your-very-secret-key-change-this-in-production
```

#### 設定 NAS 連線
用記事本開啟 `config.json` 檔案，修改您的 NAS 設定：
```json
{
  "NAS": {
    "NAS_BASE_URL": "https://你的NAS網址.com:5001/webapi/entry.cgi", //EX: "https://cwds.taivs.tp.edu.tw:5001/webapi/entry.cgi"
    "NAS_TIMEOUT": 30
  },
  "SESSION": {
    "SESSION_FILE": "session.json",
    "SESSION_EXPIRE_DAYS": 365
  },
  "FLASK": {
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "DEBUG": false
  }
}
```

**重要設定說明：**
- 將 `您的NAS網址.com` 替換為實際的 NAS 位址
- `HOST` 設為 `127.0.0.1` 僅供本機存取，設為 `0.0.0.0` 可供區網存取
- 生產環境請將 `DEBUG` 設為 `false`
- 根據部屬環境不同，`index.html`測試網頁的`baseURL`參數可能需做更改

#### 啟動服務
```bash
python run.py
```

#### 測試服務
```bash
python test.py
```

#### 使用服務
開啟瀏覽器，前往：
- **網頁介面**：http://127.0.0.1:5000/app
- **API 總覽**：http://127.0.0.1:5000/