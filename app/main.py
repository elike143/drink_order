from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, get_db
from app.menus.menu_data import cup_price, seed_menu
from app.models import Base, Cup, MenuItem, Order
from app.schemas import CupCreate, CupOut, MenuItemOut, OrderCreate, OrderOut

# 啟動時：建表、同步菜單、掛上前端頁面
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_menu(db)

app = FastAPI(title="Drink Order API")
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")


# ---------- 共用函式 ----------

def get_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    """依網址的 order_id 找訂單，找不到回 404。給需要訂單的路由用 Depends 共用。"""
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張訂單")
    return order


def calc_price(item: MenuItem, size: str, toppings: list[str]) -> int:
    """呼叫 cup_price 計價；店家規則不允許時，把 ValueError 轉成 400。"""
    try:
        return cup_price(item, size, toppings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def save(db: Session, obj):
    """存進資料庫，再拿回資料庫產生的欄位（id、開單時間）。"""
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ---------- 頁面 ----------

@app.get("/")
def home():
    return FileResponse("app/static/index.html")


# ---------- 菜單 ----------

@app.get("/shops", response_model=list[str])
def list_shops(db: Session = Depends(get_db)):
    return db.scalars(select(MenuItem.shop).distinct().order_by(MenuItem.shop)).all()


@app.get("/menu", response_model=list[MenuItemOut])
def list_menu(shop: str, db: Session = Depends(get_db)):
    items = db.scalars(select(MenuItem).where(MenuItem.shop == shop).order_by(MenuItem.id)).all()
    if not items:
        raise HTTPException(status_code=404, detail="找不到這家店的菜單")
    return items


@app.get("/price")
def get_price(
    shop: str,
    drink: str,
    size: Literal["M", "L"],
    toppings: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    item = db.scalar(select(MenuItem).where(MenuItem.shop == shop, MenuItem.name == drink))
    if item is None:
        raise HTTPException(status_code=404, detail="菜單上沒有這杯飲料")
    return {"price": calc_price(item, size, toppings)}


# ---------- 訂單 ----------

@app.get("/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order)).all()


@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    return save(db, Order(**data.model_dump()))


@app.post("/orders/{order_id}/close", response_model=OrderOut)
def close_order(order: Order = Depends(get_order), db: Session = Depends(get_db)):
    order.is_open = False
    return save(db, order)


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order: Order = Depends(get_order), db: Session = Depends(get_db)):
    for cup in order.cups:  # 先刪底下的每一杯，否則外鍵會擋住刪除訂單
        db.delete(cup)
    db.delete(order)
    db.commit()


# ---------- 飲料 ----------

@app.get("/orders/{order_id}/cups", response_model=list[CupOut])
def list_cups_in_order(order: Order = Depends(get_order)):
    return order.cups


@app.post("/orders/{order_id}/cups", response_model=CupOut, status_code=201)
def create_cup(data: CupCreate, order: Order = Depends(get_order), db: Session = Depends(get_db)):
    if not order.is_open:
        raise HTTPException(status_code=400, detail="這張訂單已經關閉，不能再點")

    item = db.scalar(select(MenuItem).where(MenuItem.shop == order.shop_name, MenuItem.name == data.drink_name))
    if item is None:
        raise HTTPException(status_code=400, detail="菜單上沒有這杯飲料")

    # 店家規則：標 ◆ 的飲料不做熱飲；得正奶蓋系列固定少冰
    if data.ice == "熱飲" and not item.hot_ok:
        raise HTTPException(status_code=400, detail="這杯飲料不建議做熱飲")
    if item.category == "Cheese MILK FOAM" and data.ice != "少冰":
        raise HTTPException(status_code=400, detail="奶蓋系列固定少冰")

    price = calc_price(item, data.size, data.toppings)  # 價格只信任後端
    return save(db, Cup(**data.model_dump(), price=price, order_id=order.id))


@app.delete("/orders/{order_id}/cups/{cup_id}", status_code=204)
def delete_cup(order_id: int, cup_id: int, db: Session = Depends(get_db)):
    cup = db.get(Cup, cup_id)
    if not cup or cup.order_id != order_id:
        raise HTTPException(status_code=404, detail="找不到這杯飲料")
    if not db.get(Order, order_id).is_open:
        raise HTTPException(status_code=400, detail="已經結單，不能刪除")
    db.delete(cup)
    db.commit()