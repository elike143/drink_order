# API


| 方法 | 路徑 | 說明 | 成功 |
| --- | --- | --- | --- |
| GET | `/shops` | 有菜單的店家清單 | 200 |
| GET | `/menu?shop=五十嵐` | 某家店的菜單 | 200 |
| GET | `/price?shop=&drink=&size=&toppings=` | 試算一杯的價格，只算不存 | 200 |
| GET | `/orders` | 所有訂單 | 200 |
| POST | `/orders` | 開一張新訂單 | 201 |
| DELETE | `/orders/{order_id}` | 刪除整張訂單和裡面的飲料 | 204 |
| GET | `/orders/{order_id}/cups` | 某張訂單的所有飲料 | 200 |
| POST | `/orders/{order_id}/cups` | 點一杯飲料 | 201 |
| DELETE | `/orders/{order_id}/cups/{cup_id}` | 刪除一杯；結單後不能刪 | 204 |
| POST | `/orders/{order_id}/close` | 結單 | 200 |

常見錯誤：找不到訂單、飲料或菜單回 **404**；訂單已結單、菜單上沒有這杯、規則不允許的點法（見下方）回 **400**；送來的欄位格式不對回 **422**。

## 資料表

| 資料表 | 存什麼 | 重要欄位 |
| --- | --- | --- |
| `orders` | 訂單 | `shop_name`、`created_at`（資料庫自動填入）、`is_open` |
| `cups` | 每一杯飲料 | `order_id`（外鍵 → `orders.id`）、`who_order`、`drink_name`、`size`、`sugar`、`ice`、`toppings`（PostgreSQL 陣列）、`add`（備註）、`price` |
| `menu_items` | 菜單 | `shop`、`category`、`name`、`price_m`、`price_l`、`hot_ok` |

