from sqlalchemy import select                          # select 用來組查詢
from sqlalchemy.orm import Session                      # 資料庫 session 的型別標註
from app.models import MenuItem                         # 菜單品項的資料表
from app.menus.fifty_lan import FIFTY_LAN_MENU                      # 從 fifty_lan.py 拿五十嵐菜單
from app.menus.de_zheng import DE_ZHENG_MENU, DE_ZHENG_TOPPINGS     # 從 de_zheng.py 拿得正菜單和加料價格

MENUS = {"五十嵐": FIFTY_LAN_MENU, "得正": DE_ZHENG_MENU}            # 店名 → 菜單，對應只寫一次

def seed_menu(db: Session) -> None:                     # 讓資料庫的菜單跟 MENUS 裡每一家店一致
    for shop, menu in MENUS.items():                    # 一家店一家店處理，例如 ("五十嵐", FIFTY_LAN_MENU)
        existing = {                                    # 先把資料庫裡這家店的品項全部拿出來，用品名當索引
            item.name: item                             # 品名 → 那一筆 MenuItem
            for item in db.scalars(select(MenuItem).where(MenuItem.shop == shop))   # SELECT * FROM menu_items WHERE shop = 這家店
        }                                               # 字典結束
        names_in_file = set()                           # 記錄檔案裡這家店有哪些品名，等一下判斷要刪哪些
        for c, n, m, l, h in menu:                      # 這家店的品項一筆一筆看
            names_in_file.add(n)                        # 記下這個品名
            item = existing.get(n)                      # 資料庫有沒有同名的品項，沒有會拿到 None
            if item is None:                            # 資料庫沒有：新品項
                db.add(MenuItem(shop=shop, category=c, name=n, price_m=m, price_l=l, hot_ok=h))   # 新增，店名用迴圈的 shop
            else:                                       # 資料庫已經有
                item.category = c                       # 更新分類
                item.price_m = m                        # 更新 M 價格
                item.price_l = l                        # 更新 L 價格（可能是 None）
                item.hot_ok = h                         # 更新能不能熱飲
        for name, item in existing.items():             # 資料庫裡這家店的品項一筆一筆看
            if name not in names_in_file:               # 檔案裡已經沒有這個品名
                db.delete(item)                         # 從資料庫刪掉
    db.commit()                                         # 所有店都處理完，一次存進資料庫：中途出錯就整批不存

TEAS = {"茉莉綠茶", "阿薩姆紅茶", "四季春青茶", "黃金烏龍"}   # 純茶，加珍波椰 M+5 L+10
TOPPING_ADD_TOPPING = {"找口感", "招牌特調"}   # 有料，加珍波椰 +10


def get_topping_group(category, name):   # 給它分類和品名，回傳標籤
    if name in TEAS:                # 如果品名在純茶名單裡
        return "純茶"                         # 就回傳"純茶"
    if category in TOPPING_ADD_TOPPING :          # 如果分類是找口感或招牌特調
        return "有料"                     # 就回傳"有料"
    return "一般"                          # 都沒有符合回傳"一般"

def topping_price(shop, category, name, size, toppings):   # 算這杯的加料要多收多少：店名、分類、品名、杯型、加料清單
    total = 0                                         # 從 0 開始算
    if shop == "得正":                                 # 得正的規則很單純
        for topping in toppings:                      # 加的料一個一個看
            if topping not in DE_ZHENG_TOPPINGS:      # 得正沒有這種料，例如波霸
                raise ValueError(f"得正沒有{topping}")   # 交給呼叫的人轉成 400
            total += DE_ZHENG_TOPPINGS[topping]       # 查表加錢，一律 +10
        return total                                  # 回傳得正的加料總價
    group = get_topping_group(category, name)         # 以下是五十嵐：先貼標籤，例如 "純茶"
    for topping in toppings:                          # 加的料一個一個看
        if topping in {"布丁", "冰淇淋"}:              # 布丁或冰淇淋
            total += 15                               # 不管哪種飲料都 +15
        elif topping in {"珍珠", "波霸", "椰果"}:      # 珍波椰
            if group == "純茶":                       # 純茶
                total += 5 if size == "M" else 10      # M 杯 +5 L 杯 +10
            elif group == "有料":                      # 有料
                total += 10                            # 不管 M L 都 +10
        else:                                         # 五十嵐沒有的料，例如黃金珍珠
            raise ValueError(f"五十嵐沒有{topping}")   # 交給呼叫的人轉成 400
    return total                                      # 回傳加料總共多少

def cup_price(item, size, toppings):                  # 一杯的總價：菜單品項、杯型、加料清單；新增一杯和試算都用它
    if size == "L":                                   # 點大杯
        if item.price_l is None:                      # 這杯沒有 L 的價格
            raise ValueError(f"{item.name}只有 M 杯")   # 交給呼叫的人轉成 400
        base = item.price_l                           # 飲料本身用 L 價格
    else:                                             # 點中杯
        base = item.price_m                           # 飲料本身用 M 價格
    return base + topping_price(item.shop, item.category, item.name, size, toppings)   # 飲料價格 + 加料價格；店名直接從品項拿