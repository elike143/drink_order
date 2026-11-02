from fastapi import Depends, FastAPI                   # FastAPI 主類別與依賴注入工具
from sqlalchemy import select                          # 組 SQL 查詢用
from sqlalchemy.orm import Session                     # session 的型別標註，讓編輯器能提示
from app.database import get_db                        # 取得資料庫 session 的依賴函式
from app.models import MenuItem                        # 菜單資料表模型

app = FastAPI(title="Drink Order API")                 # 建立應用程式，title 會顯示在 /docs 頁面


@app.get("/health")                                    # 註冊 GET /health 路由，用來檢查服務是否活著
def health():                                          # 路由處理函式
    return {"status": "ok"}                            # 回傳 JSON，之後 Docker 健康檢查會用到


@app.get("/menu")                                      # 註冊 GET /menu 路由，取得上架中的菜單
def get_menu(db: Session = Depends(get_db)):           # 透過依賴注入拿到一個資料庫 session
    items = db.scalars(                                # 執行查詢並取回物件
        select(MenuItem)                               # 查詢菜單資料表
        .where(MenuItem.is_active.is_(True))           # 只取上架中的品項
        .order_by(MenuItem.category, MenuItem.id)      # 先依分類、再依編號排序
    )
    return [                                           # 把每個物件轉成 JSON 可用的字典
        {"id": m.id, "name": m.name, "category": m.category, "price": m.price}   # 只回傳前端需要的欄位
        for m in items                                 # 逐筆處理查詢結果
    ]