from typing import Literal                                # 匯入 Literal，用來限制「只能是這幾個值」
from pydantic import BaseModel, Field, ConfigDict         # 匯入 Pydantic 的 BaseModel（資料格式的父類別）  、 Field（設定檢查條件）、 ConfigDict（設定模型行為）


class CupCreate(BaseModel):                                  # 同學新增一杯時送來的資料格式
    who_order: str = Field(min_length=1, max_length=10)      # 誰點的：必填，至少 1 個字（不能空白）、最多 10 字      
    drink_name: str = Field(min_length=1, max_length=100)    # 飲料名：至少 1 個字（不能空白）、最多 100 字
    ice: Literal["正常", "半冰", "微冰", "完全去冰"]           # 冰塊：只能是這四個值之一，送其他值會被拒絕
    sugar: Literal["無糖", "微糖", "半糖", "七分糖", "全糖"]   # 糖分：只能是這五個值之一，送其他值會被拒絕
    size: Literal["小杯", "中杯", "大杯"]                     # 尺寸：只能是這三個值之一，送其他值會被拒絕
    add: str | None = Field(default=None, max_length=100)    # 加料：選填，沒送就是 None；有送最多 100 字
    price: int = Field(ge=1, le=200)                         # 價格：整數，必須 >=1 且 <= 200（le = 小於等於）

class CupOut(CupCreate):                                     # API 回傳時，每一杯存好的飲料的格式
    id: int                                                  # 編號：整數，必填
    model_config = ConfigDict(from_attributes=True)          # 允許用.去物件取值