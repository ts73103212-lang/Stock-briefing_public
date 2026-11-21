"""Charts for kabukura 2026-11-21 handout (A4 portrait PDF).

Usage: python3 make_charts.py   -> writes fig1..fig4 SVGs next to this script.
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


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), format="svg", bbox_inches="tight",
                pad_inches=0.04, metadata={"Date": None})
    plt.close(fig)


def comma(x, _pos=None):
    return f"{x:,.0f}"


# ---------------------------------------------------------------- fig1
def fig1():
    data = [("日経平均", -5.06, "-5.06%"), ("TOPIX", -3.88, "-3.88%"),
            ("NYダウ", -1.93, "-1.93%"), ("S&P500", -3.70, "-3.70%"),
            ("ナスダック総合", -5.28, "-5.28%"), ("SOX指数", -10.7, "-10.7%"),
            ("エヌビディア", -14.0, "-14.0%")]
    data.sort(key=lambda d: d[1], reverse=True)  # smallest drop first (top)
    fig, ax = plt.subplots(figsize=(3.35, 2.45))
    ys = range(len(data))
    ax.barh(ys, [d[1] for d in data], color=RED, height=0.62, zorder=2)
    for y, (_, v, s) in zip(ys, data):
        ax.text(v - 0.25, y, s, va="center", ha="right", fontsize=8.5, color=TEXT)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([d[0] for d in data])
    ax.invert_yaxis()
    ax.set_xlim(-17.5, 0)
    ax.set_xticks([-15, -10, -5, 0])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x:.0f}"))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(0, color="#666666", lw=0.7, zorder=3)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("騰落率（%）")
    fig.text(0.0, -0.10, "※日本株は11/20東京終値、米国株は11/20NY終値",
             fontsize=7.5, color="#555555", ha="left", va="top",
             transform=fig.transFigure)
    save(fig, "fig1_daily_drop.svg")


# ---------------------------------------------------------------- fig2
def spread_labels(values, min_gap):
    """Return label y-positions (same order as values) separated by min_gap."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos = [values[i] for i in order]
    for _ in range(200):
        moved = False
        for k in range(1, len(pos)):
            gap = pos[k] - pos[k - 1]
            if gap < min_gap:
                shift = (min_gap - gap) / 2
                pos[k - 1] -= shift
                pos[k] += shift
                moved = True
        if not moved:
            break
    out = [0.0] * len(values)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def ladder(ax, title, levels, current, ylim, min_gap):
    # levels: list of (value, label, kind) kind in {"high","above","current","support"}
    x0, x1, xl = 0.03, 0.30, 0.35
    supports = [v for v, _, k in levels if k == "support"]
    if supports:
        lo, hi = min(supports), max(supports)
        ax.axhspan(lo, hi, xmin=x0, xmax=x1, color=RED, alpha=0.10, lw=0, zorder=1)
        ax.text((x0 + x1) / 2, (lo + hi) / 2, "下値目途\nゾーン", ha="center",
                va="center", fontsize=8, color=RED, zorder=4, linespacing=1.15)
    vals = [v for v, _, _ in levels]
    ly = spread_labels(vals, min_gap)
    for (v, lab, kind), y in zip(levels, ly):
        if kind == "current":
            c, lw, ls, fw = NAVY, 2.4, "-", "bold"
        elif kind == "support":
            c, lw, ls, fw = RED, 1.3, "-", "normal"
        elif kind == "high":
            c, lw, ls, fw = GRAY, 1.1, (0, (4, 2)), "normal"
        else:
            c, lw, ls, fw = GRAY, 1.1, "-", "normal"
        ax.plot([x0, x1], [v, v], color=c, lw=lw, ls=ls, zorder=3,
                solid_capstyle="butt")
        if kind == "current":
            ax.plot([x1], [v], marker="o", ms=5, color=NAVY, zorder=5)
        ax.plot([x1 + 0.005, xl - 0.015], [v, y], color="#9AA3B2", lw=0.6, zorder=2)
        tc = NAVY if kind == "current" else (RED if kind == "support" else "#444444")
        ax.text(xl, y, f"{v:,}  {lab}", va="center", ha="left", fontsize=8,
                color=tc, fontweight=fw, zorder=4)
    ax.set_xlim(0, 1)
    ax.set_ylim(*ylim)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.yaxis.set_major_formatter(FuncFormatter(comma))
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=9.5, fontweight="bold", color=NAVY,
                 pad=4)


