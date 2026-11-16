DE_ZHENG_MENU = [                                       # 得正菜單：(分類, 品名, M 價格, L 價格, 可不可以做熱飲)；L 是 None 代表只有 M 杯
    ("Original TEA", "紅茶", 25, 30, True),             # 原味茶 1，分類標 ♥ 可調整為熱飲
    ("Original TEA", "綠茶", 25, 30, True),             # 原味茶 2
    ("Original TEA", "春烏龍", 30, 35, True),           # 原味茶 3，# 茶師推薦
    ("Original TEA", "輕烏龍", 30, 35, True),           # 原味茶 4，# 茶師推薦
    ("Original TEA", "焙烏龍", 30, 35, True),           # 原味茶 5，# 茶師推薦
    ("Double FRUIT", "檸檬春烏龍", 55, 65, False),      # 果茶 1，分類沒有 ♥，不可熱飲；# 茶師推薦
    ("Double FRUIT", "香橙春烏龍", 60, 70, False),      # 果茶 2，# 茶師推薦
    ("Double FRUIT", "甘蔗春烏龍", 60, 70, False),      # 果茶 3，# 茶師推薦
    ("Double FRUIT", "青梅春烏龍", 50, 60, False),      # 果茶 4
    ("Double FRUIT", "優酪春烏龍", 55, 65, False),      # 果茶 5
    ("Double FRUIT", "雙柚金烏龍", 55, 65, False),      # 果茶 6
    ("Cheese MILK FOAM", "芝士奶蓋春烏龍", 50, 60, False),   # 奶蓋 1，奶蓋固定少冰；# 茶師推薦
    ("Cheese MILK FOAM", "芝士奶蓋焙烏龍", 50, 60, False),   # 奶蓋 2，# 茶師推薦
    ("Cheese MILK FOAM", "芝士奶蓋阿華田", 55, 65, False),   # 奶蓋 3
    ("Cheese MILK FOAM", "芝士奶蓋烘吉茶", 55, 65, False),   # 奶蓋 4
    ("Classic MILK TEA", "奶茶", 45, 50, True),         # 奶茶 1，分類標 ♥ 可調整為熱飲
    ("Classic MILK TEA", "焙烏龍奶茶", 45, 50, True),   # 奶茶 2，# 茶師推薦
    ("Classic MILK TEA", "珍珠奶茶", 55, 60, True),     # 奶茶 3
    ("Classic MILK TEA", "黃金珍珠奶綠", 55, 60, True), # 奶茶 4，# 茶師推薦
    ("Classic MILK TEA", "烘吉奶茶", 50, None, True),   # 奶茶 5，菜單只有 M 欄有價格
    ("Fresh MILK", "紅茶鮮奶", 55, 65, True),           # 鮮奶 1，分類標 ♥ 可調整為熱飲；# 茶師推薦
    ("Fresh MILK", "輕烏龍鮮奶", 55, 65, True),         # 鮮奶 2，# 茶師推薦
    ("Fresh MILK", "焙烏龍鮮奶", 55, 65, True),         # 鮮奶 3
    ("Fresh MILK", "烘吉鮮奶", 70, None, True),         # 鮮奶 4，菜單只有 M 欄有價格
]                                                       # 菜單結束，共 24 項

DE_ZHENG_TOPPINGS = {"珍珠": 10, "黃金珍珠": 10, "焙烏龍茶凍": 10}   # 得正加料：不分 M、L、飲料種類，一律 +10
