from fastapi import FastAPI,Depends     
from sqlalchemy import select
from sqlalchemy.orm import Session      
from app.database import get_db ,engine       
from app.schemas import CupOut, CupCreate, OrderCreate, OrderOut          
from app.models import Base,Cup,Order         
from fastapi.exceptions import HTTPException

Base.metadata.create_all(bind=engine)                #建立資料庫表格
app = FastAPI(title = "Drink Order API")             #做一個名字叫Drink Order API的API存進app裡

@app.get("/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order)).all()

@app.post("/orders", response_model=OrderOut, status_code=201) # 公告:新增一筆全班的空白訂單，找下面的店員；成功回傳 201
def create_order(data: OrderCreate, db: Session = Depends(get_db)):# 店員:拿到客人的點單 data，和資料庫鑰匙 db
    order = Order(**data.model_dump())                              # 把點單 data 轉成一筆可以存進資料庫的 Order
    db.add(order)                                                    # 放進暫存區
    db.commit()                                                     # 正式存進資料庫
    db.refresh(order)                                                # 去資料庫拿回最新的樣子，這時才有 id
    return order                                                     # 把存好的這筆訂單回傳給客人

@app.get("/cups", response_model=list[CupOut])       # 門牌：有人要看所有飲料，交給下面的函式
def list_cups(db: Session = Depends(get_db)):        # 函式：FastAPI 會先準備好資料庫連線 db 再交給它
    return db.scalars(select(Cup)).all()             # 去資料庫拿出所有飲料，回傳出去

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
    cup = Cup(**data.model_dump(), order_id=order_id)                 # 把點單 data 轉成一杯可以存進資料庫的 Cup
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