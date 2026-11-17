from fastapi import FastAPI,Depends,Query    # 匯入 FastAPI 來建立 API，匯入 Depends 來取得資料庫連線，匯入 Query 來取得查詢參數
from sqlalchemy import select          #匯入 select 來查詢資料庫
from sqlalchemy.orm import Session     #匯入 Session 來取得資料庫連線
from app.database import get_db ,engine , SessionLocal       #匯入 get_db 來取得資料庫連線，匯入 engine 來建立資料庫表格
from app.schemas import CupOut, CupCreate, OrderCreate, OrderOut, MenuItemOut,OrderCreated,CupCreated   #匯入 schemas 來定義資料格式       
from app.models import Base,Cup,Order,MenuItem   #匯入 models 來定義資料表      
from fastapi.exceptions import HTTPException #匯入 HTTPException 來回傳錯誤訊息
from fastapi.staticfiles import StaticFiles
from app.menus.menu_data import seed_menu, cup_price   # 匯入建立菜單、計算一杯總價的函式
from typing import Literal                            # 匯入 Literal，限制查詢參數只能是幾個固定值

## 管理碼、刪除碼
from fastapi import Header, Response              # Header：從請求的 header 拿值；Response：回傳沒有內容的 204
import secrets                                    # 產生隨機的管理碼，以及安全地比對
from fastapi.responses import FileResponse        # 回傳一個檔案，給首頁用
import os                                         # 讀環境變數

ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]           # 網站管理者的萬用鑰匙：可以結任何一張單
def token_ok(given: str | None, expected: str | None) -> bool:   # 檢查送來的碼對不對
    return bool(given and expected and secrets.compare_digest(given, expected))   # 兩個都要有值，而且一模一樣才算對

Base.metadata.create_all(bind=engine)                #建立資料庫表格
app = FastAPI(title = "Drink Order API")             #做一個名字叫Drink Order API的API存進app裡
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")   # 網址 /static 開頭的請求，都去 app/static 資料夾找檔案
@app.get("/")                                     # 有人打開網站首頁
def home():                                       # 不用查資料庫
    return FileResponse("app/static/index.html")  # 直接把網頁送給瀏覽器

# 建立菜單
with SessionLocal() as db:
    seed_menu(db)

@app.get("/orders", response_model=list[OrderOut])    # 公告:有人要看所有訂單，找下面的店員
def list_orders(db: Session = Depends(get_db)):       # 店員:拿到資料庫鑰匙 db
    return db.scalars(select(Order)).all()            # 傳回所有訂單，scalars() 會把每一筆資料庫物件轉成 OrderOut，all() 會把所有資料庫物件放進 list 裡  

@app.get("/orders/{order_id}/cups", response_model=list[CupOut])  # 公告：有人要看某張訂單的所有飲料，找下面的店員
def list_cups_in_order(order_id: int, db: Session = Depends(get_db)):  # 店員：拿到客人的點單 order_id，和資料庫鑰匙 db
    order = db.get(Order, order_id)                 # 先去資料庫找這張訂單
    if not order:                                   # 如果找不到
        raise HTTPException(status_code=404, detail="找不到這張訂單")  # 回傳 404 給客人
    return order.cups                               # 回傳這張訂單的所有飲料

