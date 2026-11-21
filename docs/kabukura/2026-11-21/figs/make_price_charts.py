"""Price-based charts (real data via yfinance) for kabukura 2026-11-21 handout.

Usage: python3 make_price_charts.py
  -> downloads closes (auto_adjust=True: splits/dividends adjusted),
     writes prices.csv and fig5..fig7 SVGs next to this script.
     python3 make_price_charts.py --cached  re-uses prices.csv instead.
"""
import logging
import os
import sys
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*findfont.*")
warnings.filterwarnings("ignore", message=".*Glyph.*missing.*")

OUT = os.path.dirname(os.path.abspath(__file__))

NAVY = "#1F3A5F"
RED = "#C0392B"
ORANGE = "#E67E22"
GREEN = "#2E8B57"
GRAY = "#8A94A6"
LIGHT = "#EEF2F7"
GRID = "#DDE2EA"
TEXT = "#222222"

plt.rcParams.update({
    "font.family": ["Meiryo UI", "IPAGothic"],
    "svg.fonttype": "none",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#666666",
    "axes.linewidth": 0.7,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "text.color": TEXT,
    "axes.labelcolor": "#444444",
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "svg.hashsalt": "kabukura-20261121",
})

TICKERS = ["^N225", "^GSPC", "^SOX", "1357.T", "1360.T", "2249.T", "SOXS",
           "1570.T", "SOXL"]
DL_START = "2026-05-15"   # warm-up so the 25-day MA exists well before 9/1
START = "2026-06-01"
END = "2026-11-20"
CSV = os.path.join(OUT, "prices.csv")


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), format="svg", bbox_inches="tight",
                pad_inches=0.04, metadata={"Date": None})
    plt.close(fig)


def load(cached=False):
    if cached and os.path.exists(CSV):
        return pd.read_csv(CSV, index_col=0, parse_dates=True)
    import yfinance as yf
    df = yf.download(TICKERS, start=DL_START, end="2026-11-21", progress=False,
                     auto_adjust=True)["Close"]
    df = df[TICKERS]
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Date"
    df.round(4).to_csv(CSV)
    return df


def pair(c, a, b, start=START):
    """Align two series on their own common trading dates."""
    return c[[a, b]].dropna().loc[start:END]


def pct(x):
    return f"{x:+.1f}%"


def month_axis(ax, fmt="%-m月"):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))


def md(ts):
    return f"{ts.month}/{ts.day}"


# ---------------------------------------------------------------- fig5
PAIRS5 = [
    ("^N225", "1357.T", "日経平均", "1357 日経ダブルインバース（-2倍）"),
    ("^N225", "1360.T", "日経平均", "1360 日経平均ベア2倍（-2倍）"),
    ("^GSPC", "2249.T", "S&P500", "2249 S&P500ダブルインバース（-2倍）"),
    ("^SOX", "SOXS", "SOX指数", "SOXS 半導体ベア3倍（-3倍）"),
]


