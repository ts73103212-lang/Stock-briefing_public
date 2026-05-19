"""
fetch_macro.py
--------------
GitHub Actions から実行する指数・為替・コモディティデータ取得スクリプト。
fetch_data.py とは完全に独立しており、既存処理に影響しない。

出力: macro_result.json
実行: python fetch_macro.py
依存: yfinance, pytz  （pip install yfinance pytz）
"""

import json
import sys
from datetime import datetime, timedelta

import pytz
import yfinance as yf

# ──────────────────────────────────────────
# 取得対象シンボル定義
# ──────────────────────────────────────────
SYMBOLS = {
    # 米国指数
    "NASDAQ100":    "^NDX",
    "S&P500":       "^GSPC",
    "ダウ平均":     "^DJI",
    "SOX":          "^SOX",
    "VIX":          "^VIX",
    # コモディティ
    "WTI原油":      "CL=F",
    "金(XAUUSD)":   "GC=F",
    # 為替
    "ドル円":       "JPY=X",
    # 日本株指数（前日終値）
    "日経225":      "^N225",
    "TOPIX":        "1306.T",   # ETF経由（^TPX は取れない場合がある）
}

# コメントテンプレート（Routineへのヒント）
COMMENTS = {
    "NASDAQ100":    "ハイテク・半導体の方向性",
    "S&P500":       "米国全体のセンチメント",
    "ダウ平均":     "景気敏感・バリュー動向",
    "SOX":          "半導体セクター直結",
    "VIX":          "20超え警戒 / 30超えパニック水準",
    "WTI原油":      "エネルギー・ナフサ・輸送コスト",
    "金(XAUUSD)":   "リスクオフ・インフレ指標",
    "ドル円":       "円安→輸出株サポート / 急変に注意",
    "日経225":      "日本市場の前日終値",
    "TOPIX":        "ETF(1306)経由の概算値",
}


def jst_now() -> str:
    jst = pytz.timezone("Asia/Tokyo")
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")


def fetch_symbol(name: str, ticker_str: str) -> dict:
    """1銘柄分のデータを取得して辞書で返す。失敗時はエラー情報を返す。"""
    try:
        ticker = yf.Ticker(ticker_str)

        # 直近2営業日分を取得（前日終値を確実に得るため）
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

        # 前日比計算（2日分あれば算出）
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
            "change_pct": change_pct,       # プラスなら上昇・マイナスなら下落
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

    print(f"[fetch_macro] 開始: {fetched_at}")

    for name, ticker_str in SYMBOLS.items():
        row = fetch_symbol(name, ticker_str)
        results.append(row)

        if row["status"] == "OK":
            sign = "+" if (row["change_pct"] or 0) >= 0 else ""
            print(f"  ✅ {name:15s} {row['close']:>12,.2f}  "
                  f"({sign}{row['change_pct']}%)")
        else:
            print(f"  ❌ {name:15s} {row['status']}")
            errors.append(name)

    # ──────────────────────────────────────────
    # JSON出力
    # ──────────────────────────────────────────
    output = {
        "fetched_at": fetched_at,
        "status": "OK" if not errors else f"PARTIAL_ERROR: {errors}",
        "note": "前日米国市場終値ベース（15分ディレイ）。朝7:20取得なら実質前日終値。",
        "macro": results,
    }

    with open("macro_result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[fetch_macro] 完了 → macro_result.json 出力")
    print(f"  取得成功: {len(results) - len(errors)}/{len(results)} シンボル")

    if errors:
        print(f"  取得失敗: {errors}")
        sys.exit(1)  # Actionsでエラー検知させる場合はexit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
