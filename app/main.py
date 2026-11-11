from fastapi import FastAPI,Depends    #匯入 FastAPI 來建立 API，匯入 Depends 來取得資料庫連線
from sqlalchemy import select          #匯入 select 來查詢資料庫
from sqlalchemy.orm import Session     #匯入 Session 來取得資料庫連線
from app.database import get_db ,engine , SessionLocal       #匯入 get_db 來取得資料庫連線，匯入 engine 來建立資料庫表格
from app.schemas import CupOut, CupCreate, OrderCreate, OrderOut, MenuItemOut   #匯入 schemas 來定義資料格式       
from app.models import Base,Cup,Order,MenuItem   #匯入 models 來定義資料表      
from fastapi.exceptions import HTTPException #匯入 HTTPException 來回傳錯誤訊息
from fastapi.staticfiles import StaticFiles
from app.menu_data import seed_menu  #匯入 menu_data 來建立菜單
from app.menu_data import seed_menu, topping_price, PAID_TOPPINGS   # 多匯入加料價格表和計算函式

Base.metadata.create_all(bind=engine)                #建立資料庫表格
app = FastAPI(title = "Drink Order API")             #做一個名字叫Drink Order API的API存進app裡
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")   # 網址 /static 開頭的請求，都去 app/static 資料夾找檔案

# 建立菜單
with SessionLocal() as db:
    seed_menu(db)

@app.get("/orders", response_model=list[OrderOut])    # 公告:有人要看所有訂單，找下面的店員
def list_orders(db: Session = Depends(get_db)):       # 店員:拿到資料庫鑰匙 db
    return db.scalars(select(Order)).all()            # 傳回所有訂單，scalars() 會把每一筆資料庫物件轉成 OrderOut，all() 會把所有資料庫物件放進 list 裡  

@app.post("/orders", response_model=OrderOut, status_code=201) # 公告:新增一筆全班的空白訂單，找下面的店員；成功回傳 201
def create_order(data: OrderCreate, db: Session = Depends(get_db)):# 店員:拿到客人的點單 OrderCreate，和資料庫鑰匙 db
    order = Order(**data.model_dump())                              # 把點單 data 轉成一筆可以存進資料庫的 Order
    db.add(order)                                                    # 放進暫存區
    db.commit()                                                     # 正式存進資料庫
    db.refresh(order)                                                # 去資料庫拿回最新的樣子，這時才有 id
    return order                                                     # 把存好的這筆訂單回傳給客人

@app.get("/orders/{order_id}/cups", response_model=list[CupOut])  # 公告：有人要看某張訂單的所有飲料，找下面的店員
def list_cups_in_order(order_id: int, db: Session = Depends(get_db)):  # 店員：拿到客人的點單 order_id，和資料庫鑰匙 db
    order = db.get(Order, order_id)                 # 先去資料庫找這張訂單
    if not order:                                   # 如果找不到
        raise HTTPException(status_code=404, detail="找不到這張訂單")  # 回傳 404 給客人
    return order.cups                               # 回傳這張訂單的所有飲料

@app.post("/orders/{order_id}/cups", response_model=CupOut, status_code=201)   # 公告：有人要新增一杯飲料，找下面的店員；成功回傳 201
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
    price = (item.price_m if data.size == "M" else item.price_l) + topping_price(order.shop_name, data.add)   # 飲料價格加上要錢的加料
    cup = Cup(**data.model_dump(exclude={"price"}), price=price, order_id=order_id)   # 不用前端送來的價格，換成菜單價格
    db.add(cup)                                    # 放進暫存區
    db.commit()                                    # 正式存進資料庫
    db.refresh(cup)                                # 去資料庫拿回最新的樣子，這時才有 id
    return cup                                     # 把存好的這杯回傳給客人

@app.post("/orders/{order_id}/close", response_model=OrderOut)  # 公告：有人要關閉訂單，找下面的店員
def close_order(order_id: int, db: Session = Depends(get_db)):  # 店員：拿到客人的點單 order_id，和資料庫鑰匙 db
    order = db.get(Order, order_id)                 # 先去資料庫找這張訂單
    if not order:                                   # 如果找不到
        raise HTTPException(status_code=404, detail="找不到這張訂單")  # 回傳 404 給客人
    order.is_open = False                           # 把這張訂單關閉
    db.commit()                                     # 正式存進資料庫
    db.refresh(order)                               # 去資料庫拿回最新的樣子
    return order                                    # 把存好的這張訂單回傳給客人

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

@app.get("/toppings")                                             # 公告：有人要看某家店哪些加料要加錢
def list_toppings(shop: str):                                     # shop 是查詢參數：/toppings?shop=五十嵐；這支不用查資料庫
    prices = PAID_TOPPINGS.get(shop, {})                          # 拿出這家店的加料價格，沒有就是空的
    return [{"name": name, "price": price} for name, price in prices.items()]   # 轉成 [{"name": "布丁", "price": 15}, ...]