def fig2():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.1, 2.8))
    nk = [(72366, "最高値（6/25終値）", "high"),
          (57893, "高値−20%（弱気相場ライン）", "above"),
          (56745, "11/6安値", "above"),
          (56437, "11/20終値", "current"),
          (54275, "高値−25%", "support"),
          (50558, "年初来安値（3/31）", "support"),
          (50000, "心理的節目", "support")]
    ladder(a1, "日経平均（円）", nk, 56437, (47500, 74500), min_gap=1650)
    sp = [(7818, "最高値（10/6）", "high"),
          (7036, "高値−10%（調整入りライン）", "above"),
          (6910, "11/20終値", "current"),
          (6645, "高値−15%", "support"),
          (6254, "高値−20%（弱気相場ライン）", "support")]
    ladder(a2, "S&P500（ポイント）", sp, 6910, (6100, 7950), min_gap=115)
    fig.subplots_adjust(wspace=0.32)
    save(fig, "fig2_levels.svg")


# ---------------------------------------------------------------- fig3
def sim(returns, lev=-2.0):
    idx, etf = [100.0], [100.0]
    for r in returns:
        idx.append(idx[-1] * (1 + r))
        etf.append(etf[-1] * (1 + lev * r))
    return idx, etf


def fig3():
    down = [-0.02] * 10
    chop = [0.05 if i % 2 == 0 else -0.0476 for i in range(10)]
    panels = [("下落トレンド（指数が毎日−2%）", down),
              ("往復・ヨコヨコ（+5%と−4.76%を交互）", chop)]
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.3), sharey=False)
    for ax, (title, rets) in zip(axes, panels):
        idx, etf = sim(rets)
        xs = list(range(len(idx)))
        ax.plot([0, 10], [100, 100], color=GRAY, lw=0.8, ls=(0, (3, 2)), zorder=1)
        ax.plot(xs, idx, color=NAVY, lw=1.8, marker="o", ms=2.8, label="指数",
                zorder=3)
        ax.plot(xs, etf, color=RED, lw=1.8, marker="o", ms=2.8,
                label="ダブルインバース（−2倍）", zorder=3)
        ax.text(10.35, idx[-1], f"{idx[-1]:.1f}", color=NAVY, va="center",
                ha="left", fontsize=8.5, fontweight="bold")
        ax.text(10.35, etf[-1], f"{etf[-1]:.1f}", color=RED, va="center",
                ha="left", fontsize=8.5, fontweight="bold")
        ax.set_xlim(-0.3, 11.6)
        ax.set_xticks(range(0, 11, 2))
        ax.set_xlabel("営業日")
        ax.set_ylabel("基準=100")
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", fontsize=9, fontweight="bold",
                     color=NAVY, pad=4)
    axes[0].set_ylim(70, 160)
    axes[1].set_ylim(80, 115)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.07), fontsize=8.5)
    fig.subplots_adjust(wspace=0.28)
    save(fig, "fig3_inverse_decay.svg")


# ---------------------------------------------------------------- fig4
def fig4():
    cats = ["2008/11\nリーマン", "2020/3\nコロナ", "2024/8\n円キャリー",
            "2025/4\n関税\nショック", "2026/11/20\n今回"]
    vals = [80.86, 82.69, 65.73, 52.33, 35.89]
    labs = ["80.86", "82.69", "65.73\n(場中)", "52.33", "35.89"]
    cols = [GRAY, GRAY, GRAY, GRAY, NAVY]
    fig, ax = plt.subplots(figsize=(3.35, 2.6))
    xs = range(len(vals))
    ax.bar(xs, vals, color=cols, width=0.6, zorder=2)
    for x, v, s in zip(xs, vals, labs):
        if x == 4:
            ax.text(x, v - 1.5, s, ha="center", va="top", fontsize=8,
                    color="white", fontweight="bold", zorder=4)
        else:
            ax.text(x, v + 1.2, s, ha="center", va="bottom", fontsize=8,
                    color=TEXT, linespacing=1.05, zorder=4)
    # intraday high for current
    ax.plot([3.7, 4.3], [40, 40], color=NAVY, lw=1.2, ls=(0, (2, 1.5)), zorder=3)
    ax.text(4.3, 41.0, "場中一時40", ha="right", va="bottom", fontsize=7.5,
            color=NAVY, zorder=4)
    ax.axhline(50, color=RED, lw=1.1, ls=(0, (4, 2)), zorder=3)
    ax.axhline(20, color=GREEN, lw=1.0, ls=(0, (4, 2)), alpha=0.75, zorder=3)
    ax.annotate("VIX50＝セリングクライマックスの目安", xy=(4.5, 50.5),
                xytext=(4.62, 96), ha="right", va="center", fontsize=7.5,
                color=RED, arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.7,
                                           shrinkA=0, shrinkB=0,
                                           connectionstyle="angle,angleA=0,angleB=90,rad=0",
                                           mutation_scale=7))
    ax.text(-0.97, 21.0, "平常時\n〜20", ha="left", va="bottom", fontsize=7.5,
            color=GREEN, linespacing=1.05, zorder=4)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(cats, fontsize=7.2, linespacing=1.1)
    ax.set_xlim(-1.0, 4.65)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_ylabel("VIX（ピーク値）")
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0)
    save(fig, "fig4_vix_history.svg")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    print("done")
