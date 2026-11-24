# 匯入需要的工具
# - FastAPI：建立 API；Depends：取得資料庫連線；Query：取得查詢參數；Response：回傳沒有內容的 204
# - HTTPException：回傳錯誤訊息；StaticFiles：提供靜態檔案；FileResponse：回傳首頁的 HTML 檔
# - select：組 SQL 查詢；Session：資料庫連線的型別
# - Literal：限制查詢參數只能是幾個固定值
# - 專案自己的資料庫連線、資料格式（schemas）、資料表（models）、菜單與計價函式
from typing import Literal
from fastapi import FastAPI, Depends, Query, Response
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db, engine, SessionLocal
from app.schemas import CupOut, CupCreate, OrderCreate, OrderOut, MenuItemOut
from app.models import Base, Cup, Order, MenuItem
from app.menus.menu_data import seed_menu, cup_price

# 啟動時的準備工作
# - 建立資料庫表格（已經存在的表不會被修改）
# - 建立名叫 Drink Order API 的 app
# - 網址 /static 開頭的請求，都去 app/static 資料夾找檔案
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Drink Order API")
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

# 首頁：不用查資料庫，直接把網頁送給瀏覽器
@app.get("/")
def home():
    return FileResponse("app/static/index.html")

# 建立菜單：把資料庫的菜單同步成 app/menus/ 裡的內容
with SessionLocal() as db:
    seed_menu(db)

# 看所有訂單
# scalars() 把每一筆資料轉成 Order 物件，all() 全部放進 list，再由 OrderOut 決定回傳格式
@app.get("/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order)).all()

# 看某張訂單裡的所有飲料：找不到訂單回 404，找到就回傳它底下的每一杯
@app.get("/orders/{order_id}/cups", response_model=list[CupOut])
def list_cups_in_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張訂單")
    return order.cups

# 新增一杯飲料，成功回 201
# 1. 找不到訂單回 404；訂單已經結單回 400
# 2. 在這家店的菜單裡找這杯飲料，菜單上沒有就拒絕
# 3. 店家規則：菜單標 ◆ 的飲料不能做熱飲；得正的奶蓋系列固定少冰
# 4. 價格由後端用 cup_price 計算（飲料價格加上加料），規則不允許（例如只有 M 杯卻點 L、得正點波霸）時回 400 和原因
# 5. 前端資料加上算好的價格和訂單編號存進資料庫，refresh 之後才拿得到 id
@app.post("/orders/{order_id}/cups", response_model=CupOut, status_code=201)
def create_cup(order_id: int, data: CupCreate, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張訂單")
    if not order.is_open:
        raise HTTPException(status_code=400, detail="這張訂單已經關閉，不能再點")
    item = db.scalar(select(MenuItem).where(MenuItem.shop == order.shop_name, MenuItem.name == data.drink_name))
    if item is None:
        raise HTTPException(status_code=400, detail="菜單上沒有這杯飲料")
    if data.ice == "熱飲" and not item.hot_ok:
        raise HTTPException(status_code=400, detail="這杯飲料不建議做熱飲")
    if item.category == "Cheese MILK FOAM" and data.ice != "少冰":
        raise HTTPException(status_code=400, detail="奶蓋系列固定少冰")
    try:
        price = cup_price(item, data.size, data.toppings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    cup = Cup(**data.model_dump(), price=price, order_id=order_id)
    db.add(cup)
    db.commit()
    db.refresh(cup)
    return cup

# 結單：任何人都可以結單；找不到訂單回 404，結單後回傳這張訂單最新的樣子
@app.post("/orders/{order_id}/close", response_model=OrderOut)
def close_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張訂單")
    order.is_open = False
    db.commit()
    db.refresh(order)
    return order

# 看某家店的菜單，例如 /menu?shop=五十嵐
# 只拿這家店的品項並照菜單順序排列；這家店沒有菜單就回 404
@app.get("/menu", response_model=list[MenuItemOut])
def list_menu(shop: str, db: Session = Depends(get_db)):
    items = db.scalars(
        select(MenuItem).where(MenuItem.shop == shop).order_by(MenuItem.id)
    ).all()
    if not items:
        raise HTTPException(status_code=404, detail="找不到這家店的菜單")
    return items

# 看有哪些店家可以選：從菜單表拿出所有店名，去掉重複、照名字排序，例如 ["五十嵐", "得正"]
@app.get("/shops", response_model=list[str])
def list_shops(db: Session = Depends(get_db)):
    return db.scalars(
        select(MenuItem.shop).distinct().order_by(MenuItem.shop)
    ).all()

# 試算一杯飲料多少錢，例如 /price?shop=五十嵐&drink=珍珠奶茶&size=L&toppings=布丁
# - toppings 在網址裡可以重複出現，代表多種加料
# - 用店名和品名找出這杯飲料，菜單上沒有就回 404
# - 和新增一杯用同一個 cup_price 計價，規則不允許時回 400 和原因
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
    try:
        price = cup_price(item, size, toppings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"price": price}

# 開一張新訂單，成功回 201；refresh 之後才拿得到 id 和資料庫填好的開單時間
@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    order = Order(**data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

# 刪除整張訂單：任何人都可以刪
# 找不到回 404；先把這張單裡的每一杯標記刪除，再標記訂單本身，最後一次 commit 真正刪掉，回 204
@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="找不到這張訂單")
    for cup in order.cups:
        db.delete(cup)
    db.delete(order)
    db.commit()
    return Response(status_code=204)

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
    if not order.is_open:
        raise HTTPException(status_code=400, detail="已經結單，不能刪除")
    db.delete(cup)
    db.commit()
    return Response(status_code=204)
