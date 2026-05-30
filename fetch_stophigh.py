"""
fetch_stophigh.py
-----------------
引け後（15:37 JST）実行。ストップ高圏銘柄からPTS継続候補を抽出する。
fetch_macro_closing.py・fetch_data.py とは完全に独立。

【抽出条件（フィルタ）】
  - 騰落率 +15%以上（ストップ高圏）
  - 終値 > VWAP（強気引け）
  - 時価総額 ≥ 30億円（板の厚み）
  - close/high ≥ 0.97（高値引け・上ヒゲ3%以内）

【記録項目（フィルタなし・ルーティン判断用）】
  - stock_type: 寄らずストップ高 / ザラ場ストップ高 / ストップ高（通常）
  - ema5_above_ema25: EMA5 > EMA25 か
  - close_above_ema25: 終値 > EMA25 か
  - change_1d: 前日騰落率（連続性の参考）

出力: screening_stophigh_closing.json（上位10件）
実行: python fetch_stophigh.py
依存: tradingview-screener （pip install tradingview-screener）
"""

import json
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
OUTPUT_FILE = "screening_stophigh_closing.json"


def save_error(message):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": now_jst, "status": "ERROR",
                   "error": message}, f, ensure_ascii=False, indent=2)
    print(f"ERROR: {message}")


try:
    from tradingview_screener import Query, col
except ImportError as e:
    save_error(f"tradingview-screener未インストール: {e}")
    sys.exit(1)


def classify_stock_type(vol_ratio: float) -> str:
    """出来高比率からストップ高のタイプを判定する"""
    if vol_ratio < 0.3:
        return "寄らずストップ高（超強気）"
    elif vol_ratio >= 3.0:
        return "ザラ場ストップ高（出来高急増）"
    else:
        return "ストップ高（通常）"


def build_candidate(row) -> dict:
    """DataFrameの1行をJSONフォーマットに変換する"""
    vol     = float(row["volume"])   if row.get("volume")   else 0
    vol_avg = float(row["average_volume_10d_calc"]) \
              if row.get("average_volume_10d_calc") else 1
    close   = float(row["close"])    if row.get("close")    else 0
    high    = float(row["high"])     if row.get("high")     else close
    ema5    = float(row["EMA5"])     if row.get("EMA5")     else None
    ema25   = float(row["EMA25"])    if row.get("EMA25")    else None
    vwap    = float(row["VWAP"])     if row.get("VWAP")     else None
    change_1d = float(row["change|1"]) if row.get("change|1") else None

    vol_ratio = round(vol / max(vol_avg, 1), 1)
    close_to_high = round(close / high, 3) if high > 0 else None

    return {
        "ticker":             row["name"],
        "close":              round(close, 1),
        "change":             round(float(row["change"]), 2) if row.get("change") else None,
        "high":               round(high, 1),
        "close_to_high":      close_to_high,           # 1.0に近いほど高値引け
        "volume":             int(vol),
        "vol_ratio":          vol_ratio,
        "stock_type":         classify_stock_type(vol_ratio),
        "turnover_mil":       round(close * vol / 1e6, 1),
        "market_cap_bil":     round(float(row["market_cap_basic"]) / 1e8, 1)
                              if row.get("market_cap_basic") else None,
        "rsi":                round(float(row["RSI"]), 1)   if row.get("RSI")   else None,
        "vwap":               round(vwap, 1)                if vwap             else None,
        "ema5":               round(ema5, 1)                if ema5             else None,
        "ema25":              round(ema25, 1)               if ema25            else None,
        "atr":                round(float(row["ATR"]), 1)   if row.get("ATR")   else None,
        "ema5_above_ema25":   (ema5 > ema25)               if (ema5 and ema25) else None,
        "close_above_ema25":  (close > ema25)              if ema25            else None,
        "change_1d":          round(change_1d, 2)          if change_1d is not None else None,
    }


print(f"[{now_jst}] fetch_stophigh: スクリーニング開始")

try:
    n, df = (
        Query()
        .set_markets("japan")
        .select(
            "name", "close", "high", "VWAP", "EMA5", "EMA25",
            "volume", "average_volume_10d_calc",
            "change", "change|1",
            "market_cap_basic", "RSI", "ATR",
        )
        .where(
            col("change")           >= 15,          # ストップ高圏（+15%以上）
            col("close")            >  col("VWAP"), # 強気引け
            col("market_cap_basic") >= 3e9,         # 時価総額30億円以上
        )
        .order_by("change", ascending=False)
        .limit(50)
        .get_scanner_data()
    )
    print(f"  where句通過: {n}件")

    if n == 0 or len(df) == 0:
        print("  ヒット0件（ストップ高銘柄なし）→ 正常終了")
        result = {
            "fetched_at": now_jst, "status": "NO_DATA",
            "note": "本日ストップ高圏通過銘柄なし",
            "total_hits": 0, "candidates": []
        }
    else:
        # close/high ≥ 0.97 フィルタ（高値引け）をPython側で適用
        # ※ high列が取得できない場合は除外しない（スキップ）
        candidates = []
        skipped = 0
        for _, row in df.iterrows():
            close = float(row["close"]) if row.get("close") else 0
            high  = float(row["high"])  if row.get("high")  else 0
            if high > 0:
                ratio = close / high
                if ratio < 0.97:
                    skipped += 1
                    continue   # 上ヒゲ大きい → 除外
            candidates.append(build_candidate(row))

        print(f"  高値引けフィルタ後: {len(candidates)}件（除外: {skipped}件）")

        # 騰落率降順で上位10件
        candidates = candidates[:10]
        print(f"  最終出力: {len(candidates)}件")

        result = {
            "fetched_at":  now_jst,
            "status":      "OK",
            "note":        (
                "騰落率+15%以上・強気引け・高値引け(close/high≥0.97)の銘柄。"
                "stock_typeで寄らず/ザラ場を判別。"
                "ema5_above_ema25・close_above_ema25・change_1dはフィルタなし参考値。"
                "ルーティン側で3銘柄に絞ること。"
            ),
            "total_hits":  int(n),
            "candidates":  candidates,
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  {OUTPUT_FILE} 保存完了")

    for c in result.get("candidates", []):
        print(f"  {c['ticker']:6s} {c['close']:>8.1f}円  "
              f"+{c['change']}%  {c['stock_type']}  "
              f"close/high={c['close_to_high']}")

except Exception as e:
    save_error(str(e))
    sys.exit(1)

print(f"[{now_jst}] fetch_stophigh: 完了")
