from datetime import datetime                          # 日期時間型別，給 created_at 欄位使用
from sqlalchemy import ForeignKey, String, DateTime, func   # 外鍵、字串長度型別、時間型別、SQL 函式
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship   # ORM 的基底類別與欄位工具


class Base(DeclarativeBase):                           # 所有資料表類別的共同父類別
    pass                                               # 不需要額外內容


class MenuItem(Base):                                  # 菜單品項資料表
    __tablename__ = "menu_items"                       # 資料庫裡實際的資料表名稱
    id: Mapped[int] = mapped_column(primary_key=True)  # 主鍵，自動遞增的品項編號
    name: Mapped[str] = mapped_column(String(50))      # 品名，最長 50 字
    category: Mapped[str] = mapped_column(String(30))  # 分類，例如茶類、奶茶類
    price: Mapped[int] = mapped_column()                        # 價格，新台幣整數，不用小數
    is_active: Mapped[bool] = mapped_column(default=True)   # 是否上架；下架用這個欄位，不刪資料


class Order(Base):                                     # 訂單主表
    __tablename__ = "orders"                           # 資料表名稱
    id: Mapped[int] = mapped_column(primary_key=True)  # 訂單編號
    customer_name: Mapped[str] = mapped_column(String(30))   # 訂購人姓名或暱稱
    status: Mapped[str] = mapped_column(String(20), default="pending")   # 訂單狀態，預設待處理
    total: Mapped[int]                                 # 訂單總金額
    created_at: Mapped[datetime] = mapped_column(      # 建立時間欄位
        DateTime(timezone=True), server_default=func.now())   # 帶時區，由資料庫自動填入當下時間
    items: Mapped[list["OrderItem"]] = relationship(   # 一張訂單對應多筆明細的關聯
        back_populates="order", cascade="all, delete-orphan")   # 雙向關聯；刪除訂單時連同明細一起刪


class OrderItem(Base):                                 # 訂單明細表
    __tablename__ = "order_items"                      # 資料表名稱
    id: Mapped[int] = mapped_column(primary_key=True)  # 明細編號
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))   # 指向所屬訂單
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))   # 指向所點的品項
    quantity: Mapped[int]                              # 杯數
    unit_price: Mapped[int]                            # 下單當下的單價，之後菜單調價也不影響歷史訂單
    sugar: Mapped[str] = mapped_column(String(10))     # 甜度
    ice: Mapped[str] = mapped_column(String(10))       # 冰塊
    order: Mapped["Order"] = relationship(back_populates="items")   # 反向關聯回所屬訂單
