from sqlalchemy import String, DateTime  # 匯入 String、DateTime 來設定文字最大長度、時間欄位
from sqlalchemy import func ,ForeignKey #匯入 func,ForeignKey 來使用 SQL 的函式和外鍵
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column # 匯入 ORM 的基底類別與定義欄位的工具
from sqlalchemy.orm import relationship #匯入 relationship 來建立關聯
from datetime import datetime #匯入datetime來處理時間

class Base(DeclarativeBase):                                      # 所有資料表的共同父類別
    pass                                                          # 不需要額外內容

class Order(Base):                                         # 定義下訂類別
    __tablename__ = "orders"                               # 表名
    id: Mapped[int] = mapped_column(primary_key=True)    # 主鍵
    shop_name: Mapped[str] = mapped_column(String(50))  # 文字欄位
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())  # 開單時間：由資料庫在新增時自動填入
    is_open: Mapped[bool] = mapped_column(default=True) #判斷是否收單
    cups: Mapped[list["Cup"]] = relationship()    # 關聯：這張訂單底下的所有杯，SQLAlchemy 會透過外鍵 order_id 自動找出來

class Cup(Base):                                                  # 定義一杯類別，對應資料庫裡的一張表
    __tablename__ = "cups"                                        # 資料庫裡實際的表名稱
    id: Mapped[int] = mapped_column(primary_key=True)             # 編號：主鍵，資料庫自動產生 1、2、3……
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))   # 外鍵：這杯屬於哪張訂單，值必須是 orders 表裡存在的 id
    who_order: Mapped[str] = mapped_column(String(100))           # 誰點的：文字，必填          
    drink_name: Mapped[str] = mapped_column(String(100))          # 飲料名稱：文字，必填
    ice: Mapped[str] = mapped_column(String(100))                 # 冰塊：文字，必填
    sugar: Mapped[str] = mapped_column(String(100))               # 糖分：文字，必填
    size: Mapped[str] = mapped_column(String(100))                # 尺寸：文字，必填
    add: Mapped[str | None] = mapped_column(String(100))          # 加料：文字，選填
    price: Mapped[int]                                            # 單杯價格：整數，必填

class MenuItem(Base):                                             # 菜單品項，一筆是一種飲料
    __tablename__ = "menu_items"                                  # 資料庫裡的表名
    id: Mapped[int] = mapped_column(primary_key=True)             # 編號：主鍵
    shop: Mapped[str] = mapped_column(String(50), index=True)     # 哪一家店；加索引，用店名查比較快
    category: Mapped[str] = mapped_column(String(20))             # 菜單分類，例如「找好茶」
    name: Mapped[str] = mapped_column(String(50))                 # 品名
    price_m: Mapped[int]                                          # M 杯價格
    price_l: Mapped[int]                                          # L 杯價格
    hot_ok: Mapped[bool] = mapped_column(default=True)            # 可不可以做熱飲；菜單標 ◆ 的是 False