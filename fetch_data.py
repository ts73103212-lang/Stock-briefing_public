"""
fetch_data.py  ── GitHub Actions上で実行されるデータ取得スクリプト（本番版）
==========================================================================
取得条件:
  - 株価 2,500円以下
  - 終値 > VWAP（強気引け）
  - EMA5 > EMA25（上昇トレンド②）
  - 騰落率 +3% 〜 +15%（ストップ高除外）
  - RSI <= 70（過熱除外）
  - 時価総額 30億円以上（板薄除外）
  - 出来高 > 10日平均の2倍（本物の資金流入）

出力: screening_result.json（リポジトリルートに上書き保存）
"""

import json
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

try:
    from tradingview_screener import Query, col
except ImportError as e:
    result = {"fetched_at": now_jst, "status": "ERROR",
              "error": f"tradingview-screener未インストール: {e}", "stocks": []}
    with open("screening_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"ERROR: {e}")
    sys.exit(1)

print(f"[{now_jst}] スクリーニング開始")

try:
    n, df = (
        Query()
        .set_markets("japan")
        .select(
            "name",
            "close",
            "VWAP",
            "EMA5",
            "EMA25",
            "volume",
            "average_volume_10d_calc",
            "change",
            "market_cap_basic",
            "RSI",
            "ATR",
        )
        .where(
            col("close") <= 2500,
            col("close") > col("VWAP"),
            col("EMA5") > col("EMA25"),
            col("change") >= 3,
            col("change") <= 15,
            col("RSI") <= 70,
            col("market_cap_basic") >= 3e9,
            col("volume") > col("average_volume_10d_calc") * 2,
        )
        .order_by("change", ascending=False)
        .limit(20)
        .get_scanner_data()
    )
    print(f"スクリーニング成功: {n}件ヒット")

except Exception as e:
    result = {"fetched_at": now_jst, "status": "ERROR", "error": str(e), "stocks": []}
    with open("screening_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"ERROR: {e}")
    sys.exit(1)

# ── DataFrameをJSONに変換
stocks = []
for _, row in df.iterrows():
    vol     = float(row["volume"]) if row["volume"] else 0
    vol_avg = float(row["average_volume_10d_calc"]) if row["average_volume_10d_calc"] else 1
    close   = float(row["close"]) if row["close"] else 0

    stocks.append({
        "ticker":         row["name"],
        "close":          round(close, 1),
        "change":         round(float(row["change"]), 2),
        "volume":         int(vol),
        "vol_ratio":      round(vol / vol_avg, 1),
        "turnover_mil":   round(close * vol / 1e6, 1),
        "market_cap_bil": round(float(row["market_cap_basic"]) / 1e8, 1)
                          if row["market_cap_basic"] else None,
        "rsi":            round(float(row["RSI"]), 1)
                          if row["RSI"] else None,
        "vwap":           round(float(row["VWAP"]), 1)
                          if row["VWAP"] else None,
        "ema5":           round(float(row["EMA5"]), 1)
                          if row["EMA5"] else None,
        "ema25":          round(float(row["EMA25"]), 1)
                          if row["EMA25"] else None,
        "atr":            round(float(row["ATR"]), 1)
                          if row["ATR"] else None,
    })

result = {
    "fetched_at": now_jst,
    "status":     "OK",
    "total_hits": int(n),
    "stocks":     stocks,
}

with open("screening_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[{now_jst}] screening_result.json 保存完了（{len(stocks)}件）")
print(json.dumps(result, ensure_ascii=False, indent=2))
