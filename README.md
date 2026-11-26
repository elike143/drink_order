# 訂飲料系統 drink_order

揪團訂飲料用的小網站：開一張單、把連結丟進群組，大家各自點，最後一鍵結單。價格由後端照菜單和加料規則算，不靠前端。

這是我轉職後端工程師培訓的結訓專題，主要練 API 設計和資料庫設計。

<img width="1820" height="827" alt="點餐畫面" src="https://github.com/user-attachments/assets/e40fdea2-6ea8-4674-9a9d-1741de111f16" />

線上版：https://drink-order-8h9v.onrender.com/
（Render 免費方案，閒置 15 分鐘會休眠，第一次打開要等大約 1 分鐘）

## 做了什麼

- 開單：目前支援五十嵐和得正
- 點飲料：選尺寸、甜度、冰塊、加料，換選項時價格會即時向後端試算
- 明細：依點單的人分組，算出每人小計和總金額
- 結單：結單後不能再點，但明細還看得到

技術：FastAPI、PostgreSQL、SQLAlchemy、Pydantic、Docker Compose。前端是單一個 HTML 檔，部署在 Render，資料庫放在 Neon。

## 為什麼這樣設計

**價格只在後端算。**
前端畫面上會顯示試算價格，但點單送出時，後端不收前端傳來的價格，一律用 `cup_price()` 重新算一次。如果後端直接相信前端，有人打開開發者工具把 `price` 改成 1，這杯就真的只收 1 塊。試算 API `/price` 也呼叫同一個函式，所以畫面上看到的價格和最後記下來的一定一樣。

**目前沒有權限控管。**
這個專題先把點單流程做完整。原本每張單有管理碼和刪除碼，在 PR #13 拿掉了，現在拿到連結的人都能結單、刪單。這只適合彼此認識的揪團；要給陌生人用的話，下一步是加上 JWT 登入。

**擋住用程式灌資料。**
沒有權限控管，至少要讓人沒辦法繞過網頁、直接呼叫 API 把資料庫塞滿。開單時店名必須是有菜單的店，同一種料不能加兩次，一張單最多 100 杯，首頁只列最新的 50 張單。會改資料的請求另外有次數限制：每 60 秒同一個 IP 最多 20 次、整個網站最多 200 次，超過回 429。

**後端和資料庫都放新加坡。**
Render 和 Neon 選同一個區域，查詢不用跨海，延遲比較低。同一份程式碼靠 `DATABASE_URL` 環境變數決定連本機的 Docker 資料庫還是 Neon，程式本身不用知道自己跑在哪裡。

## 在自己電腦跑起來

需要 Python、Docker Desktop、Git。

```bash
git clone https://github.com/elike143/drink_order.git
cd drink_order
cp .env.example .env              # 把 .env 裡的 change_me 換成自己的密碼

python -m venv venv
source venv/Scripts/activate      # macOS / Linux：source venv/bin/activate
pip install -r requirements.txt

docker compose up -d              # 啟動 PostgreSQL
uvicorn app.main:app --reload     # 第一次啟動會自動建表、寫入菜單
```

打開 http://127.0.0.1:8000/ 是點餐頁，http://127.0.0.1:8000/docs 可以直接測試每支 API。

## 已知限制

- 拿到連結的人都能結單、刪單，沒有權限控管
- 次數限制的紀錄存在記憶體，只適用一個程序，伺服器重開就清空
- 用 `X-Forwarded-For` 認 IP，這個 header 可以偽造。全站上限能擋住灌資料，但有心人也能用它讓所有人一分鐘內都不能點單。下一步改成 JWT 登入後依帳號限制
- 用 `create_all` 建表，改資料表結構要重建資料庫。下一步改用 Alembic
- 加料規則用 if 依店名分支，每多一家店就要改程式
- 還沒有自動測試，目前用 FastAPI 的 `TestClient` 寫臨時腳本手動驗證。下一步加 GitHub Actions，每次開 PR 自動跑 pytest

## 更多細節

- [API 一覽](docs/api.md)
- [計價與點單規則](docs/pricing.md)：五十嵐、得正的加料價格，哪些點法會被拒絕
- [部署](docs/deployment.md)：Render 和 Neon 的設定、資安設定、資料表結構變更
