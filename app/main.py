from fastapi import FastAPI,Depends     
from sqlalchemy import select,func
from sqlalchemy.orm import Session      
from app.database import get_db ,engine       
from app.schemas import CupOut, CupCreate          
from app.models import Base,Cup         
from fastapi.exceptions import HTTPException


Max_Cup = 60

Base.metadata.create_all(bind=engine)                #建立資料庫表格
app = FastAPI(title = "Drink Order API")             #做一個名字叫Drink Order API的API存進app裡

@app.get("/cups", response_model=list[CupOut])       # 門牌：有人要看所有飲料，交給下面的函式
def list_cups(db: Session = Depends(get_db)):        # 函式：FastAPI 會先準備好資料庫連線 db 再交給它
    return db.scalars(select(Cup)).all()             # 去資料庫拿出所有飲料，回傳出去

@app.post("/cups", response_model=CupOut, status_code=201)   # 公告：有人要新增一杯飲料，找下面的店員；成功回傳 201
def create_cup(data: CupCreate, db: Session = Depends(get_db)):   # 店員：拿到客人的點單 data，和資料庫鑰匙 db
    count_cup = db.scalar(select(func.count()).select_from(Cup)) # 檢查目前飲料數量是否已達上限 
    if count_cup >= Max_Cup:
        raise HTTPException(status_code=400, detail="Maximum number of cups reached")
    
    cup = Cup(**data.model_dump())                 # 把點單 data 轉成一杯可以存進資料庫的 Cup
    db.add(cup)                                    # 放進暫存區
    db.commit()                                    # 正式存進資料庫
    db.refresh(cup)                                # 去資料庫拿回最新的樣子，這時才有 id
    return cup                                     # 把存好的這杯回傳給客人