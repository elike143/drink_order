# 匯入需要的工具
# - time：取得目前時間，算一分鐘內送了幾次
# - deque：兩頭都能快速加減的清單，用來記每一次送出的時間
# - Lock：同時有好幾個請求時，避免一起改同一份紀錄
# - HTTPException、Request：回傳 429 錯誤、讀取請求的來源 IP
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException, Request

# 限流設定：每 60 秒內，同一個 IP 最多 20 次、整個網站加起來最多 200 次寫入
# 寫入指的是開單、點杯、結單、刪單、刪杯，看資料的請求不受限制
WINDOW_SECONDS = 60
PER_IP_LIMIT = 20
GLOBAL_LIMIT = 200

# 紀錄：key 是 "ip:來源IP" 或 "all"，value 是最近一分鐘內每次寫入的時間
# 紀錄只存在記憶體，伺服器重開就清空；Render 免費方案只跑一個程序，所以一份紀錄就夠
_hits: dict[str, deque[float]] = {}
_lock = Lock()


# 找出請求來自哪個 IP
# 部署在 Render 時，請求會先經過 Render 的代理，真正的來源 IP 放在 X-Forwarded-For 的第一個；
# 本機直接連線沒有這個 header，就用連線本身的 IP
# 注意：X-Forwarded-For 可以被偽造，換 IP 就能繞過單一 IP 的限制，所以另外有全站上限當最後一道防線
def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# 先丟掉超過 60 秒的舊紀錄，再看這個 key 在一分鐘內是不是已經到上限
def _is_full(key: str, limit: int, now: float) -> bool:
    hits = _hits.get(key)
    if hits is None:
        return False
    while hits and hits[0] <= now - WINDOW_SECONDS:
        hits.popleft()
    return len(hits) >= limit


# 清掉一分鐘內都沒有再送過的 IP，避免很多不同 IP 送過一次後，紀錄一直留在記憶體裡越堆越多
def _sweep(now: float) -> None:
    for key in [k for k, hits in _hits.items() if not hits or hits[-1] <= now - WINDOW_SECONDS]:
        del _hits[key]


# 給寫入的路由用 dependencies=[Depends(limit_writes)] 掛上
# 1. 單一 IP 或全站任一個到上限，就回 429 並請對方等一下，這次不算進紀錄
# 2. 沒到上限就把這次記下來，讓路由繼續執行
# 3. 紀錄超過 1000 個 key 時順便清一次舊的
def limit_writes(request: Request) -> None:
    now = time.monotonic()
    ip_key = f"ip:{client_ip(request)}"
    with _lock:
        if _is_full("all", GLOBAL_LIMIT, now) or _is_full(ip_key, PER_IP_LIMIT, now):
            raise HTTPException(status_code=429, detail="送出太頻繁了，請等一分鐘再試")
        _hits.setdefault("all", deque()).append(now)
        _hits.setdefault(ip_key, deque()).append(now)
        if len(_hits) > 1000:
            _sweep(now)
