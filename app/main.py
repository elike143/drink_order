from fastapi import Depends, FastAPI, HTTPException                   # FastAPI 主類別與依賴注入工具
from sqlalchemy import select                          # 組 SQL 查詢用
from sqlalchemy.orm import Session                     # session 的型別標註，讓編輯器能提示
from app.database import get_db                        # 取得資料庫 session 的依賴函式
from app.models import MenuItem, Order, OrderItem                        # 菜單資料表模型
from pydantic import BaseModel

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

class OrderItemCreate(BaseModel):                                 # 訂單明細的輸入資料模型
    menu_item_id: int                                  # 菜單品項編號
    quantity: int                                      # 杯數
    sugar: str                                         # 甜度
    ice: str                                           # 冰塊

class OrderCreate(BaseModel):
  customer_name: str
  items: list[OrderItemCreate]

@app.post("/orders")
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
  # 1. 檢查顧客名稱與明細是否為空
  if not order_in.items:
    raise HTTPException(status_code=400, detail="訂單不能沒有品項")

  total_amount = 0
  order_items_to_save = []

  # 2. 驗證每一個點餐品項，並計算總金額
  for item_in in order_in.items:
    menu_item = db.get(MenuItem, item_in.menu_item_id)
    if not menu_item or not menu_item.is_active:
      raise HTTPException(
          status_code=400, detail=f"品項 ID {item_in.menu_item_id} 不存在或已下架"
      )

    subtotal = menu_item.price * item_in.quantity
    total_amount += subtotal

    # 建立 OrderItem 物件
    order_item = OrderItem(
        menu_item_id=menu_item.id,
        quantity=item_in.quantity,
        unit_price=menu_item.price,
        sugar=item_in.sugar,
        ice=item_in.ice,
    )
    order_items_to_save.append(order_item)

  # 3. 建立 Order 主檔
  new_order = Order(
      customer_name=order_in.customer_name,
      total=total_amount,
      status="pending",
      items=order_items_to_save,  # 透過關聯自動寫入明細
  )

  # 4. 寫入資料庫
  db.add(new_order)
  db.commit()
  db.refresh(new_order)

  return {
      "message": "訂單建立成功",
      "order_id": new_order.id,
      "total": new_order.total,
  }