@app.post("/orders/{order_id}/cups", response_model=CupCreated, status_code=201)   # 公告：有人要新增一杯飲料，找下面的店員；成功回傳 201
def create_cup(order_id: int, data: CupCreate, db: Session = Depends(get_db)):   # 店員：拿到客人的點單 data，和資料庫鑰匙 db   
    order = db.get(Order, order_id)                 # 先去資料庫找這張訂單
    if not order:                                   # 如果找不到
        raise HTTPException(status_code=404, detail="找不到這張訂單")  # 回傳 404 給客人
    if not order.is_open:                            # 如果這張訂單已經關閉
        raise HTTPException(status_code=400, detail="這張訂單已經關閉，不能再點")  # 回傳 400 給客人
    item = db.scalar(select(MenuItem).where(MenuItem.shop == order.shop_name, MenuItem.name == data.drink_name))   # 在這家店的菜單裡找這杯飲料
    if item is None:                                                  # 菜單上沒有這杯
        raise HTTPException(status_code=400, detail="菜單上沒有這杯飲料")   # 拒絕
    if data.ice == "熱飲" and not item.hot_ok:                        # 菜單標 ◆ 的飲料卻點熱飲
        raise HTTPException(status_code=400, detail="這杯飲料不建議做熱飲")   # 拒絕
    if item.category == "Cheese MILK FOAM" and data.ice != "少冰":    # 得正的奶蓋系列菜單規定固定少冰
        raise HTTPException(status_code=400, detail="奶蓋系列固定少冰")   # 拒絕
    try:                                                              # 算價格時可能遇到店家規則不允許的情況
        price = cup_price(item, data.size, data.toppings)             # 飲料價格加上加料，規則都在 cup_price 裡
    except ValueError as e:                                           # 例如只有 M 杯卻點 L、得正點波霸
        raise HTTPException(status_code=400, detail=str(e))           # 照規則拒絕，回 400 和原因
    cup = Cup(**data.model_dump(exclude={"price"}), price=price, order_id=order_id, delete_token=secrets.token_urlsafe(24))   # 多存一串隨機的刪除碼
    db.add(cup)                                    # 放進暫存區
    db.commit()                                    # 正式存進資料庫
    db.refresh(cup)                                # 去資料庫拿回最新的樣子，這時才有 id
    return cup                                     # 把存好的這杯回傳給客人

@app.post("/orders/{order_id}/close", response_model=OrderOut)   # 結單：開單的人或網站管理者都可以
def close_order(
    order_id: int,                                               # 網址裡的訂單編號
    x_manage_token: str | None = Header(default=None),           # 開單的人：瀏覽器自動帶的管理碼
    x_admin_token: str | None = Header(default=None),            # 網站管理者：萬用鑰匙
    db: Session = Depends(get_db),                               # 資料庫鑰匙
):
    order = db.get(Order, order_id)                              # 先找這張訂單
    if not order:                                                # 找不到
        raise HTTPException(status_code=404, detail="找不到這張訂單")   # 回 404
    is_owner = token_ok(x_manage_token, order.manage_token)      # 是不是開單的人
    is_admin = token_ok(x_admin_token, ADMIN_TOKEN)              # 是不是網站管理者
    if not (is_owner or is_admin):                               # 兩個都不是
        raise HTTPException(status_code=403, detail="只有開單的人可以結單")   # 回 403
    order.is_open = False                                        # 把訂單關閉
    db.commit()                                                  # 存進資料庫
    db.refresh(order)                                            # 拿回最新的樣子
    return order                                                 # 回傳這張訂單

@app.get("/menu", response_model=list[MenuItemOut])               # 公告：有人要看某家店的菜單
def list_menu(shop: str, db: Session = Depends(get_db)):          # shop 是查詢參數：/menu?shop=五十嵐
    items = db.scalars(                                           # 執行查詢
        select(MenuItem).where(MenuItem.shop == shop).order_by(MenuItem.id)   # 只要這家店的品項，照菜單順序
    ).all()                                                       # 全部放進 list
    if not items:                                                 # 這家店沒有菜單
        raise HTTPException(status_code=404, detail="找不到這家店的菜單")   # 回傳 404
    return items                                                  # 回傳菜單

@app.get("/shops", response_model=list[str])                      # 公告：有人要看有哪些店家可以選
def list_shops(db: Session = Depends(get_db)):                    # 只需要資料庫鑰匙
    return db.scalars(                                            # 執行查詢
        select(MenuItem.shop).distinct().order_by(MenuItem.shop)  # 從菜單表拿出所有店名，去掉重複，照名字排序
    ).all()                                                       # 全部放進 list，例如 ["五十嵐"]

