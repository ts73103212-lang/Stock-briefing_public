"""Margin-trading charts for kabukura 2026-11-21 handout.

Usage: python3 make_margin_charts.py  -> writes fig9_kioxia_margin.svg and
fig10_margin_cycle.svg next to this script.

fig9 data (Kioxia HD, 285A), weekly 信用買い残 (shares, 申込日=Friday):
  - 2026/6/5 - 7/17: IRBANK https://irbank.net/285A/margin (split-adjusted)
  - 2026/7/24 - 11/13: Yahoo!ファイナンス https://finance.yahoo.co.jp/quote/285A.T/margin
    (raw; values before the 2026/9/29 1:3 split are multiplied by 3 here.
    Overlap 7/3-7/17 matches IRBANK exactly after x3.)
  Price: yfinance 285A.T split-adjusted Friday close (fetched 2026-11-21).
"""
import logging
import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*findfont.*")
warnings.filterwarnings("ignore", message=".*Glyph.*missing.*")

OUT = os.path.dirname(os.path.abspath(__file__))

NAVY = "#1F3A5F"
LNAVY = "#8FA6C4"
RED = "#C0392B"
GRAY = "#8A94A6"
LIGHT = "#EEF2F7"
GRID = "#DDE2EA"
TEXT = "#222222"

plt.rcParams.update({
    "font.family": ["Meiryo UI", "IPAGothic"],
    "svg.fonttype": "none",
    "font.size": 9,
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
    "svg.hashsalt": "kabukura-20261121-margin",
})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), format="svg", bbox_inches="tight",
                pad_inches=0.04, metadata={"Date": None})
    plt.close(fig)


def comma(x, _pos=None):
    return f"{x:,.0f}"


# (date, 信用買い残 shares split-adjusted, weekly close yen split-adjusted)
KIOXIA = [
    ("6/5", 40_386_000, 26047), ("6/12", 34_281_300, 27067),
    ("6/19", 32_209_200, 36200), ("6/26", 43_404_000, 30727),
    ("7/3", 39_124_200, 27767), ("7/10", 39_387_000, 25667),
    ("7/17", 41_663_700, 17370), ("7/24", 11_385_700 * 3, 18670),
    ("7/31", 12_321_600 * 3, 15500), ("8/7", 13_231_000 * 3, 15910),
    ("8/14", 12_103_500 * 3, 17913), ("8/21", 13_289_500 * 3, 18107),
    ("8/28", 16_165_800 * 3, 15967), ("9/4", 13_506_700 * 3, 18153),
    ("9/11", 13_943_000 * 3, 18010), ("9/18", 13_486_500 * 3, 18190),
    ("9/25", 13_929_900 * 3, 18593), ("10/2", 41_467_700, 19300),
    ("10/9", 44_798_300, 17505), ("10/16", 47_831_100, 13375),
    ("10/23", 48_234_500, 12755), ("10/30", 47_992_400, 13470),
    ("11/6", 48_227_800, 8511), ("11/13", 49_959_000, 9091),
    ("11/20", None, 7307),  # 11/20 margin balance published 11/25
]


# ---------------------------------------------------------------- fig9
def fig9():
    xs = list(range(len(KIOXIA)))
    bal = [None if b is None else b / 1e4 for _, b, _ in KIOXIA]
    px = [p for _, _, p in KIOXIA]
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    bx = [x for x, b in zip(xs, bal) if b is not None]
    by = [b for b in bal if b is not None]
    ax.bar(bx, by, width=0.72, color=LNAVY, zorder=2, label="信用買い残（左）")
    ax.set_ylim(0, 6000)
    ax.yaxis.set_major_formatter(FuncFormatter(comma))
    ax.set_ylabel("信用買い残（万株）")
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)

    ax2 = ax.twinx()
    ax2.plot(xs, px, color=RED, lw=1.6, marker="o", ms=2.2, zorder=3,
             label="株価（右）")
    ax2.set_ylim(0, 40000)
    ax2.yaxis.set_major_formatter(FuncFormatter(comma))
    ax2.set_ylabel("株価（円）", color=RED)
    ax2.tick_params(axis="y", colors=RED)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(RED)
    ax2.spines["top"].set_visible(False)

    # month ticks: first Friday of each month in the list
    ticks, labels, seen = [], [], set()
    for x, (d, _, _) in enumerate(KIOXIA):
        m = d.split("/")[0]
        if m not in seen:
            seen.add(m)
            ticks.append(x)
            labels.append(f"{m}月")
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_xlim(-0.7, len(xs) - 0.3)

    # annotations
    ax2.annotate("6/19 36,200円", xy=(2, 36200), xytext=(4.2, 36500),
                 fontsize=7.5, color=RED, va="center",
                 arrowprops=dict(arrowstyle="-", color=RED, lw=0.6))
    ax.annotate("11/13 4,996万株", xy=(23, 4996), xytext=(14.6, 5600),
                fontsize=7.5, color=NAVY, va="center",
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=0.6))
    ax2.annotate("11/20\n7,307円", xy=(24, 7307), xytext=(22.6, 15200),
                 fontsize=7.5, color=RED, ha="center", va="bottom",
                 arrowprops=dict(arrowstyle="-", color=RED, lw=0.6))

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(0.0, 1.17),
              ncol=2, frameon=False, handlelength=1.4, columnspacing=1.0)
    save(fig, "fig9_kioxia_margin.svg")


