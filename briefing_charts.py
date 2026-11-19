"""briefing_charts.py ── デイトレブリーフィング用の週足/日足チャート（出来高付き）を PNG で書き出す。

使い方:
    python briefing_charts.py 9048 1926 197A 4071            # → charts/<code>.png
    python briefing_charts.py --from-json screening_result.json --top 5
    python briefing_charts.py 9048 1926 --combined           # → charts/combined.png（1枚にまとめる）
    python briefing_charts.py --from-json screening_result.json --top 10 --clean   # 朝の GitHub Actions 用

charts/manifest.json に、銘柄ごとの「ファイル名・最終足の日付・sha256」を書き出す
（ルーティンが Gmail のインライン添付に使う）。

1銘柄 = 横並び2面（左: 週足 約1年＋13/26週EMA、右: 日足 約4か月＋EMA5/25）、下段に出来高。
メール本文に cid 画像として貼る前提で、幅1200px・PNG（1枚 60〜90KB 程度）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

UP, DOWN, NAVY, GOLD, GRID, MUTED = "#16A34A", "#DC2626", "#1E3A5F", "#D4A017", "#E5E1D8", "#5E6470"


def setup_font() -> None:
    try:
        from note_pipeline.fonts import ensure_fonts
        ensure_fonts()
    except Exception:
        matplotlib.rcParams["font.family"] = ["IPAGothic", "Noto Sans CJK JP", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False


OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def _download(code: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(f"{code}.T", period=period, interval=interval, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[OHLCV].dropna()


def fetch(code: str, latest: dict | None = None) -> tuple[pd.DataFrame, list[str]]:
    """日足（約14か月）を返す。

    早朝（6時台）は Yahoo の日足に前営業日の足がまだ載っていないことがある（2026-11-19 に発生）。
    そのときは 60分足から欠けた日の足を組み立てて補う。60分足には引けの板寄せが入らないので、
    最新足の終値・出来高は latest（スクリーニング JSON の close / volume）があればそちらを使う。
    戻り値: (日足, 補完した日付のリスト)
    """
    d = _download(code, "14mo", "1d")
    try:
        h = _download(code, "5d", "60m")
    except Exception as e:  # 補完できなくても日足だけで描く
        print(f"WARN {code}: 60分足取得失敗 {e}", file=sys.stderr)
        return d, []
    if h.empty:
        return d, []
    if h.index.tz is not None:
        h.index = h.index.tz_convert("Asia/Tokyo").tz_localize(None)
    last_daily = d.index[-1].normalize() if len(d) else pd.Timestamp.min
    h = h[h.index.normalize() > last_daily]
    if h.empty:
        return d, []
    bars = h.groupby(h.index.normalize()).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
    if latest and latest.get("close"):
        i = bars.index[-1]
        c = float(latest["close"])
        bars.loc[i, "Close"] = c
        bars.loc[i, "High"] = max(bars.loc[i, "High"], c)
        bars.loc[i, "Low"] = min(bars.loc[i, "Low"], c)
        if latest.get("volume"):
            bars.loc[i, "Volume"] = float(latest["volume"])
    bars.index.name = d.index.name
    return pd.concat([d, bars[OHLCV]]), [t.strftime("%Y-%m-%d") for t in bars.index]


def to_weekly(d: pd.DataFrame) -> pd.DataFrame:
    return d.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min",
                                    "Close": "last", "Volume": "sum"}).dropna()


def draw(ax, axv, df: pd.DataFrame, emas: tuple[int, int], title: str, date_fmt: str) -> None:
    x = range(len(df))
    up = df["Close"] >= df["Open"]
    col = [UP if u else DOWN for u in up]
    ax.vlines(x, df["Low"], df["High"], color=col, linewidth=0.8)
    body_lo = df[["Open", "Close"]].min(axis=1)
    body_h = (df["Close"] - df["Open"]).abs().clip(lower=df["Close"].mean() * 0.0008)
    ax.bar(x, body_h, bottom=body_lo, color=col, width=0.65)
    for n, c in zip(emas, (GOLD, NAVY)):
        ax.plot(x, df["Close"].ewm(span=n, adjust=False).mean(), color=c, linewidth=1.3,
                label=f"EMA{n}")
    last = df["Close"].iloc[-1]
    ax.axhline(last, color=MUTED, linewidth=0.6, linestyle=":")
    ax.annotate(f"¥{last:,.0f}", (len(df) - 1, last), xytext=(4, 0), textcoords="offset points",
                fontsize=8, color=NAVY, va="center")
    ax.set_title(title, fontsize=10, loc="left", color=NAVY, fontweight="bold")
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    axv.bar(x, df["Volume"], color=col, width=0.65, alpha=0.8)
    axv.yaxis.set_major_formatter(lambda v, _: f"{v / 1e4:,.0f}万" if v < 1e8 else f"{v / 1e8:.1f}億")
    step = max(1, len(df) // 6)
    axv.set_xticks(list(x)[::step])
    axv.set_xticklabels([d.strftime(date_fmt) for d in df.index[::step]], fontsize=7)
    for a in (ax, axv):
        a.grid(color=GRID, linewidth=0.6)
        a.tick_params(labelsize=7)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        a.set_xlim(-1, len(df) + 3)
    ax.tick_params(labelbottom=False)


def render(code: str, name: str, out: Path, latest: dict | None = None):
    d, patched = fetch(code, latest)
    if d.empty:
        raise RuntimeError(f"{code}: データ取得失敗")
    w = to_weekly(d).tail(52)
    dd = d.tail(80)
    fig = plt.figure(figsize=(12, 4.2), dpi=100)
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.05, wspace=0.12,
                          left=0.05, right=0.97, top=0.86, bottom=0.08)
    head = f"{code} {name}".strip()
    fig.suptitle(f"{head}　終値 ¥{d['Close'].iloc[-1]:,.0f}（{d.index[-1]:%m/%d}）",
                 x=0.05, ha="left", fontsize=12, fontweight="bold", color=NAVY)
    draw(fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0]), w, (13, 26), "週足（約1年）", "%y/%m")
    draw(fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1]), dd, (5, 25), "日足（約4か月）", "%m/%d")
    fig.text(0.97, 0.01, "出典: Yahoo!ファイナンス（yfinance）", ha="right", fontsize=7, color=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png", facecolor="white")
    plt.close(fig)
    return out, d.index[-1].strftime("%Y-%m-%d"), patched


def combine(paths: list[Path], out: Path) -> Path:
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    canvas = Image.new("RGB", (max(i.width for i in ims), sum(i.height for i in ims)), "white")
    y = 0
    for im in ims:
        canvas.paste(im, (0, y))
        y += im.height
    canvas.save(out, optimize=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*")
    ap.add_argument("--from-json")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--names", default="", help="code=名前,code=名前 ...")
    ap.add_argument("--out", default="charts")
    ap.add_argument("--combined", action="store_true")
    ap.add_argument("--clean", action="store_true", help="出力先の既存PNGを消してから作る")
    a = ap.parse_args()
    codes = list(a.codes)
    latest: dict[str, dict] = {}  # スクリーニング JSON の終値・出来高（最新足の補完用）
    if a.from_json:
        stocks = json.load(open(a.from_json))["stocks"][: a.top]
        codes += [s["ticker"] for s in stocks]
        latest = {s["ticker"]: s for s in stocks}
    names = dict(kv.split("=", 1) for kv in a.names.split(",") if "=" in kv)
    setup_font()
    out_dir = Path(a.out)
    if a.clean and out_dir.exists():
        for old in out_dir.glob("*.png"):
            old.unlink()
    done, manifest = [], {}
    for c in codes:
        try:
            p, last, patched = render(c, names.get(c, ""), out_dir / f"{c}.png", latest.get(c))
            done.append(p)
            manifest[c] = {"file": p.name, "last_bar": last,
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            if patched:  # Yahoo 日足に無かった日を60分足（＋スクリーニング終値）で補った
                manifest[c]["patched_bars"] = patched
            print(f"{p}  last_bar={last}" + (f"  patched={patched}" if patched else ""))
        except Exception as e:  # 1銘柄の失敗で全体を止めない
            print(f"SKIP {c}: {e}", file=sys.stderr)
    if done:
        jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M JST")
        (out_dir / "manifest.json").write_text(json.dumps(
            {"generated_at": jst, "charts": manifest}, ensure_ascii=False, indent=1))
    if a.combined and done:
        print(combine(done, Path(a.out) / "combined.png"))


if __name__ == "__main__":
    main()
