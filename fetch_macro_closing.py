"""
fetch_macro_closing.py
----------------------
引け後（15:40 JST）実行。当日の日本株引け値と各種マクロデータを取得する。
fetch_macro.py・fetch_macro_midday.py とは完全に独立。

【v2修正点】
  - period="2d"の日足取得をやめ、fast_info.last_price（最新値）を主軸にした
  - 大引け15:40取得時、日経225・TOPIXは当日終値が確実に取れる
  - 米国指数は前日終値（米国市場未開場）、先物・為替はリアルタイム最新値
  - last_price取得失敗時のみ日足にフォールバック

取得対象:
  - 日経225・TOPIX ETF（当日終値）
  - 米国指数・SOX（前日終値 ※米国市場未開場のため）
  - ドル円・VIX・WTI原油・金（リアルタイムに近い値）
  - 米国株先物（夕時点のセンチメント）

出力: macro_result_closing.json
実行: python fetch_macro_closing.py
依存: yfinance pytz （pip install yfinance pytz）
"""

import json
import sys
from datetime import datetime

import pytz
import yfinance as yf

SYMBOLS = {
    "日経225":          "^N225",
    "TOPIX(ETF)":       "1306.T",
    "NASDAQ100":        "^NDX",
    "S&P500":           "^GSPC",
    "ダウ平均":         "^DJI",
    "SOX":              "^SOX",
    "ドル円":           "JPY=X",
    "VIX":              "^VIX",
    "WTI原油":          "CL=F",
    "金(XAUUSD)":       "GC=F",
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
    print(f"[fetch_macro_closing] 開始: {fetched_at}")

    for name, ticker_str in SYMBOLS.items():
        row = fetch_symbol(name, ticker_str)
        results.append(row)
        if row["status"] == "OK":
            sign = "+" if (row["change_pct"] or 0) >= 0 else ""
            date_tag = f" [{row['data_date']}]" if row.get("data_date") else ""
            print(f"  OK {name:20s} {row['close']:>12,.2f}  "
                  f"({sign}{row['change_pct']}%)  src={row['source']}{date_tag}")
        else:
            print(f"  NG {name:20s} {row['status']}")
            errors.append(name)

    output = {
        "fetched_at": fetched_at,
        "status": "OK" if not errors else f"PARTIAL_ERROR: {errors}",
        "note": (
            "15:40 JST取得。fast_info.last_price優先。"
            "日経225・TOPIXは当日終値。"
            "米国指数（NASDAQ・S&P500・SOX）は前日終値（米国市場未開場）。"
            "先物・為替・VIXはリアルタイムに近い値。"
            "sourceがfast_infoなら最新値、daily_historyならdata_date日の終値。"
            "statusがOK以外はweb検索で補完すること。"
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
