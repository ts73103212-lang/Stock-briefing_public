"""
briefing.py  ―  デイトレ朝夕ブリーフィング生成スクリプト
Claude Routines から実行される。
yfinanceライブラリを使わず requests で直接APIを叩く設計。

依存: pandas, requests  (標準ライブラリ + 2つのみ)
"""

import requests
import json
import sys
import io
import time
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────
# 0. 設定
# ─────────────────────────────────────────

JST = timezone(timedelta(hours=9))
NOW = datetime.now(JST)
TODAY_STR = NOW.strftime("%Y-%m-%d")
IS_EVENING = NOW.hour >= 15

# ★ 保有銘柄 ― 銘柄変更時にここだけ編集する
HOLDINGS = [
    {"code": "6613", "name": "QDレーザ",    "shares": 200, "cost": 1600}
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,*/*",
    "Accept-Language": "ja,en;q=0.9",
}

# ─────────────────────────────────────────
# 1. Yahoo Finance Chart API (requests直接)
# ─────────────────────────────────────────

def fetch_yahoo_chart(symbol, days=30):
    """
    Yahoo Finance Chart APIから日足データを取得する。
    戻り値: [{"date":..., "open":..., "high":..., "low":..., "close":..., "volume":...}]
    失敗時: []
    """
    period2 = int(time.time())
    period1 = period2 - days * 24 * 3600 * 2

    for host in ["query1", "query2"]:
        url = (
            f"https://{host}.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?interval=1d&period1={period1}&period2={period2}"
            f"&includePrePost=false"
        )
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            data = r.json()
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            q = result["indicators"]["quote"][0]
            rows = []
            for i, ts in enumerate(timestamps):
                rows.append({
                    "date":   datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                    "open":   q["open"][i],
                    "high":   q["high"][i],
                    "low":    q["low"][i],
                    "close":  q["close"][i],
                    "volume": q["volume"][i],
                })
            rows = [row for row in rows if row["close"] is not None][-days:]
            return rows
        except Exception:
            continue
    return []


def calc_ma(rows, n):
    closes = [r["close"] for r in rows if r["close"] is not None]
    if len(closes) < n:
        return None
    return round(sum(closes[-n:]) / n, 2)


def calc_vol_ratio(rows, n=5):
    vols = [r["volume"] for r in rows if r["volume"] is not None]
    if len(vols) < n + 1:
        return None
    avg = sum(vols[-n-1:-1]) / n
    if avg == 0:
        return None
    return round(vols[-1] / avg, 2)

# ─────────────────────────────────────────
# 2. マクロデータ取得
# ─────────────────────────────────────────

MACRO_SYMBOLS = {
    "日経225":    "^N225",
    "TOPIX":     "^TPX",
    "NASDAQ100": "^NDX",
    "SOX":       "^SOX",
    "VIX":       "^VIX",
    "WTI原油":   "CL=F",
    "Gold":      "GC=F",
    "ドル円":    "USDJPY=X",
    "米10年債":  "^TNX",
}

def fetch_macro():
    rows = []
    for name, sym in MACRO_SYMBOLS.items():
        data = fetch_yahoo_chart(sym, days=5)
        if len(data) >= 2:
            close = data[-1]["close"]
            prev  = data[-2]["close"]
            chg   = round((close - prev) / prev * 100, 2) if prev else 0
            rows.append({"名称": name, "終値": round(close, 2), "前日比%": chg})
        elif len(data) == 1:
            rows.append({"名称": name, "終値": round(data[-1]["close"], 2), "前日比%": None})
        else:
            rows.append({"名称": name, "終値": "取得失敗", "前日比%": None})
        time.sleep(0.3)
    return rows

# ─────────────────────────────────────────
# 3. 保有銘柄データ取得
# ─────────────────────────────────────────

def fetch_holdings_data():
    results = []
    for h in HOLDINGS:
        sym  = h["code"] + ".T"
        data = fetch_yahoo_chart(sym, days=30)
        if len(data) < 2:
            results.append({"code": h["code"], "name": h["name"], "error": "データ取得失敗"})
            continue

        close     = data[-1]["close"]
        prev      = data[-2]["close"]
        chg       = round((close - prev) / prev * 100, 2) if prev else 0
        ma5       = calc_ma(data, 5)
        ma25      = calc_ma(data, 25)
        vol_ratio = calc_vol_ratio(data, 5)
        vs_ma5    = round((close - ma5) / ma5 * 100, 2) if ma5 else None
        pnl_pct   = round((close - h["cost"]) / h["cost"] * 100, 2)
        pnl_yen   = round((close - h["cost"]) * h["shares"], 0)

        if ma5 and ma25:
            if ma5 > ma25 and close > ma5:
                cycle = "②上昇トレンド"
            elif ma5 < ma25 and close < ma5:
                cycle = "④下降トレンド"
            else:
                cycle = "③ディストリビューション候補"
        else:
            cycle = "判定不可（データ不足）"

        results.append({
            "code":      h["code"],
            "name":      h["name"],
            "close":     round(close, 1),
            "chg_pct":   chg,
            "vol_ratio": vol_ratio,
            "ma5":       ma5,
            "ma25":      ma25,
            "vs_ma5":    vs_ma5,
            "cycle":     cycle,
            "cost":      h["cost"],
            "shares":    h["shares"],
            "pnl_pct":   pnl_pct,
            "pnl_yen":   pnl_yen,
        })
        time.sleep(0.3)
    return results

# ─────────────────────────────────────────
# 4. JPX公開CSV → 急騰・出来高ランキング
# ─────────────────────────────────────────

JPX_CSV_URL = (
    "https://www.jpx.co.jp/markets/statistics-equities/daily/"
    "nlsgeu0000008axv-att/data_j.csv"
)

def fetch_jpx_ranking(top_n=50):
    try:
        import pandas as pd
        r = requests.get(JPX_CSV_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        r.encoding = "cp932"
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = df.columns.str.strip()

        col_map = {}
        for c in df.columns:
            if "コード"   in c: col_map[c] = "code"
            if "銘柄"     in c: col_map[c] = "name"
            if "騰落"     in c: col_map[c] = "chg_pct"
            if "出来高"   in c: col_map[c] = "volume"
            if "終値"     in c and "前日" not in c: col_map[c] = "close"
            if "前日終値" in c: col_map[c] = "prev_close"
            if "売買代金" in c: col_map[c] = "turnover"
        df = df.rename(columns=col_map)

        for col in ["chg_pct", "volume", "close", "turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",","").str.replace("%",""),
                    errors="coerce"
                )
        df = df.dropna(subset=["close"])

        vol_col = "turnover" if "turnover" in df.columns else "volume"
        top_vol  = df.nlargest(top_n, vol_col)[
            ["code","name","close","chg_pct",vol_col]
        ].to_dict("records")
        top_gain = df[df["chg_pct"] > 0].nlargest(top_n, "chg_pct")[
            ["code","name","close","chg_pct",vol_col]
        ].to_dict("records")

        return {"volume_ranking": top_vol, "gainer_ranking": top_gain}

    except Exception as e:
        return {"error": str(e), "volume_ranking": [], "gainer_ranking": []}

# ─────────────────────────────────────────
# 5. まとめてJSON出力
# ─────────────────────────────────────────

def build_context():
    print("📡 マクロデータ取得中...", file=sys.stderr)
    macro = fetch_macro()

    print("📊 保有銘柄データ取得中...", file=sys.stderr)
    holdings = fetch_holdings_data()

    print("🏦 JPXランキング取得中...", file=sys.stderr)
    jpx = fetch_jpx_ranking(top_n=50)

    return {
        "date":           TODAY_STR,
        "time":           NOW.strftime("%H:%M"),
        "session":        "evening" if IS_EVENING else "morning",
        "macro":          macro,
        "holdings":       holdings,
        "volume_ranking": jpx.get("volume_ranking", [])[:50],
        "gainer_ranking": jpx.get("gainer_ranking", [])[:50],
        "jpx_error":      jpx.get("error"),
    }

if __name__ == "__main__":
    ctx = build_context()
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
