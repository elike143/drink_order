# 匯入需要的工具
# - select：組查詢；Session：資料庫連線的型別標註；MenuItem：菜單品項的資料表
# - 各家店的菜單：五十嵐菜單、得正菜單和得正的加料價格
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import MenuItem
from app.menus.fifty_lan import FIFTY_LAN_MENU
from app.menus.de_zheng import DE_ZHENG_MENU, DE_ZHENG_TOPPINGS

# 店名 → 菜單，對應只寫在這裡一次
MENUS = {"五十嵐": FIFTY_LAN_MENU, "得正": DE_ZHENG_MENU}

# 讓資料庫的菜單跟 MENUS 裡每一家店一致，一家店一家店處理：
# 1. 先把資料庫裡這家店的品項全部拿出來，做成「品名 → MenuItem」的字典
# 2. 檔案裡的品項一筆一筆看（c 分類、n 品名、m M 價、l L 價、h 能不能熱飲），並記下出現過的品名
#    - 資料庫沒有同名的：新增
#    - 資料庫已經有：更新分類、M／L 價格（L 可能是 None）、能不能熱飲
# 3. 資料庫裡有、但檔案裡已經沒有的品名：從資料庫刪掉
# 4. 所有店都處理完才一次 commit，中途出錯就整批不存
def seed_menu(db: Session) -> None:
    for shop, menu in MENUS.items():
        existing = {
            item.name: item
            for item in db.scalars(select(MenuItem).where(MenuItem.shop == shop))
        }
        names_in_file = set()
        for c, n, m, l, h in menu:
            names_in_file.add(n)
            item = existing.get(n)
            if item is None:
                db.add(MenuItem(shop=shop, category=c, name=n, price_m=m, price_l=l, hot_ok=h))
            else:
                item.category = c
                item.price_m = m
                item.price_l = l
                item.hot_ok = h
        for name, item in existing.items():
            if name not in names_in_file:
                db.delete(item)
    db.commit()

# 五十嵐加料計價用的分組
# - TEAS：純茶，加珍波椰 M +5、L +10
# - TOPPING_ADD_TOPPING：本身就有料的分類，加珍波椰一律 +10
TEAS = {"茉莉綠茶", "阿薩姆紅茶", "四季春青茶", "黃金烏龍"}
TOPPING_ADD_TOPPING = {"找口感", "招牌特調"}

# 給分類和品名，回傳五十嵐的加料分組：品名在純茶名單裡是「純茶」，分類是找口感或招牌特調是「有料」，其他都是「一般」
def get_topping_group(category, name):
    if name in TEAS:
        return "純茶"
    if category in TOPPING_ADD_TOPPING:
        return "有料"
    return "一般"

# 算這杯的加料要多收多少錢（店名、分類、品名、杯型、加料清單）
# - 得正：每種料查 DE_ZHENG_TOPPINGS，一律 +10；得正沒有的料（例如波霸）丟 ValueError
# - 五十嵐：先用 get_topping_group 分組，再一個一個料看
#   - 布丁、冰淇淋：不管哪種飲料都 +15
#   - 珍珠、波霸、椰果：純茶 M +5、L +10；有料 +10；一般不加錢
#   - 五十嵐沒有的料（例如黃金珍珠）丟 ValueError
# 丟出的 ValueError 由呼叫的路由轉成 400
def topping_price(shop, category, name, size, toppings):
    total = 0
    if shop == "得正":
        for topping in toppings:
            if topping not in DE_ZHENG_TOPPINGS:
                raise ValueError(f"得正沒有{topping}")
            total += DE_ZHENG_TOPPINGS[topping]
        return total
    group = get_topping_group(category, name)
    for topping in toppings:
        if topping in {"布丁", "冰淇淋"}:
            total += 15
        elif topping in {"珍珠", "波霸", "椰果"}:
            if group == "純茶":
                total += 5 if size == "M" else 10
            elif group == "有料":
                total += 10
        else:
            raise ValueError(f"五十嵐沒有{topping}")
    return total

# 一杯的總價（菜單品項、杯型、加料清單），新增一杯和試算價格都用它
# - 點 L：用 L 價格，這杯沒有 L 價格就丟 ValueError（由路由轉成 400）
# - 點 M：用 M 價格
# - 最後加上加料價格，店名直接從品項拿
def cup_price(item, size, toppings):
    if size == "L":
        if item.price_l is None:
            raise ValueError(f"{item.name}只有 M 杯")
        base = item.price_l
    else:
        base = item.price_m
    return base + topping_price(item.shop, item.category, item.name, size, toppings)
