# Synology DSM API Wrapper

本專案是一個 Python Flask 實現的 Synology DSM (DiskStation Manager) API 包裝器，提供簡化的 RESTful API 介面來管理 Synology NAS 系統，隱藏了原始 API 的複雜性。

## 功能

### 身份驗證
- DSM 系統登入/登出
- Session 管理和驗證
- 自動 SSL 證書處理

### 檔案管理
- 瀏覽目錄和檔案列表
- 檔案上傳
- 檔案/資料夾刪除
- 任務狀態監控
- 創建資料夾

### 檔案操作
- 檔案壓縮 (ZIP/7Z)
- 下載連結生成
- **檔案分享連結生成** (含 QR Code)
- 完整的錯誤處理

### 系統管理
- 後台任務列表
- Debug 模式切換

### 網頁介面
- 完整的網頁 NAS 管理介面
- 響應式設計，支援各種設備
- 無需額外依賴，純前端實現

## 安裝

### 1. 安裝依賴項

```bash
pip install -r requirements.txt
```

### 2. 啟動伺服器

```bash
python run.py
```

伺服器將在 `http://localhost:5000` 啟動。

### 3. 測試 API

```bash
python test.py
```

## Demo 網站
**提醒: Demo網站還在測試階段，並沒有包含所有支援的API功能**

本專案包含完整的網頁管理介面，提供友善的使用者體驗：

### 訪問方式
- **URL**: `http://localhost:5000/app`
- **功能**: 完整的 NAS 檔案管理界面
- **特色**: 響應式設計，支援手機和桌面設備

### 主要功能
- 登入/登出 NAS 系統
- 瀏覽檔案和資料夾
- 上傳檔案 (支援拖放)
- 下載檔案
- **分享檔案 (含 QR Code)**
- 刪除檔案/資料夾
- 創建資料夾
- ~~壓縮檔案~~
- 即時任務狀態監控

### 部署選項
1. **透過 Flask 應用** (推薦)：直接訪問 `/app` 路由
2. **獨立部署**：使用任何網頁伺服器提供 `static/` 目錄
3. **反向代理**：使用 nginx 等代理伺服器

詳細部署說明請參閱 [static/README.md](static/README.md)。


## 專案結構

```
dsm-api-wrapper/
├── app/                     # 模組化版本主目錄
│   ├── __init__.py          # 應用程式工廠
│   ├── config.py            # 配置設定
│   ├── services/            # 服務層
│   │   ├── __init__.py
│   │   └── nas_service.py   # NAS API 服務類別
│   ├── routes/              # 路由層
│   │   ├── __init__.py
│   │   ├── auth_routes.py   # 身份驗證路由
│   │   ├── file_routes.py   # 檔案管理路由
│   │   └── system_routes.py # 系統管理路由
│   └── utils/               # 工具函數
│       ├── __init__.py
│       └── helpers.py       # 輔助函數
├── static/                  # 網頁應用靜態文件
│   ├── index.html           # 網頁 NAS 管理介面
│   └── README.md            # 靜態文件部署說明
├── run.py                   # 應用程式啟動文件
├── test.py                  # 測試套件
├── test_tasks.py            # 任務測試
├── requirements.txt         # Python 依賴項
├── README.md                # 本專案說明
├── API_DOCS.md              # 詳細 API 文檔
├── LICENSE                  # 授權條款
├── Dockerfile               # Docker 配置
└── .gitignore               # Git 忽略設定
```

## API 概覽

本專案提供以下主要 API 端點：

### 身份驗證
- `POST /api/login` - 登入 NAS 系統
- `POST /api/logout` - 登出系統
- `GET /api/session/check` - 檢查 Session 狀態

### 檔案管理
- `GET /api/files` - 獲取檔案列表
- `POST /api/upload` - 上傳檔案
- `DELETE /api/delete` - 刪除檔案/資料夾
- `GET /api/delete/status/<taskid>` - 查詢刪除任務狀態
- `POST /api/folder` - 建立新資料夾

### 檔案操作
- `POST /api/compress` - 壓縮檔案/資料夾
- `GET /api/download` - 生成下載連結
- `POST /api/share` - 建立分享連結 (含 QR Code)

### 系統管理
- `GET /api/tasks` - 獲取後台任務列表
- `POST /api/debug/toggle` - 切換 Debug 模式

### 網頁應用
- `GET /app` - 訪問網頁 NAS 管理介面
- `GET /static/<filename>` - 靜態資源文件

> 📖 **詳細 API 文檔**: 請參閱 [API_DOCS.md](API_DOCS.md) 獲取完整的 API 使用說明、請求/回應範例、錯誤代碼等詳細資訊。

## 測試
### 自動測試
```bash
python test.py
```

### 手動測試
1. 啟動伺服器: `python run.py`
2. 訪問 API 文檔: `http://localhost:5000/`
3. 訪問網頁介面: `http://localhost:5000/app`
4. 使用任何 HTTP 客戶端測試端點

## 文檔
- **[API 詳細文檔](API_DOCS.md)** - 完整的 API 端點說明

## 參考資料

- [Synology API 官方文檔](https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf)


