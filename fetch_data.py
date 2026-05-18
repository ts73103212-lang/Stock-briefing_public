"""
fetch_data.py  ── GitHub Actions上で実行されるデータ取得スクリプト（本番版）
==========================================================================

【スクリーニング条件】
  - 株価 2,500円以下
  - 終値 > VWAP（強気引け）
  - EMA5 > EMA25（上昇トレンド②）
  - 騰落率 +3% 〜 +15%（ストップ高除外）
  - RSI <= 70（過熱除外）
  - 時価総額 30億円以上（板薄除外）
  - 出来高 > 10日平均の2倍（本物の資金流入）

【出力ファイル】
  - screening_result.json（スクリーニング通過銘柄・上位20件）
  - holdings_result.json （保有銘柄の個別株価データ）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【保有銘柄の編集方法】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  HOLDINGS リストを直接編集してください。
  フォーマット: {"code": "TSE:証券コード", "shares": 株数, "cost": 取得単価}

  ▼ 銘柄追加の例:
    {"code": "TSE:9984", "shares": 100, "cost": 8500},   # ソフトバンクG

  ▼ 銘柄削除: 該当行をまるごと削除

  ▼ 保有なし: HOLDINGS = [] のまま（空リスト）にする
    → holdings_result.json に holdings: [] が記録され、Routineは「保有なし」と表示

  ※ コードは必ず "TSE:数字" の形式で入力（例: TSE:6613）
  ※ 変更後はGitHubでCommitすること（次回Actions実行から反映）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
from datetime import datetime, timezone, timedelta

# ══════════════════════════════════════════════
# ★ 保有銘柄リスト ── ここだけ編集する ★
# ══════════════════════════════════════════════
HOLDINGS = [
    {"code": "TSE:6613", "shares": 100, "cost": 1600},  # QDレーザ
    {"code": "TSE:6494", "shares": 500, "cost": 124},   # NFK
    {"code": "TSE:7375", "shares": 100, "cost": 1540},  # リファインバース 
    # ↓ 銘柄を追加する場合はここにコピー＆ペーストして編集
    # {"code": "TSE:XXXX", "shares": 100, "cost": 0000},  # 銘柄名
]
# ══════════════════════════════════════════════

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def save_error(filename, message):
    """エラー時にJSONを保存して続行（sys.exitしない）"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": now_jst, "status": "ERROR",
                   "error": message}, f, ensure_ascii=False, indent=2)
    print(f"ERROR [{filename}]: {message}")


def stock_row_to_dict(row):
    """DataFrameの1行をJSONフォーマットに変換する共通関数"""
    vol     = float(row["volume"])   if row["volume"]   else 0
    vol_avg = float(row["average_volume_10d_calc"]) \
              if row.get("average_volume_10d_calc") else 1
    close   = float(row["close"])    if row["close"]    else 0
    return {
        "ticker":         row["name"],
        "close":          round(close, 1),
        "change":         round(float(row["change"]), 2) if row.get("change") else None,
        "volume":         int(vol),
        "vol_ratio":      round(vol / max(vol_avg, 1), 1),
        "turnover_mil":   round(close * vol / 1e6, 1),
        "market_cap_bil": round(float(row["market_cap_basic"]) / 1e8, 1)
                          if row.get("market_cap_basic") else None,
        "rsi":            round(float(row["RSI"]), 1)   if row.get("RSI")   else None,
        "vwap":           round(float(row["VWAP"]), 1)  if row.get("VWAP")  else None,
        "ema5":           round(float(row["EMA5"]), 1)  if row.get("EMA5")  else None,
        "ema25":          round(float(row["EMA25"]), 1) if row.get("EMA25") else None,
        "atr":            round(float(row["ATR"]), 1)   if row.get("ATR")   else None,
    }


# ──────────────────────────────────────────────
# ライブラリインポート
# ──────────────────────────────────────────────
try:
    from tradingview_screener import Query, col
