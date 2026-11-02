from sqlalchemy import func, select                    # func 用來做 COUNT，select 用來組查詢
from app.database import SessionLocal, engine          # 引入 session 工廠與連線引擎
from app.models import Base, MenuItem                  # 引入資料表基底類別與菜單模型

SEED_ITEMS = [                                         # 預設菜單，每筆是（品名, 分類, 價格）
    ("紅茶", "茶類", 30),                               # 品項 1
    ("綠茶", "茶類", 30),                               # 品項 2
    ("烏龍茶", "茶類", 35),                             # 品項 3
    ("茉莉綠茶", "茶類", 35),                           # 品項 4
    ("珍珠奶茶", "奶茶類", 55),                         # 品項 5
    ("紅茶拿鐵", "奶茶類", 55),                         # 品項 6
    ("烏龍拿鐵", "奶茶類", 60),                         # 品項 7
    ("黑糖鮮奶", "鮮奶類", 65),                         # 品項 8
    ("檸檬綠茶", "果茶類", 50),                         # 品項 9
    ("百香雙響炮", "果茶類", 60),                       # 品項 10
    ("柳橙綠茶", "果茶類", 60),                         # 品項 11
    ("冬瓜檸檬", "果茶類", 45),                         # 品項 12
]


def main():                                            # 主流程函式
    Base.metadata.create_all(engine)                   # 依 models.py 建立所有尚未存在的資料表
    with SessionLocal() as db:                         # 開啟一個 session，離開區塊時自動關閉
        count = db.scalar(select(func.count()).select_from(MenuItem))   # 查詢菜單目前有幾筆
        if count:                                      # 如果已經有資料
            print(f"菜單已有 {count} 筆，略過寫入")      # 提示並跳過，避免重複寫入
            return                                     # 結束函式
        db.add_all(                                    # 一次加入多筆資料
            MenuItem(name=n, category=c, price=p) for n, c, p in SEED_ITEMS   # 把每個三元組轉成菜單物件
        )
        db.commit()                                    # 提交交易，真正寫進資料庫
        print(f"已寫入 {len(SEED_ITEMS)} 筆菜單")        # 顯示寫入筆數


if __name__ == "__main__":                             # 只有直接執行這個檔案時才會進入
    main()                                             # 執行主流程