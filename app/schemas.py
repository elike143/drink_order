# 匯入定義資料格式需要的工具
# - Literal：限制「只能是這幾個值」
# - BaseModel：Pydantic 資料格式的父類別；Field：設定檢查條件；ConfigDict：設定模型行為
# - datetime：處理時間
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# 開單時送來的資料格式
# - shop_name：店家名，必填，1～50 個字（不能空白）
class OrderCreate(BaseModel):
    shop_name: str = Field(min_length=1, max_length=50)

# API 回傳訂單的格式：繼承 OrderCreate，再加上 id、開單時間、是否收單
# from_attributes=True 允許直接從資料庫的 Order 物件取值
class OrderOut(OrderCreate):
    id: int
    created_at: datetime
    is_open: bool
    model_config = ConfigDict(from_attributes=True)

# 點一杯時送來的資料格式，送不符合的值會被拒絕（422）
# - who_order：誰點的，1～10 個字
# - drink_name：飲料名，1～100 個字
# - ice：冰塊，只能是 正常冰／少冰／去冰／熱飲
# - sugar：糖分，只能是 正常／9分／少糖／半糖／微糖／無糖
# - size：尺寸，只能是 M 或 L
# - add：備註，選填，最多 100 字
# - toppings：加料，可複選；前五種是五十嵐、後兩種是得正，哪家店能加什麼由 cup_price 檢查
# 前端送來的 price 不在這裡，會被忽略，價格一律由後端計算
class CupCreate(BaseModel):
    who_order: str = Field(min_length=1, max_length=10)
    drink_name: str = Field(min_length=1, max_length=100)
    ice: Literal["正常冰", "少冰", "去冰", "熱飲"]
    sugar: Literal["正常", "9分", "少糖", "半糖", "微糖", "無糖"]
    size: Literal["M", "L"]
    add: str | None = Field(default=None, max_length=100)
    toppings: list[Literal["珍珠", "波霸", "椰果", "布丁", "冰淇淋", "黃金珍珠", "焙烏龍茶凍"]] = Field(default=[])

# API 回傳每一杯飲料的格式：繼承 CupCreate，再加上 id、所屬訂單、後端算好的價格
# from_attributes=True 允許直接從資料庫的 Cup 物件取值
class CupOut(CupCreate):
    id: int
    order_id: int
    price: int
    model_config = ConfigDict(from_attributes=True)

# API 回傳菜單品項的格式：編號、店名、分類、品名、M／L 價格（L 可能沒有）、可不可以做熱飲
# from_attributes=True 允許直接從資料庫的 MenuItem 物件取值
class MenuItemOut(BaseModel):
    id: int
    shop: str
    category: str
    name: str
    price_m: int
    price_l: int | None
    hot_ok: bool
    model_config = ConfigDict(from_attributes=True)