def fig5(c, stats):
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.4))
    for ax, (ix, etf, iname, ename) in zip(axes.flat, PAIRS5):
        lagged = etf.endswith(".T") and not ix == "^N225"
        if lagged:
            # Tokyo-listed ETF on a US index: its Tokyo close on day t trades
            # against the previous NY close, so pair it with the last index
            # close strictly before t (own-date pairing gives corr ~ -0.14).
            si, se = c[ix].dropna(), c[etf].dropna()
            se = se[se.index > si.index[0]]
            m = pd.DataFrame({ix: [si.loc[:t - pd.Timedelta(days=1)].iloc[-1]
                                   for t in se.index], etf: se.values},
                             index=se.index).loc[START:END]
            corr = m.pct_change().dropna().corr().iloc[0, 1]
            # plot each series on its own calendar, both based at 6/1 close
            si = si.loc[START:END]
            se = se.loc[START:END]
            d = pd.concat([si, se], axis=1, sort=True)
            n = pd.concat([si / si.iloc[0] * 100, se / se.iloc[0] * 100], axis=1, sort=True)
        else:
            d = pair(c, ix, etf)
            n = d / d.iloc[0] * 100
            corr = d.pct_change().dropna().corr().iloc[0, 1]
        di, de = d[ix].dropna(), d[etf].dropna()
        ni, ne = n[ix].dropna(), n[etf].dropna()
        hi = di.idxmax()
        stats[etf] = dict(start=di.index[0], i0=di.iloc[0], e0=de.iloc[0],
                          i1=di.iloc[-1], e1=de.iloc[-1],
                          ir=ni.iloc[-1] - 100, er=ne.iloc[-1] - 100,
                          hi=hi, hiv=di.max(), corr=corr, n=len(de),
                          lagged=lagged)
        ax.axhline(100, color=GRAY, lw=0.7, ls=(0, (3, 2)), zorder=1)
        ax.plot(ni.index, ni, color=NAVY, lw=1.5, zorder=3)
        ax.plot(ne.index, ne, color=RED, lw=1.5, zorder=3)
        lo = min(n.min()) ; up = max(n.max())
        pad = (up - lo) * 0.08
        ax.set_ylim(lo - pad * 2.6, up + pad * 1.6)
        ax.axvline(hi, color=GRAY, lw=0.9, ls=(0, (1, 1.5)), zorder=2)
        ax.text(hi + pd.Timedelta(days=2), up + pad * 1.35,
                f"指数の高値（{md(hi)}）", fontsize=7.5, color="#555555",
                va="top", ha="left")
        # end labels
        x_end = n.index[-1] + pd.Timedelta(days=4)
        ie, ee = ni.iloc[-1], ne.iloc[-1]
        ax.text(x_end, ie, f"指数 {ie:.0f}", color=NAVY, fontsize=8,
                fontweight="bold", va="center", ha="left")
        ax.text(x_end, ee, f"ETF {ee:.0f}", color=RED, fontsize=8,
                fontweight="bold", va="center", ha="left")
        ctxt = f"日次騰落率の相関 {corr:.3f}"
        if lagged:
            ctxt += "（前日NY終値比）"
        ax.text(0.02, 0.04, ctxt,
                transform=ax.transAxes, fontsize=7.5, color="#444444",
                ha="left", va="bottom",
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
        ax.set_xlim(n.index[0] - pd.Timedelta(days=2),
                    n.index[-1] + pd.Timedelta(days=30))
        month_axis(ax)
        ax.set_ylabel("基準=100")
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_title(f"{iname} vs {ename}", loc="left", fontsize=9,
                     fontweight="bold", color=NAVY, pad=4)
    h = [Line2D([], [], color=NAVY, lw=1.8), Line2D([], [], color=RED, lw=1.8)]
    fig.legend(h, ["指数（各パネル見出しの左側）", "ベアETF"], loc="upper center",
               ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.04), fontsize=8.5)
    fig.subplots_adjust(wspace=0.25, hspace=0.42)
    save(fig, "fig5_inverse_compare.svg")


# ---------------------------------------------------------------- fig6
ITEMS6 = [  # (ticker, label, kind)
    ("^N225", "日経平均", "index"),
    ("1570.T", "1570 日経レバ（ブル2倍）", "bull"),
    ("1357.T", "1357 ダブルインバース（ベア2倍）", "bear"),
    ("1360.T", "1360 日経平均ベア2倍", "bear"),
    ("^GSPC", "S&P500", "index"),
    ("2249.T", "2249 S&P500ベア2倍", "bear"),
    ("^SOX", "SOX指数", "index"),
    ("SOXL", "SOXL 半導体ブル3倍", "bull"),
    ("SOXS", "SOXS 半導体ベア3倍", "bear"),
]


