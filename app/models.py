# 匯入定義資料表需要的工具
# - String、DateTime：設定文字最大長度、時間欄位
# - UniqueConstraint：設定多個欄位合起來不能重複
# - func、ForeignKey：使用 SQL 的函式（例如 now()）、設定外鍵
# - DeclarativeBase、Mapped、mapped_column：ORM 的基底類別與定義欄位的工具
# - relationship：建立資料表之間的關聯
# - datetime：處理時間
# - ARRAY：PostgreSQL 的陣列型別，讓一格可以存一個清單
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

# 所有資料表的共同父類別，不需要額外內容
class Base(DeclarativeBase):
    pass

# 訂單資料表 orders
# - id：主鍵，資料庫自動產生
# - shop_name：店家名稱
# - created_at：開單時間，由資料庫在新增時自動填入
# - is_open：是否還在收單，預設是 True
# - cups：這張訂單底下的所有杯，SQLAlchemy 會透過外鍵 order_id 自動找出來
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_name: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_open: Mapped[bool] = mapped_column(default=True)
    cups: Mapped[list["Cup"]] = relationship()

# 每一杯飲料的資料表 cups
# - id：主鍵，資料庫自動產生 1、2、3……
# - order_id：外鍵，這杯屬於哪張訂單，值必須是 orders 表裡存在的 id
#   加索引：PostgreSQL 不會自動幫外鍵建索引，查「某張單的所有杯」時才不用掃整張表
# - who_order、drink_name、ice、sugar、size：誰點的、飲料名稱、冰塊、糖分、尺寸，都是必填文字
# - add：備註，選填，例如「茶味重」
# - toppings：加料，直接存成清單，沒加料就是空清單
# - price：單杯價格，由後端計算，必填
class Cup(Base):
    __tablename__ = "cups"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    who_order: Mapped[str] = mapped_column(String(100))
    drink_name: Mapped[str] = mapped_column(String(100))
    ice: Mapped[str] = mapped_column(String(100))
    sugar: Mapped[str] = mapped_column(String(100))
    size: Mapped[str] = mapped_column(String(100))
    add: Mapped[str | None] = mapped_column(String(100))
    toppings: Mapped[list[str]] = mapped_column(ARRAY(String(10)), default=list)
    price: Mapped[int]

# 菜單品項資料表 menu_items，一筆是一種飲料
# - shop：哪一家店
# - category：菜單分類，例如「找好茶」
# - name：品名
# - price_m、price_l：M 杯、L 杯價格；L 是 None 代表只有 M 杯
# - hot_ok：可不可以做熱飲，菜單標 ◆ 的是 False
# 同一家店不能有兩筆同名品項：(shop, name) 設唯一限制，重複的資料在寫入時就會被資料庫擋下
# 唯一限制會自動建立 (shop, name) 的索引，點單、試算用店名加品名查、/menu 只用店名查都用得到，所以 shop 不用另外加索引
class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (UniqueConstraint("shop", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    shop: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(50))
    price_m: Mapped[int]
    price_l: Mapped[int | None]
    hot_ok: Mapped[bool] = mapped_column(default=True)
