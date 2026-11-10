from sqlalchemy import String                                     # 匯入 String，用來設定文字欄位的最大長度
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column # 匯入 ORM 的基底類別與定義欄位的工具


class Base(DeclarativeBase):                                      # 所有資料表的共同父類別，seed.py 可能會用到它
    pass                                                          # 不需要額外內容


class Cup(Base):                                                  # 定義一杯類別，對應資料庫裡的一張表
    __tablename__ = "cups"                                        # 資料庫裡實際的表名稱
    id: Mapped[int] = mapped_column(primary_key=True)             # 編號：主鍵，資料庫自動產生 1、2、3……
    who_order: Mapped[str] = mapped_column(String(100))           # 誰點的：文字，必填          
    drink_name: Mapped[str] = mapped_column(String(100))          # 飲料名稱：文字，必填
    ice: Mapped[str] = mapped_column(String(100))                 # 冰塊：文字，必填
    sugar: Mapped[str] = mapped_column(String(100))               # 糖分：文字，必填
    size: Mapped[str] = mapped_column(String(100))                # 尺寸：文字，必填
    add: Mapped[str | None] = mapped_column(String(100))          # 加料：文字，選填
    price: Mapped[int]                                            # 單杯價格：整數，必填