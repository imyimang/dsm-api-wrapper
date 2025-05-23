# Static Files 目錄

## 📁 目錄說明

這個目錄包含網頁應用的靜態文件，主要是 HTML/CSS/JavaScript 前端應用。

## 📄 文件說明

### `index.html`
- 主要的網頁應用文件
- 包含完整的 NAS 管理界面
- 純前端實現，無需額外依賴

## 🚀 部署方式

### 方式一：透過 Flask 應用
```bash
# 啟動 Flask 應用
python run.py

# 訪問網頁應用
http://localhost:5000/app
```

### 方式二：獨立部署
```bash
# 使用任何網頁伺服器提供靜態文件
# 例如使用 Python 內建伺服器
cd static
python -m http.server 8080

# 訪問應用
http://localhost:8080
```

### 方式三：nginx 部署
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/static;
        index index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 自定義配置

### API 端點配置
如果您的 API server 不在同一主機，請修改 `index.html` 中的 baseURL：

```javascript
// 在 NASManager 類別的 constructor 中
constructor() {
    this.baseURL = 'http://your-api-server:5000';  // 修改為您的 API 地址
    // ...
}
```

### 樣式自定義
所有 CSS 樣式都在 `<style>` 標籤中，您可以：
- 修改顏色主題
- 調整佈局大小
- 自定義動畫效果

### 功能擴展
JavaScript 代碼採用模組化設計，容易擴展：
- 添加新的 API 端點支援
- 自定義檔案操作
- 增加新的使用者介面元素

## 📱 跨域問題

如果遇到 CORS 問題，確保：
1. Flask 應用已啟用 CORS (`flask_cors`)
2. API server 配置正確的 CORS 標頭
3. 使用相同的協議和埠號

## 🛡️ 安全注意事項

- 不要在前端硬編碼敏感資訊
- 所有認證都透過 API 處理
- Session 管理完全依賴後端
- 建議在生產環境使用 HTTPS

---

**注意**: 這是一個單頁面應用，所有功能都包含在 `index.html` 中，方便部署和維護。 