@app.get("/price")                                                        # 公告：有人要試算一杯飲料多少錢
def get_price(                                                            # 店員：試算價格
    shop: str,                                                            # 查詢參數：哪家店，例如 ?shop=五十嵐
    drink: str,                                                           # 查詢參數：哪杯飲料
    size: Literal["M", "L"],                                              # 查詢參數：M 或 L
    toppings: list[str] = Query(default=[]),                              # 查詢參數：加料清單，網址裡可以重複出現
    db: Session = Depends(get_db),                                        # 資料庫鑰匙
):
    item = db.scalar(select(MenuItem).where(MenuItem.shop == shop, MenuItem.name == drink))   # 用店名和品名，從菜單表查出這杯飲料
    if item is None:                                                      # 菜單上沒有這杯
        raise HTTPException(status_code=404, detail="菜單上沒有這杯飲料")   # 回傳 404
    try:                                                                  # 算價格時可能遇到店家規則不允許的情況
        price = cup_price(item, size, toppings)                           # 飲料本身的價格 + 加料的價格，和新增一杯用同一個函式
    except ValueError as e:                                               # 例如只有 M 杯卻點 L、得正點波霸
        raise HTTPException(status_code=400, detail=str(e))               # 回 400 和原因，不再變成 500
    return {"price": price}     

@app.post("/orders", response_model=OrderCreated, status_code=201)    # 開單成功的回應會多一個管理碼
def create_order(data: OrderCreate, db: Session = Depends(get_db)):   # 拿到客人的點單和資料庫鑰匙
    order = Order(**data.model_dump(), manage_token=secrets.token_urlsafe(24))   # 建立訂單，同時產生一串隨機的管理碼
    db.add(order)                                                     # 放進暫存區
    db.commit()                                                       # 存進資料庫
    db.refresh(order)                                                 # 拿回最新的樣子，這時才有 id
    return order                                                      # 回傳訂單和管理碼

@app.delete("/orders/{order_id}", status_code=204)               # 刪除整張訂單，裡面的飲料一起刪
def delete_order(
    order_id: int,                                               # 網址裡的訂單編號
    x_manage_token: str | None = Header(default=None),           # 從 header 的 X-Manage-Token 拿管理碼
    db: Session = Depends(get_db),                               # 資料庫鑰匙
):
    order = db.get(Order, order_id)                              # 找這張訂單
    if not order:                                                # 找不到
        raise HTTPException(status_code=404, detail="找不到這張訂單")   # 回 404
    if not order.manage_token or not x_manage_token or not secrets.compare_digest(x_manage_token, order.manage_token):   # 沒有管理碼或不對
        raise HTTPException(status_code=403, detail="只有開單的人可以刪單")   # 回 403
    for cup in order.cups:                                       # 這張單裡的每一杯
        db.delete(cup)                                           # 先標記刪除
    db.delete(order)                                             # 再標記刪除訂單本身
    db.commit()                                                  # 一次真正刪掉
    return Response(status_code=204)                             # 回 204

@app.delete("/orders/{order_id}/cups/{cup_id}", status_code=204)   # 刪除一杯；成功回 204：成功，但沒有內容要回傳
def delete_cup(
    order_id: int,                                               # 網址裡的訂單編號
    cup_id: int,                                                 # 網址裡的飲料編號
    x_delete_token: str | None = Header(default=None),           # 從 header 的 X-Delete-Token 拿刪除碼
    db: Session = Depends(get_db),                               # 資料庫鑰匙
):
    cup = db.get(Cup, cup_id)                                    # 用主鍵找這杯
    if not cup or cup.order_id != order_id:                      # 找不到，或這杯不屬於網址上的訂單
        raise HTTPException(status_code=404, detail="找不到這杯飲料")   # 回 404
    order = db.get(Order, order_id)                              # 找這杯所屬的訂單
    if not order.is_open:                                        # 已經結單
        raise HTTPException(status_code=400, detail="已經結單，不能刪除")   # 回 400
    if not cup.delete_token or not x_delete_token or not secrets.compare_digest(x_delete_token, cup.delete_token):   # 沒有刪除碼或不對
        raise HTTPException(status_code=403, detail="只能刪除自己點的飲料")   # 回 403
    db.delete(cup)                                               # 從暫存區標記刪除
    db.commit()                                                  # 真正從資料庫刪掉
    return Response(status_code=204)  