# ---------------------------------------------------------------- fig10
def fig10():
    import numpy as np

    t = np.linspace(0, 1, 400)
    peak, low = 0.36, 0.80

    # price: rise to peak, fall, bottom around `low`, then recover
    price = np.where(
        t <= peak,
        0.30 + 0.62 * (t / peak) ** 1.6,
        0.0,
    )
    fall = (t > peak) & (t <= low)
    u = (t[fall] - peak) / (low - peak)
    price[fall] = 0.92 - 0.66 * (1 - (1 - u) ** 1.5) + 0.035 * np.sin(u * 9) * (1 - u)
    rec = t > low
    v = (t[rec] - low) / (1 - low)
    price[rec] = price[fall][-1] + 0.22 * v ** 1.2

    # margin balance: rises, keeps rising after peak, unwinds in zone
    zone0, zone1 = 0.70, 0.86
    bars_t = np.linspace(0.02, 0.98, 33)
    bal = []
    for x in bars_t:
        if x <= peak:
            b = 0.22 + 0.30 * (x / peak)
        elif x <= zone0:
            b = 0.52 + 0.28 * (x - peak) / (zone0 - peak)
        elif x <= zone1:
            b = 0.80 - 0.42 * (x - zone0) / (zone1 - zone0)
        else:
            b = 0.38 - 0.04 * (x - zone1) / (1 - zone1)
        bal.append(b)

    fig, ax = plt.subplots(figsize=(7.1, 2.4))
    ax.axvspan(zone0, zone1, color=LIGHT, zorder=0)
    ax.bar(bars_t, bal, width=0.021, color=LNAVY, zorder=2,
           label="信用買い残（イメージ）")
    ax.plot(t, price, color=RED, lw=2.0, zorder=3, label="株価（イメージ）")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.42)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("時間 →")
    ax.set_ylabel("価格 ／ 信用買い残")

    pk_y = 0.92
    ax.annotate("2026/6 バイイング・クライマックス（高値）",
                xy=(peak, pk_y), xytext=(peak - 0.02, 1.08),
                ha="center", va="center", fontsize=8.5, color=RED,
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.8,
                                mutation_scale=7))
    ax.annotate("下げても買い増し・ナンピン\n（信用買い残は増え続ける）",
                xy=(0.60, 0.72), xytext=(0.53, 0.93),
                ha="center", va="center", fontsize=8.5, color=NAVY,
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=0.8,
                                mutation_scale=7))
    ax.text((zone0 + zone1) / 2, 1.19,
            "2026/12 6か月の返済期限\n投げ売り・追証 → 需給改善",
            ha="center", va="center", fontsize=8.5, color=TEXT,
            linespacing=1.25)
    ax.annotate("底入れ・反転", xy=(low + 0.005, price[fall][-1] - 0.01),
                xytext=(0.93, 0.12), ha="center", va="center",
                fontsize=8.5, color=RED,
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.8,
                                mutation_scale=7))
    ax.text(0.008, 1.33, "概念図", fontsize=8.5, color="#FFFFFF",
            ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc=GRAY, ec="none"))
    ax.legend(loc="center left", bbox_to_anchor=(0.088, 1.33 / 1.42),
              frameon=False, ncol=2, fontsize=8.5, handlelength=1.4,
              columnspacing=1.2, borderaxespad=0)
    save(fig, "fig10_margin_cycle.svg")


if __name__ == "__main__":
    fig9()
    fig10()
