import json
from server import app

with open("config.json", "r", encoding="utf-8") as f:
    config_data = json.load(f)

HOST = config_data["FLASK"]["HOST"]
PORT = config_data["FLASK"]["PORT"]
DEBUG = config_data["FLASK"]["DEBUG"]

if __name__ == '__main__':
    print("=== DSM Flask API Server ===")
    print("伺服器啟動中...")
    print(f"伺服器地址: http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)