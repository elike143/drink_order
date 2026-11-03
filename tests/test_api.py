from fastapi.testclient import TestClient
from app.main import app

# 建立測試客戶端，用來模擬 HTTP 請求
client = TestClient(app)


def test_get_menu():
  """測試 GET /menu 是否能正常回傳菜單列表"""
  response = client.get("/menu")
  assert response.status_code == 200

  data = response.json()
  assert isinstance(data, list)
  # 確保至少有從 seed.py 寫入的菜單資料
  assert len(data) > 0
  assert "name" in data[0]
  assert "price" in data[0]


def test_create_order():
  """測試 POST /orders 是否能成功建立訂單並計算金額"""
  # 構造要送出的訂單 JSON 資料（需對應資料庫中真實存在的 menu_item_id，例如 1）
  order_payload = {
      "customer_name": "王小明",
      "items": [
          {"menu_item_id": 1, "quantity": 2, "sugar": "微糖", "ice": "少冰"}
      ],
  }

  response = client.post("/orders", json=order_payload)
  assert response.status_code == 200

  data = response.json()
  assert data["message"] == "訂單建立成功"
  assert "order_id" in data
  assert data["total"] > 0