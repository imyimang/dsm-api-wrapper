from server import app
from server import session_manager,Config

if __name__ == '__main__':
    print("=== SimpleNAS Flask API Server ===")
    print("伺服器啟動中...")
    print("網頁介面: http://127.0.0.1:5000/app")
    print("API 文檔: http://127.0.0.1:5000/")
    print(f"Session 檔案: {Config.SESSION_FILE}")
    print(f"Session 過期時間: {Config.SESSION_EXPIRE_DAYS} 天")
    print("=====================================")
    
    # 顯示現有 sessions 資訊
    sessions_info = session_manager.get_all_sessions_info()
    if sessions_info:
        print(f"現有 Sessions: {len(sessions_info)} 個")
        for info in sessions_info:
            print(f"  - {info['session_id']} ({info['account']}) - 最後活動: {info['last_activity']}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
