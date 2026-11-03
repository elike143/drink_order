def get_price(menu, name):                             # 定義函式：從菜單字典中查詢某品項的價格
    return menu[name]                                  # 用品名當 key 取值；如果品名不存在會丟出 KeyError

def order_total(menu, items):                          # 定義函式：計算一張訂單的總金額
    return sum(get_price(menu, i) for i in items)      # 對每個品項查價格並加總

menu = {"紅茶": 30, "綠茶": 30}                         # 建立一個只有兩個品項的簡易菜單
print(order_total(menu, ["紅茶", "奶茶"]))               # 計算訂單總額，但「奶茶」不在菜單裡，會觸發錯誤