except ImportError as e:
    save_error("screening_result.json", f"tradingview-screener未インストール: {e}")
    save_error("holdings_result.json",  f"tradingview-screener未インストール: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════
# PART 1: スクリーニング（市場全体）
# ══════════════════════════════════════════════
print(f"[{now_jst}] PART1: スクリーニング開始")

try:
    n, df = (
        Query()
        .set_markets("japan")
        .select(
            "name", "close", "VWAP", "EMA5", "EMA25",
            "volume", "average_volume_10d_calc",
            "change", "market_cap_basic", "RSI", "ATR",
        )
        .where(
            col("close") <= 2500,
            col("close") > col("VWAP"),
            col("EMA5") > col("EMA25"),
            col("change") >= 3,
            col("change") <= 15,
            col("RSI") <= 70,
            col("market_cap_basic") >= 3e9,
            col("volume") > col("average_volume_10d_calc"),  # 平均超え（2倍はPython側）
        )
        .order_by("change", ascending=False)
        .limit(50)
        .get_scanner_data()
    )
    print(f"  スクリーニング取得: {n}件ヒット")

    # 祝日・閑散日の0件処理
    if n == 0 or len(df) == 0:
        print("  ヒット0件（祝日または市場閑散）→ 正常終了")
        result = {"fetched_at": now_jst, "status": "NO_DATA",
                  "note": "スクリーニング通過銘柄なし（祝日または市場閑散の可能性）",
                  "total_hits": 0, "stocks": []}
    else:
        # 出来高2倍フィルタをPython側で適用
        df["vol_ratio_calc"] = df["volume"] / df["average_volume_10d_calc"].replace(0, 1)
        df_filtered = df[df["vol_ratio_calc"] >= 2].head(20)
        print(f"  出来高2倍フィルタ後: {len(df_filtered)}件")
        stocks = [stock_row_to_dict(row) for _, row in df_filtered.iterrows()]
        result = {"fetched_at": now_jst, "status": "OK",
                  "total_hits": int(n), "stocks": stocks}

    with open("screening_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  screening_result.json 保存完了")

except Exception as e:
    save_error("screening_result.json", str(e))


# ══════════════════════════════════════════════
# PART 2: 保有銘柄の個別データ取得
# ══════════════════════════════════════════════
print(f"[{now_jst}] PART2: 保有銘柄データ取得")

# 保有なし → 空ファイルを保存して終了
if not HOLDINGS:
    print("  保有銘柄なし → holdings_result.json に空データを保存")
    with open("holdings_result.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": now_jst, "status": "OK",
                   "note": "保有銘柄なし", "holdings": []},
                  f, ensure_ascii=False, indent=2)
    print(f"[{now_jst}] 全処理完了")
    sys.exit(0)

# "TSE:6613" → "6613" に変換（APIのnameフィールドはプレフィックスなし形式）
code_only  = lambda c: c.replace("TSE:", "")
cost_map   = {code_only(h["code"]): h["cost"]   for h in HOLDINGS}
shares_map = {code_only(h["code"]): h["shares"] for h in HOLDINGS}
full_code  = {code_only(h["code"]): h["code"]   for h in HOLDINGS}
holding_ticker_list = [code_only(h["code"]) for h in HOLDINGS]  # "6613"形式で検索

try:
    nh, dfh = (
        Query()
        .set_markets("japan")
        .select(
            "name", "close", "VWAP", "EMA5", "EMA25",
            "volume", "average_volume_10d_calc",
            "change", "market_cap_basic", "RSI", "ATR",
        )
        .where(
            col("name").isin(holding_ticker_list)  # "6613"形式で検索
        )
        .get_scanner_data()
    )
    print(f"  保有銘柄取得: {nh}件")

    holdings_data = []
    for _, row in dfh.iterrows():
        code   = row["name"]                        # APIは"6613"形式で返す
        ticker = full_code.get(code, f"TSE:{code}") # 表示は"TSE:6613"形式に戻す
        cost   = cost_map.get(code, 0)
        shares = shares_map.get(code, 0)
        close  = float(row["close"]) if row["close"] else 0

        pnl_yen = round((close - cost) * shares, 0)
        pnl_pct = round((close - cost) / cost * 100, 2) if cost else None

        entry = stock_row_to_dict(row)
        entry["ticker"] = ticker  # "TSE:6613"形式で上書き
        entry.update({"cost": cost, "shares": shares,
                      "pnl_yen": int(pnl_yen), "pnl_pct": pnl_pct})
        holdings_data.append(entry)
        print(f"  {ticker}: ¥{close} / 損益 {pnl_pct}% / ¥{pnl_yen}")

    # 取得できなかった銘柄を「データなし」として補完
    fetched_codes = [code_only(d["ticker"]) for d in holdings_data]
    for h in HOLDINGS:
        if code_only(h["code"]) not in fetched_codes:
            print(f"  {h['code']}: 取得不可（市場閉鎖または銘柄コード確認要）")
            holdings_data.append({
                "ticker": h["code"], "cost": h["cost"], "shares": h["shares"],
                "close": None, "pnl_yen": None, "pnl_pct": None,
                "note": "データ取得不可",
            })

    with open("holdings_result.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": now_jst, "status": "OK",
                   "holdings": holdings_data}, f, ensure_ascii=False, indent=2)
    print(f"  holdings_result.json 保存完了")

except Exception as e:
    save_error("holdings_result.json", str(e))

print(f"[{now_jst}] 全処理完了")
