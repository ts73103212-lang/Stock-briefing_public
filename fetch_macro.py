"""
fetch_macro.py
--------------
GitHub Actions から実行する指数・為替・コモディティデータ取得スクリプト。
fetch_data.py とは完全に独立しており、既存処理に影響しない。

【v2修正点】
  - period="2d"の日足取得をやめ、fast_info.last_price（最新値）を主軸にした
  - 日足のズレで「1日古い終値」が出る問題を解消
  - 取得した実際の日付（data_date）をJSONに記録し、ズレを可視化
  - last_price取得失敗時のみ日足にフォールバック

出力: macro_result.json
実行: python fetch_macro.py
依存: yfinance, pytz  （pip install yfinance pytz）
"""

import json
import sys
from datetime import datetime

import pytz
import yfinance as yf

SYMBOLS = {
    "NASDAQ100":    "^NDX",
    "S&P500":       "^GSPC",
    "ダウ平均":     "^DJI",
    "SOX":          "^SOX",
    "VIX":          "^VIX",
    "WTI原油":      "CL=F",
    "金(XAUUSD)":   "GC=F",
    "ドル円":       "JPY=X",
    "日経225":      "^N225",
    "日経CME先物":  "NKD=F",
    "TOPIX":        "1306.T",
}

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
    "日経CME先物":  "ドル建てCME先物。^N225終値との差分でGU/GD予測に使う",
    "TOPIX":        "ETF(1306)経由の概算値",
}


def jst_now() -> str:
    jst = pytz.timezone("Asia/Tokyo")
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")


def fetch_symbol(name: str, ticker_str: str) -> dict:
    base = {
        "name": name, "ticker": ticker_str,
        "close": None, "prev_close": None, "change_pct": None,
        "data_date": None, "source": None,
        "comment": COMMENTS.get(name, ""), "status": "NO_DATA",
    }

    # 方法1: fast_info（最新値・最優先）
    try:
        ticker = yf.Ticker(ticker_str)
        fi = ticker.fast_info
        last_price = fi.last_price
        prev_close = fi.previous_close
        if last_price is not None and prev_close is not None and prev_close != 0:
            change_pct = round((last_price - prev_close) / prev_close * 100, 2)
            base.update({
                "close": round(float(last_price), 2),
                "prev_close": round(float(prev_close), 2),
                "change_pct": change_pct,
                "source": "fast_info", "status": "OK",
            })
            return base
    except Exception as e:
        base["status"] = f"fast_info_failed: {str(e)[:50]}"

    # 方法2: 日足フォールバック
    try:
        ticker = yf.Ticker(ticker_str)
        hist = ticker.history(period="5d", interval="1d")
        if hist.empty:
            base["status"] = "NO_DATA"
            return base
        close = round(float(hist["Close"].iloc[-1]), 2)
        data_date = hist.index[-1].strftime("%Y-%m-%d")
        if len(hist) >= 2:
            prev_close = round(float(hist["Close"].iloc[-2]), 2)
            change_pct = round((close - prev_close) / prev_close * 100, 2)
        else:
            prev_close = None
            change_pct = None
        base.update({
            "close": close, "prev_close": prev_close, "change_pct": change_pct,
            "data_date": data_date, "source": "daily_history", "status": "OK",
        })
        return base
    except Exception as e:
        base["status"] = f"ERROR: {str(e)[:80]}"
        return base


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
            date_tag = f" [{row['data_date']}]" if row.get("data_date") else ""
            print(f"  OK {name:15s} {row['close']:>12,.2f}  "
                  f"({sign}{row['change_pct']}%)  src={row['source']}{date_tag}")
        else:
            print(f"  NG {name:15s} {row['status']}")
            errors.append(name)

    output = {
        "fetched_at": fetched_at,
        "status": "OK" if not errors else f"PARTIAL_ERROR: {errors}",
        "note": (
            "fast_info.last_priceを優先取得（市場クローズ後はその日の終値）。"
            "sourceがfast_infoなら最新値、daily_historyならdata_date日の終値。"
            "change_pctは前営業日終値比。statusがOK以外はweb検索で補完。"
        ),
        "macro": results,
    }
    with open("macro_result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[fetch_macro] 完了 → macro_result.json 出力")
    print(f"  取得成功: {len(results) - len(errors)}/{len(results)} シンボル")
    if errors:
        print(f"  取得失敗: {errors}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
