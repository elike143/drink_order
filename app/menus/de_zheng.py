# 得正菜單，每一筆是 (分類, 品名, M 價格, L 價格, 可不可以做熱飲)，共 24 項
# - L 價格是 None 代表菜單只有 M 欄有價格，只能點 M 杯
# - 分類標 ♥ 的（原味茶、奶茶、鮮奶）可調整為熱飲，其他分類不可熱飲
# - 菜單上標「# 茶師推薦」的：春烏龍、輕烏龍、焙烏龍、檸檬春烏龍、香橙春烏龍、甘蔗春烏龍、
#   芝士奶蓋春烏龍、芝士奶蓋焙烏龍、焙烏龍奶茶、黃金珍珠奶綠、紅茶鮮奶、輕烏龍鮮奶
DE_ZHENG_MENU = [
    # 原味茶
    ("Original TEA", "紅茶", 25, 30, True),
    ("Original TEA", "綠茶", 25, 30, True),
    ("Original TEA", "春烏龍", 30, 35, True),
    ("Original TEA", "輕烏龍", 30, 35, True),
    ("Original TEA", "焙烏龍", 30, 35, True),
    # 果茶
    ("Double FRUIT", "檸檬春烏龍", 55, 65, False),
    ("Double FRUIT", "香橙春烏龍", 60, 70, False),
    ("Double FRUIT", "甘蔗春烏龍", 60, 70, False),
    ("Double FRUIT", "青梅春烏龍", 50, 60, False),
    ("Double FRUIT", "優酪春烏龍", 55, 65, False),
    ("Double FRUIT", "雙柚金烏龍", 55, 65, False),
    # 奶蓋：固定少冰（規則寫在 main.py 的 create_cup）
    ("Cheese MILK FOAM", "芝士奶蓋春烏龍", 50, 60, False),
    ("Cheese MILK FOAM", "芝士奶蓋焙烏龍", 50, 60, False),
    ("Cheese MILK FOAM", "芝士奶蓋阿華田", 55, 65, False),
    ("Cheese MILK FOAM", "芝士奶蓋烘吉茶", 55, 65, False),
    # 奶茶：烘吉奶茶只有 M 杯
    ("Classic MILK TEA", "奶茶", 45, 50, True),
    ("Classic MILK TEA", "焙烏龍奶茶", 45, 50, True),
    ("Classic MILK TEA", "珍珠奶茶", 55, 60, True),
    ("Classic MILK TEA", "黃金珍珠奶綠", 55, 60, True),
    ("Classic MILK TEA", "烘吉奶茶", 50, None, True),
    # 鮮奶：烘吉鮮奶只有 M 杯
    ("Fresh MILK", "紅茶鮮奶", 55, 65, True),
    ("Fresh MILK", "輕烏龍鮮奶", 55, 65, True),
    ("Fresh MILK", "焙烏龍鮮奶", 55, 65, True),
    ("Fresh MILK", "烘吉鮮奶", 70, None, True),
]

# 得正加料：不分 M、L、飲料種類，一律 +10
DE_ZHENG_TOPPINGS = {"珍珠": 10, "黃金珍珠": 10, "焙烏龍茶凍": 10}
