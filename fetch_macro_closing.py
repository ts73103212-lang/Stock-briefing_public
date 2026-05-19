"""
fetch_macro_closing.py
----------------------
引け後（15:40 JST）実行。当日の日本株引け値と各種マクロデータを取得する。
fetch_macro.py・fetch_macro_midday.py とは完全に独立。

取得対象:
  - 日経225・TOPIX ETF（当日終値）
  - 米国指数・SOX（前日終値 ※米国市場未開場のため）
  - ドル円・VIX・WTI原油・金（リアルタイムに近い値）

出力: macro_result_closing.json
実行: python fetch_macro_closing.py
依存: yfinance pytz （pip install yfinance pytz）
"""

import json
import sys
from datetime import datetime

import pytz
import yfinance as yf

# ──────────────────────────────────────────
# 取得対象シンボル定義
# ──────────────────────────────────────────
SYMBOLS = {
    # 日本株指数（当日終値が取れる）
    "日経225":          "^N225",
    "TOPIX(ETF)":       "1306.T",
    # 米国指数（前日終値 ※15:40時点では米国市場未開場）
    "NASDAQ100":        "^NDX",
    "S&P500":           "^GSPC",
    "ダウ平均":         "^DJI",
    "SOX":              "^SOX",
    # 為替・コモディティ（リアルタイムに近い値）
    "ドル円":           "JPY=X",
    "VIX":              "^VIX",
    "WTI原油":          "CL=F",
    "金(XAUUSD)":       "GC=F",
    # 米国株先物（夕時点のセンチメント確認用）
    "S&P500先物":       "ES=F",
    "NASDAQ100先物":    "NQ=F",
}

COMMENTS = {
    "日経225":          "当日終値。朝シナリオ検証の基準値",
    "TOPIX(ETF)":       "ETF(1306)経由の概算値",
    "NASDAQ100":        "前日終値（米国市場は未開場）",
    "S&P500":           "前日終値（米国市場は未開場）",
    "ダウ平均":         "前日終値（米国市場は未開場）",
    "SOX":              "前日終値。翌日の半導体セクター方向性",
    "ドル円":           "円安→輸出株サポート / 急変に注意",
    "VIX":              "20超え警戒 / 30超えパニック水準",
    "WTI原油":          "エネルギー・ナフサ関連セクターへの影響",
    "金(XAUUSD)":       "リスクオフ・インフレ指標",
    "S&P500先物":       "米国市場開場前のセンチメント",
    "NASDAQ100先物":    "ハイテク・半導体の夜間センチメント",
}


def jst_now() -> str:
    jst = pytz.timezone("Asia/Tokyo")
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")


def fetch_symbol(name: str, ticker_str: str) -> dict:
    """1銘柄分のデータを取得して辞書で返す。失敗時はエラー情報を返す。"""
    try:
        ticker = yf.Ticker(ticker_str)
        hist = ticker.history(period="2d", interval="1d")

        if hist.empty:
            return {
                "name": name,
                "ticker": ticker_str,
                "close": None,
                "prev_close": None,
                "change_pct": None,
                "comment": COMMENTS.get(name, ""),
                "status": "NO_DATA",
            }

        close = round(float(hist["Close"].iloc[-1]), 2)

        if len(hist) >= 2:
            prev_close = round(float(hist["Close"].iloc[-2]), 2)
            change_pct = round((close - prev_close) / prev_close * 100, 2)
        else:
            prev_close = None
            change_pct = None

        return {
            "name": name,
            "ticker": ticker_str,
            "close": close,
            "prev_close": prev_close,
            "change_pct": change_pct,
            "comment": COMMENTS.get(name, ""),
            "status": "OK",
        }

    except Exception as e:
        return {
            "name": name,
            "ticker": ticker_str,
            "close": None,
            "prev_close": None,
            "change_pct": None,
            "comment": COMMENTS.get(name, ""),
            "status": f"ERROR: {str(e)[:80]}",
        }


def main():
    fetched_at = jst_now()
    results = []
    errors = []

    print(f"[fetch_macro_closing] 開始: {fetched_at}")

    for name, ticker_str in SYMBOLS.items():
        row = fetch_symbol(name, ticker_str)
        results.append(row)

        if row["status"] == "OK":
            sign = "+" if (row["change_pct"] or 0) >= 0 else ""
            print(f"  ✅ {name:20s} {row['close']:>12,.2f}  "
                  f"({sign}{row['change_pct']}%)")
        else:
            print(f"  ❌ {name:20s} {row['status']}")
            errors.append(name)

    output = {
        "fetched_at": fetched_at,
        "status": "OK" if not errors else f"PARTIAL_ERROR: {errors}",
        "note": (
            "15:40 JST取得。日経225・TOPIXは当日終値。"
            "米国指数（NASDAQ・S&P500・SOX）は前日終値（米国市場未開場）。"
            "先物・為替・VIXはリアルタイムに近い値（15分ディレイ）。"
            "statusがOK以外の項目はweb検索で補完すること。"
        ),
        "macro": results,
    }

    with open("macro_result_closing.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[fetch_macro_closing] 完了 → macro_result_closing.json 出力")
    print(f"  取得成功: {len(results) - len(errors)}/{len(results)} シンボル")

    if errors:
        print(f"  取得失敗: {errors}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