def fig6(c, stats):
    col = {"index": GRAY, "bull": NAVY, "bear": GREEN}
    vals = []
    for t, _, _ in ITEMS6:
        s = c[t].dropna().loc[:END]
        assert s.index[-1] == pd.Timestamp(END), t
        v = (s.iloc[-1] / s.iloc[-2] - 1) * 100
        stats.setdefault("1d", {})[t] = (v, s.index[-2], s.iloc[-2], s.iloc[-1])
        vals.append(v)
    # group gaps
    ys, y = [], 0.0
    for i, (t, _, k) in enumerate(ITEMS6):
        if i and k == "index":
            y += 0.55
        ys.append(y)
        y += 1
    fig, ax = plt.subplots(figsize=(2.3, 2.8))
    ax.barh(ys, vals, color=[col[k] for _, _, k in ITEMS6], height=0.66,
            zorder=2)
    for yy, v in zip(ys, vals):
        off = 1.0 if v >= 0 else -1.0
        ax.text(v + off, yy, f"{v:+.1f}%", va="center",
                ha="left" if v >= 0 else "right", fontsize=8, color=TEXT)
    ax.set_yticks(ys)
    ax.set_yticklabels([lab for _, lab, _ in ITEMS6], fontsize=8)
    for lab, (_, _, k) in zip(ax.get_yticklabels(), ITEMS6):
        if k == "index":
            lab.set_fontweight("bold")
    ax.invert_yaxis()
    m = max(abs(v) for v in vals)
    ax.set_xlim(-m - 26, m + 19)
    ax.set_xticks([-30, 0, 30])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x:.0f}"))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(0, color="#666666", lw=0.7, zorder=3)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("11/20の騰落率（%）")
    h = [plt.Rectangle((0, 0), 1, 1, color=col[k]) for k in ("index", "bull", "bear")]
    ax.legend(h, ["指数", "ブル型（レバレッジ）", "ベア型（インバース）"],
              loc="upper center", bbox_to_anchor=(0.12, 1.16), ncol=3,
              frameon=False, fontsize=7.5, handlelength=1.0, columnspacing=0.8,
              handletextpad=0.4)
    save(fig, "fig6_bull_bear_1day.svg")


# ---------------------------------------------------------------- fig7
def story(c, ix, etf, story_start="2026-09-01"):
    d = c[[ix, etf]].dropna().loc[:END]
    ma = d[ix].rolling(25).mean()
    w = d.loc[story_start:]
    hi = w[ix].idxmax()                      # most recent major high
    after = w.loc[hi:]
    brk = after.index[(after[ix] < ma.loc[after.index]).values][0]
    entry = d.index[d.index.get_loc(brk) + 1]  # next trading day (close)
    return dict(d=w, ma=ma.loc[story_start:], hi=hi, brk=brk, entry=entry,
                ie=d.loc[entry, ix], ee=d.loc[entry, etf],
                i1=d[ix].iloc[-1], e1=d[etf].iloc[-1],
                ir=(d[ix].iloc[-1] / d.loc[entry, ix] - 1) * 100,
                er=(d[etf].iloc[-1] / d.loc[entry, etf] - 1) * 100,
                hiv=d.loc[hi, ix], brkv=d.loc[brk, ix], brkma=ma.loc[brk])


