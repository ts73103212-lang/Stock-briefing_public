"""
fetch_data.py  ── GitHub Actions上で実行されるデータ取得スクリプト（検証用）
==========================================================================
検証フェーズなので最軽量：
  - TSE全銘柄から騰落率上位5銘柄だけ取得
  - screening_result.json として保存
  - 本番化するときにフィルタ条件を追加していく
"""

import json
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

# ── ライブラリが入っていなければ終了（Actionsのinstallステップで入るはず）
try:
    from tradingview_screener import Query, col
except ImportError as e:
    print(f"ERROR: tradingview-screener が未インストール: {e}")
    sys.exit(1)

print(f"[{now_jst}] データ取得開始")

try:
    n, df = (
        Query()
        .set_markets("japan")
        .select(
            "name",
            "close",
            "volume",
            "change",           # 騰落率（%）
            "market_cap_basic", # 時価総額
        )
        .order_by("change", ascending=False)
        .limit(5)               # 検証なので5件のみ
        .get_scanner_data()
    )

    print(f"取得成功: 総ヒット={n}件, 取得=5件")
    print(df.to_string(index=False))

except Exception as e:
    # 取得失敗してもjsonにエラーを記録してpushする
    result = {
        "fetched_at": now_jst,
        "status": "ERROR",
        "error": str(e),
        "stocks": [],
    }
    with open("screening_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"ERROR: {e}")
    sys.exit(1)

# ── DataFrameをJSONに変換して保存
stocks = []
for _, row in df.iterrows():
    stocks.append({
        "ticker": row["name"],                       # 例: TSE:6613
        "close":  round(float(row["close"]), 1),
        "change": round(float(row["change"]), 2),    # 騰落率%
        "volume": int(row["volume"]),
        "market_cap_bil": round(                     # 時価総額（億円）
            float(row["market_cap_basic"]) / 1e8, 1
        ) if row["market_cap_basic"] else None,
    })

result = {
    "fetched_at": now_jst,
    "status": "OK",
    "total_hits": int(n),
    "stocks": stocks,
}

with open("screening_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n[{now_jst}] screening_result.json に保存完了")
print(json.dumps(result, ensure_ascii=False, indent=2))
