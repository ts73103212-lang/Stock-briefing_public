"""
briefing.py  ―  デイトレ朝夕ブリーフィング生成スクリプト
Claude Routines から実行される。
  - 7:40 JST : 朝ブリーフィング (A+B+C)
  - 18:00 JST : 夕振り返り    (A+B+C+D)

依存: yfinance, pandas, requests
"""

import yfinance as yf
import pandas as pd
import requests
import io
import json
import sys
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────
# 0. 設定
# ─────────────────────────────────────────

JST = timezone(timedelta(hours=9))
NOW = datetime.now(JST)
TODAY_STR = NOW.strftime("%Y-%m-%d")
IS_EVENING = NOW.hour >= 15          # 15時以降 → 夕方モード

# ★ 保有銘柄 ― 銘柄変更時にここだけ編集する
HOLDINGS = [
    {"code": "6613", "name": "QDレーザ",    "shares": 200, "cost": 1600},
    {"code": "2667", "name": "イメージワン", "shares": 200, "cost": 254},
    # 例: {"code": "6920", "name": "レーザーテック", "shares": 100, "cost": 18000},
]

# ─────────────────────────────────────────
# 1. マクロデータ取得 (yfinance)
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
        try:
            hist = yf.Ticker(sym).history(period="3d", auto_adjust=True)
            if len(hist) < 1:
                continue
            close = hist["Close"].iloc[-1]
            prev  = hist["Close"].iloc[-2] if len(hist) >= 2 else close
            chg_pct = (close - prev) / prev * 100 if prev else 0
            high52 = hist["High"].max()  # 3日だが参考値
            rows.append({
                "名称": name,
                "終値": round(close, 2),
                "前日比%": round(chg_pct, 2),
            })
        except Exception as e:
            rows.append({"名称": name, "終値": "取得失敗", "前日比%": "-"})
    return rows

# ─────────────────────────────────────────
# 2. 保有銘柄データ取得 (yfinance)
# ─────────────────────────────────────────

def fetch_holdings_data():
    results = []
    for h in HOLDINGS:
        sym = h["code"] + ".T"
        try:
            ticker = yf.Ticker(sym)
            hist   = ticker.history(period="10d", auto_adjust=True)
            if len(hist) < 2:
                continue

            close  = hist["Close"].iloc[-1]
            prev   = hist["Close"].iloc[-2]
            vol    = hist["Volume"].iloc[-1]
            vol5   = hist["Volume"].tail(5).mean()
            chg    = (close - prev) / prev * 100

            # MA計算
            ma5    = hist["Close"].tail(5).mean()
            ma25   = hist["Close"].tail(min(25, len(hist))).mean()
            vs_ma5 = (close - ma5) / ma5 * 100

            # 評価損益
            pnl_pct = (close - h["cost"]) / h["cost"] * 100
            pnl_yen = (close - h["cost"]) * h["shares"]

            # 相場サイクルの簡易判定
            # MA5 > MA25 かつ close > MA5 → 上昇トレンド継続
            if ma5 > ma25 and close > ma5:
                cycle = "②上昇トレンド"
            elif ma5 < ma25 and close < ma5:
                cycle = "④下降トレンド"
            else:
                cycle = "③ディストリビューション候補"

            results.append({
                "code":     h["code"],
                "name":     h["name"],
                "close":    round(close, 1),
                "chg_pct":  round(chg, 2),
                "volume":   int(vol),
                "vol_ratio":round(vol / vol5, 2) if vol5 else 0,
                "ma5":      round(ma5, 1),
                "ma25":     round(ma25, 1),
                "vs_ma5":   round(vs_ma5, 2),
                "cycle":    cycle,
                "cost":     h["cost"],
                "shares":   h["shares"],
                "pnl_pct":  round(pnl_pct, 2),
                "pnl_yen":  round(pnl_yen, 0),
            })
        except Exception as e:
            results.append({"code": h["code"], "name": h["name"], "error": str(e)})
    return results

# ─────────────────────────────────────────
# 3. JPX公開データ → 急騰ランキング上位50
# ─────────────────────────────────────────

JPX_CSV_URL = (
    "https://www.jpx.co.jp/markets/statistics-equities/daily/"
    "nlsgeu0000008axv-att/data_j.csv"
)

def fetch_jpx_ranking(top_n=50):
    """
    JPX 上場銘柄一覧CSV (前営業日分) から
    出来高上位・騰落率上位の銘柄を抽出する。
    
    ※ JPXのCSVフォーマットは変更されることがある。
      カラム名が変わった場合は下記マッピングを修正する。
    """
    try:
        resp = requests.get(JPX_CSV_URL, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = "cp932"   # Shift-JIS系
        df = pd.read_csv(io.StringIO(resp.text))

        # カラム名の正規化 (スペース除去)
        df.columns = df.columns.str.strip()

        # 必要カラムの確認とリネーム
        # JPXのCSVカラム例: コード, 銘柄名, 市場・商品区分, 終値, 前日終値, 騰落率, 出来高
        col_map = {}
        for c in df.columns:
            if "コード"  in c: col_map[c] = "code"
            if "銘柄"    in c: col_map[c] = "name"
            if "騰落"    in c: col_map[c] = "chg_pct"
            if "出来高"  in c: col_map[c] = "volume"
            if "終値"    in c and "前日" not in c: col_map[c] = "close"
            if "前日終値" in c: col_map[c] = "prev_close"
            if "売買代金" in c: col_map[c] = "turnover"
        df = df.rename(columns=col_map)

        # 数値変換
        for col in ["chg_pct", "volume", "close", "turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",", "").str.replace("%", ""),
                    errors="coerce"
                )

        df = df.dropna(subset=["close"])

        # プライム・スタンダード・グロース市場のみ
        if "market" in df.columns:
            df = df[df["market"].str.contains("プライム|スタンダード|グロース", na=False)]

        # 出来高急増ランキング (売買代金で代替)
        vol_col = "turnover" if "turnover" in df.columns else "volume"
        top_volume = (
            df.nlargest(top_n, vol_col)[["code", "name", "close", "chg_pct", vol_col]]
            .to_dict("records")
        )

        # 騰落率ランキング
        top_gainers = (
            df[df["chg_pct"] > 0]
            .nlargest(top_n, "chg_pct")[["code", "name", "close", "chg_pct", vol_col]]
            .to_dict("records")
        )

        return {"volume_ranking": top_volume, "gainer_ranking": top_gainers}

    except Exception as e:
        return {"error": str(e), "volume_ranking": [], "gainer_ranking": []}

# ─────────────────────────────────────────
# 4. データをまとめてJSON出力
# ─────────────────────────────────────────

def build_context():
    print("📡 マクロデータ取得中...", file=sys.stderr)
    macro = fetch_macro()

    print("📊 保有銘柄データ取得中...", file=sys.stderr)
    holdings = fetch_holdings_data()

    print("🏦 JPXランキング取得中...", file=sys.stderr)
    jpx = fetch_jpx_ranking(top_n=50)

    ctx = {
        "date":            TODAY_STR,
        "time":            NOW.strftime("%H:%M"),
        "session":         "evening" if IS_EVENING else "morning",
        "macro":           macro,
        "holdings":        holdings,
        "volume_ranking":  jpx.get("volume_ranking", [])[:50],
        "gainer_ranking":  jpx.get("gainer_ranking", [])[:50],
        "jpx_error":       jpx.get("error"),
    }
    return ctx

if __name__ == "__main__":
    ctx = build_context()
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
