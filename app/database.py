# 匯入連線資料庫需要的工具
# - os：和作業系統溝通，讀環境變數
# - load_dotenv：讀取 .env 檔
# - create_engine：建立資料庫引擎（總機）
# - sessionmaker：建立產生資料庫連線（session）的工廠
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 讀取設定
# 把 .env 檔的內容放進環境變數，再讀出連線網址；沒有設定 DATABASE_URL 就直接啟動失敗
load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

# 建立總機並帶入網址，15 秒內連不到就直接報錯
# pool_pre_ping：每次從連線池拿連線前先試一下，連線已經被切斷（例如 Neon 閒置暫停）就丟掉換一條新的
# 再設定 SessionLocal 工廠：每次呼叫都產生一個新的資料庫連線，並且不自動 flush
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 15}, pool_pre_ping=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine)

# 取得資料庫連線，給 API 的 Depends(get_db) 使用
# - yield 把 db 交給路由函式使用，並暫停在這裡，等路由執行完再回來繼續
# - 不管路由中途有沒有出錯，最後都會跑 finally 把連線關掉
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
