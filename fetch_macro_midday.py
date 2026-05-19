"""
fetch_macro_midday.py
---------------------
昼ルーティン用マクロデータ取得スクリプト。
fetch_macro.py（朝用）とは独立しており、既存処理に影響しない。

取得対象:
  - 日経225・TOPIX ETF（前場終値 or ザラ場中の最新値）
  - 米国株先物（S&P500先物・NASDAQ先物）
  - ドル円・ユーロ円（現在値）
  - VIX（現在値）
  - WTI原油（現在値）

出力: macro_result_midday.json
実行: python fetch_macro_midday.py
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
    # 日本株指数
    "日経225":          "^N225",
    "TOPIX(ETF)":       "1306.T",
    # 米国株先物（昼時点では前日終値だが朝より新しい可能性あり）
    "S&P500先物":       "ES=F",
    "NASDAQ100先物":    "NQ=F",
    # 為替
    "ドル円":           "JPY=X",
    "ユーロ円":         "EURJPY=X",
    # ボラティリティ
    "VIX":              "^VIX",
    # コモディティ
    "WTI原油":          "CL=F",
}

COMMENTS = {
    "日経225":          "前場終値。後場の方向性判断に使う",
    "TOPIX(ETF)":       "ETF(1306)経由の概算値",
    "S&P500先物":       "後場への米国影響度を確認",
    "NASDAQ100先物":    "ハイテク・半導体セクターの後場影響",
    "ドル円":           "円安→輸出株サポート / 急変に注意",
    "ユーロ円":         "リスクセンチメントの補助指標",
    "VIX":              "20超え警戒 / 30超えパニック水準",
    "WTI原油":          "エネルギー・ナフサ関連セクターへの影響",
}


def jst_now() -> str:
    jst = pytz.timezone("Asia/Tokyo")
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")


def fetch_symbol(name: str, ticker_str: str) -> dict:
    """1銘柄分のデータを取得して辞書で返す。失敗時はエラー情報を返す。"""
    try:
        ticker = yf.Ticker(ticker_str)

        # 直近2日分の日足で取得（前場終値の最善の近似値）
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

    print(f"[fetch_macro_midday] 開始: {fetched_at}")

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
            "昼11:40取得。日経225・TOPIXは前場終値の近似値。"
            "米国先物・為替・VIXはリアルタイムに近い値（15分ディレイ）。"
            "statusがOK以外の項目はweb検索で補完すること。"
        ),
        "macro": results,
    }

    with open("macro_result_midday.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[fetch_macro_midday] 完了 → macro_result_midday.json 出力")
    print(f"  取得成功: {len(results) - len(errors)}/{len(results)} シンボル")

    if errors:
        print(f"  取得失敗: {errors}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
