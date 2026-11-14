"""briefing_charts.py ── デイトレブリーフィング用の週足/日足チャート（出来高付き）を PNG で書き出す。

使い方:
    python briefing_charts.py 9048 1926 197A 4071            # → charts/<code>.png
    python briefing_charts.py --from-json screening_result.json --top 5
    python briefing_charts.py 9048 1926 --combined           # → charts/combined.png（1枚にまとめる）

1銘柄 = 横並び2面（左: 週足 約1年＋13/26週EMA、右: 日足 約4か月＋EMA5/25）、下段に出来高。
メール本文に cid 画像として貼る前提で、幅1200px・PNG（1枚 60〜90KB 程度）。
"""
from __future__ import annotations

import argparse
import json
import sys
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


def fetch(code: str) -> pd.DataFrame:
    df = yf.download(f"{code}.T", period="14mo", interval="1d", progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


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


def render(code: str, name: str, out: Path) -> Path:
    d = fetch(code)
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
    return out


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
    a = ap.parse_args()
    codes = list(a.codes)
    if a.from_json:
        codes += [s["ticker"] for s in json.load(open(a.from_json))["stocks"][: a.top]]
    names = dict(kv.split("=", 1) for kv in a.names.split(",") if "=" in kv)
    setup_font()
    done = []
    for c in codes:
        try:
            done.append(render(c, names.get(c, ""), Path(a.out) / f"{c}.png"))
            print(done[-1])
        except Exception as e:  # 1銘柄の失敗で全体を止めない
            print(f"SKIP {c}: {e}", file=sys.stderr)
    if a.combined and done:
        print(combine(done, Path(a.out) / "combined.png"))


if __name__ == "__main__":
    main()