def fig7(c, stats):
    specs = [("^N225", "1357.T", "日経平均", "1357（ベア2倍）", "日経平均（円）",
              "1357（円）", lambda x, p: f"{x:,.0f}"),
             ("^SOX", "SOXS", "SOX指数", "SOXS（ベア3倍）", "SOX指数",
              "SOXS（ドル）", lambda x, p: f"{x:,.0f}")]
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.5))
    for ax, (ix, etf, iname, ename, il, el, fmt) in zip(axes, specs):
        s = story(c, ix, etf)
        stats["story_" + etf] = s
        d = s["d"]
        ax.plot(d.index, s["ma"], color=GRAY, lw=1.0, ls=(0, (3, 1.5)), zorder=2)
        ax.plot(d.index, d[ix], color=NAVY, lw=1.6, zorder=3)
        ax.set_ylabel(il, color=NAVY)
        ax.yaxis.set_major_formatter(FuncFormatter(fmt))
        ax.tick_params(axis="y", colors=NAVY)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        a2 = ax.twinx()
        a2.spines["right"].set_visible(True)
        a2.spines["top"].set_visible(False)
        a2.plot(d.index, d[etf], color=RED, lw=1.6, zorder=3)
        a2.set_ylabel(el, color=RED)
        a2.tick_params(axis="y", colors=RED)
        # recent high
        ax.plot([s["hi"]], [s["hiv"]], marker="v", ms=5, color=NAVY, zorder=5)
        ax.annotate(f"直近高値 {md(s['hi'])}", xy=(s["hi"], s["hiv"]),
                    xytext=(-4, 3), textcoords="offset points", ha="right",
                    va="bottom", fontsize=7.5, color=NAVY)
        # entry
        e = s["entry"]
        ax.axvline(e, color="#555555", lw=0.9, ls=(0, (1, 1.5)), zorder=2)
        ax.plot([e], [s["ie"]], marker="o", ms=4.5, color=NAVY, zorder=6)
        a2.plot([e], [s["ee"]], marker="o", ms=5.5, color=RED, mec="white",
                mew=0.8, zorder=6)
        a2.plot([d.index[-1]], [s["e1"]], marker="o", ms=4, color=RED, zorder=6)
        ax.plot([d.index[-1]], [s["i1"]], marker="o", ms=4, color=NAVY, zorder=6)
        ax.text(e + pd.Timedelta(days=1.5), 0.03, f"買い {md(e)}",
                transform=ax.get_xaxis_transform(), fontsize=7.5,
                color="#333333", ha="left", va="bottom", fontweight="bold")
        # result line under the panel header
        ax.text(0.0, 1.03, f"{md(e)}買い→{md(d.index[-1])}：", transform=ax.transAxes,
                fontsize=8, color="#333333", ha="left", va="bottom")
        ax.annotate(f"{ename.split('（')[0]} {pct(s['er'])}", xy=(1, 0),
                    xycoords=ax.texts[-1], xytext=(2, 0),
                    textcoords="offset points", fontsize=8.5, color=RED,
                    fontweight="bold", ha="left", va="bottom")
        ax.annotate(f"（{iname} {pct(s['ir'])}）", xy=(1, 0),
                    xycoords=ax.texts[-1], xytext=(3, 0),
                    textcoords="offset points", fontsize=8, color=NAVY,
                    ha="left", va="bottom")
        month_axis(ax)
        ax.set_xlim(d.index[0] - pd.Timedelta(days=1),
                    d.index[-1] + pd.Timedelta(days=2))
        lo, up = d[ix].min(), d[ix].max()
        ax.set_ylim(lo - (up - lo) * 0.55, up + (up - lo) * 0.12)
        elo, eup = d[etf].min(), d[etf].max()
        a2.set_ylim(elo - (eup - elo) * 0.14, eup + (eup - elo) * 0.08)
        ax.set_title(f"{iname}と{ename}", loc="left", fontsize=9,
                     fontweight="bold", color=NAVY, pad=17)
    h = [Line2D([], [], color=NAVY, lw=1.8),
         Line2D([], [], color=GRAY, lw=1.0, ls=(0, (3, 1.5))),
         Line2D([], [], color=RED, lw=1.8)]
    fig.legend(h, ["指数（左軸）", "指数の25日移動平均", "ベアETF（右軸）"],
               loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.16), fontsize=8.5)
    fig.subplots_adjust(wspace=0.62)
    save(fig, "fig7_bear_story.svg")


def report(c, st):
    print("rows:", c.loc[START:END].count().to_dict())
    for etf, v in st.items():
        if etf in ("1d",) or etf.startswith("story"):
            continue
        print(f"{etf}: {md(v['start'])}->11/20 n={v['n']} idx {v['i0']:.2f}->{v['i1']:.2f} "
              f"({v['ir']:+.1f}%), etf {v['e0']:.2f}->{v['e1']:.2f} ({v['er']:+.1f}%), "
              f"idx high {v['hi'].date()} {v['hiv']:.2f}, corr {v['corr']:.3f} lagged={v['lagged']}")
    for t, (v, pd_, p0, p1) in st["1d"].items():
        print(f"1d {t}: {pd_.date()} {p0:.2f} -> {p1:.2f} = {v:+.2f}%")
    for k in ("story_1357.T", "story_SOXS"):
        s = st[k]
        print(f"{k}: high {s['hi'].date()} {s['hiv']:.2f}; close<MA25 on {s['brk'].date()} "
              f"({s['brkv']:.2f} < {s['brkma']:.2f}); entry {s['entry'].date()} idx {s['ie']:.2f} "
              f"etf {s['ee']:.2f}; 11/20 idx {s['i1']:.2f} etf {s['e1']:.2f}; "
              f"idx {s['ir']:+.1f}% etf {s['er']:+.1f}%")


if __name__ == "__main__":
    c = load(cached="--cached" in sys.argv)
    st = {}
    fig5(c, st)
    fig6(c, st)
    fig7(c, st)
    report(c, st)
