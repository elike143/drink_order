# 匯入需要的工具
# - FastAPI：建立 API；Depends：取得資料庫連線或共用的前置工作；Query：取得查詢參數
# - HTTPException：回傳錯誤訊息；StaticFiles：提供靜態檔案；FileResponse：回傳首頁的 HTML 檔
# - select：組 SQL 查詢；Session：資料庫連線的型別
# - Literal：限制查詢參數只能是幾個固定值
# - 專案自己的資料庫連線、資料表（models）、菜單與計價函式、資料格式（schemas）
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

# 啟動時的準備工作
# - 建立資料庫表格（已經存在的表不會被修改）
# - 把資料庫的菜單同步成 app/menus/ 裡的內容
# - 建立名叫 Drink Order API 的 app，網址 /static 開頭的請求都去 app/static 資料夾找檔案
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_menu(db)

app = FastAPI(title="Drink Order API")
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")


# ---------- 共用函式 ----------

# 依網址上的 order_id 找訂單，找不到回 404
# 需要訂單的路由用 Depends(get_order) 共用這段；同一個請求裡的 Depends(get_db) 會拿到同一個連線
def get_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張訂單")
    return order


# 用 cup_price 計算一杯的價格（飲料價格加上加料）
# 規則不允許時（例如只有 M 杯卻點 L、得正點波霸）cup_price 會丟 ValueError，這裡轉成 400 和原因
def calc_price(item: MenuItem, size: str, toppings: list[str]) -> int:
    try:
        return cup_price(item, size, toppings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 把資料存進資料庫並回傳
# refresh 之後才拿得到資料庫產生的欄位，例如 id、開單時間
def save(db: Session, obj):
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ---------- 頁面 ----------

# 首頁：不用查資料庫，直接把網頁送給瀏覽器
@app.get("/")
def home():
    return FileResponse("app/static/index.html")


# ---------- 菜單 ----------

# 看有哪些店家可以選：從菜單表拿出所有店名，去掉重複、照名字排序，例如 ["五十嵐", "得正"]
@app.get("/shops", response_model=list[str])
def list_shops(db: Session = Depends(get_db)):
    return db.scalars(select(MenuItem.shop).distinct().order_by(MenuItem.shop)).all()


# 看某家店的菜單，例如 /menu?shop=五十嵐
# 只拿這家店的品項並照菜單順序排列；這家店沒有菜單就回 404
@app.get("/menu", response_model=list[MenuItemOut])
def list_menu(shop: str, db: Session = Depends(get_db)):
    items = db.scalars(select(MenuItem).where(MenuItem.shop == shop).order_by(MenuItem.id)).all()
    if not items:
        raise HTTPException(status_code=404, detail="找不到這家店的菜單")
    return items


# 試算一杯飲料多少錢，例如 /price?shop=五十嵐&drink=珍珠奶茶&size=L&toppings=布丁
# - toppings 在網址裡可以重複出現，代表多種加料
# - 用店名和品名找出這杯飲料，菜單上沒有就回 404
# - 和新增一杯用同一個 calc_price 計價，規則不允許時回 400 和原因
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

# 看所有訂單
# scalars() 把每一筆資料轉成 Order 物件，all() 全部放進 list，再由 OrderOut 決定回傳格式
@app.get("/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order)).all()


# 開一張新訂單，成功回 201，並回傳含 id 和開單時間的訂單
@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    return save(db, Order(**data.model_dump()))


# 結單：任何人都可以結單；找不到訂單回 404，結單後回傳這張訂單最新的樣子
@app.post("/orders/{order_id}/close", response_model=OrderOut)
def close_order(order: Order = Depends(get_order), db: Session = Depends(get_db)):
    order.is_open = False
    return save(db, order)


# 刪除整張訂單：任何人都可以刪，找不到回 404
# 先把這張單裡的每一杯標記刪除（否則外鍵會擋住刪除訂單），再標記訂單本身，最後一次 commit 真正刪掉，回 204
@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order: Order = Depends(get_order), db: Session = Depends(get_db)):
    for cup in order.cups:
        db.delete(cup)
    db.delete(order)
    db.commit()


# ---------- 飲料 ----------

# 看某張訂單裡的所有飲料：找不到訂單回 404，找到就回傳它底下的每一杯
@app.get("/orders/{order_id}/cups", response_model=list[CupOut])
def list_cups_in_order(order: Order = Depends(get_order)):
    return order.cups


# 新增一杯飲料，成功回 201
# 1. 找不到訂單回 404；訂單已經結單回 400
# 2. 在這家店的菜單裡找這杯飲料，菜單上沒有就回 400
# 3. 店家規則：菜單標 ◆ 的飲料不能做熱飲；得正的奶蓋系列固定少冰
# 4. 價格只信任後端，由 calc_price 計算，規則不允許時回 400 和原因
# 5. 前端資料加上算好的價格和訂單編號存進資料庫
@app.post("/orders/{order_id}/cups", response_model=CupOut, status_code=201)
def create_cup(data: CupCreate, order: Order = Depends(get_order), db: Session = Depends(get_db)):
    if not order.is_open:
        raise HTTPException(status_code=400, detail="這張訂單已經關閉，不能再點")

    item = db.scalar(select(MenuItem).where(MenuItem.shop == order.shop_name, MenuItem.name == data.drink_name))
    if item is None:
        raise HTTPException(status_code=400, detail="菜單上沒有這杯飲料")

    if data.ice == "熱飲" and not item.hot_ok:
        raise HTTPException(status_code=400, detail="這杯飲料不建議做熱飲")
    if item.category == "Cheese MILK FOAM" and data.ice != "少冰":
        raise HTTPException(status_code=400, detail="奶蓋系列固定少冰")

    price = calc_price(item, data.size, data.toppings)
    return save(db, Cup(**data.model_dump(), price=price, order_id=order.id))


# 刪除一杯：任何人都可以刪，但已經結單就不能刪
# - 用主鍵找這杯，找不到或這杯不屬於網址上的訂單回 404
# - 這杯所屬的訂單已經結單回 400
# - 刪掉之後回 204（成功，但沒有內容要回傳）
@app.delete("/orders/{order_id}/cups/{cup_id}", status_code=204)
def delete_cup(order_id: int, cup_id: int, db: Session = Depends(get_db)):
    cup = db.get(Cup, cup_id)
    if not cup or cup.order_id != order_id:
        raise HTTPException(status_code=404, detail="找不到這杯飲料")
    order = db.get(Order, order_id)
    if order is None or not order.is_open:
        raise HTTPException(status_code=400, detail="已經結單，不能刪除")
    db.delete(cup)
    db.commit()
