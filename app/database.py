import os                                  #匯入os套件來和電腦的作業系統溝通
from dotenv import load_dotenv             #匯入dotenv套件來準備讀取env檔
from sqlalchemy import create_engine       #匯入sqlalchemy套件來建立資料庫引擎
from sqlalchemy.orm import sessionmaker    #匯入orm套件來讓資料庫順利溝通

load_dotenv()                              #把env檔存入環境變數讓os讀它
DATABASE_URL= os.environ["DATABASE_URL"]   #讀取env裡面的url，並將其存入DATABASE_URL變數中

    
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})   #建立總機帶入url，5秒內連不到直接報錯

SessionLocal = sessionmaker(autoflush=False, bind=engine) #設定sessionLocal工廠的行為和總機

def get_db():               #建立一個函式來取得資料庫連線
    db = SessionLocal()     #設定執行的簡稱
    try:                    #若在db執行過程中發生錯誤，會跳到finally裡面去關閉資料庫連線
        yield db            #把db交給呼叫這個函式的地方，並且暫停這個函式的執行，等到呼叫這個函式的地方執行完畢後再回到這裡繼續執行
    finally:           
        db.close()          #關閉資料庫連線