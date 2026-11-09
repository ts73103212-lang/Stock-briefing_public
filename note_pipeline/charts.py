"""図の型 A〜F（設計書 §5.2）。各関数は spec dict を受け取り JPEG を書き出す。

共通キー: type, title, subtitle, source, web_search(任意)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from .style import PALETTE, SIZES, TONE, blank_axes, new_canvas, save_jpeg, style_axes


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fmt_num(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:,.1f}" if v != int(v) else f"{int(v):,}"


def _canvas(spec: dict, number: int):
    return new_canvas(spec.get("title", ""), spec.get("subtitle", ""), spec.get("source", ""),
                      number, web_search=bool(spec.get("web_search")))


def fmt_volume(v: float) -> str:
    if v >= 1e8:
        return f"{v / 1e8:.1f}億"
    if v >= 1e4:
        return f"{v / 1e4:,.0f}万"
    return f"{v:,.0f}"


_OFFSETS = {
    "above": (0, 40, "center", "bottom"), "below": (0, -40, "center", "top"),
    "left": (-24, 0, "right", "center"), "right": (24, 0, "left", "center"),
    "above-left": (-24, 36, "right", "bottom"), "above-right": (24, 36, "left", "bottom"),
    "below-left": (-24, -36, "right", "top"), "below-right": (24, -36, "left", "top"),
}


def annotation_offset(pos: str) -> tuple[int, int, str, str]:
    """注釈の吹き出し位置（点からのずらし量[pt]と文字揃え）。"""
    if pos not in _OFFSETS:
        raise ValueError(f"unknown annotation pos: {pos!r}（{', '.join(_OFFSETS)}）")
    return _OFFSETS[pos]


def _date_axis(dates: list[datetime]):
    """期間に応じて重複しない日付目盛りを返す（月が重複して並ぶのを防ぐ）。"""
    span = (max(dates) - min(dates)).days
    if span > 60:
        return mdates.MonthLocator(interval=1 if span <= 240 else 2), mdates.DateFormatter("%y/%m")
    return mdates.DayLocator(interval=max(1, span // 6)), mdates.DateFormatter("%m/%d")


def date_tick_labels(dates: list[datetime]) -> list[str]:
    loc, fmt = _date_axis(dates)
    return [fmt(t) for t in loc.tick_values(min(dates), max(dates))]


def chart_a(spec: dict, out: Path, number: int) -> Path:
    """株価（終値線）＋出来高、重要日に注釈。"""
    fig, ax = _canvas(spec, number)
    x0, y0, w, h = ax.get_position().bounds
    ax.remove()
    price = fig.add_axes((x0, y0 + h * 0.3, w, h * 0.7))
    vol = fig.add_axes((x0, y0, w, h * 0.25), sharex=price)
    for a in (price, vol):
        style_axes(a)
    dates = [datetime.fromisoformat(d) for d in spec["dates"]]
    close, volume = spec["close"], spec["volume"]
    price.plot(dates, close, color=PALETTE["navy"], linewidth=3.2, zorder=3)
    lo = min(close)
    pad = (max(close) - lo) * 0.08 or 1
    price.fill_between(dates, close, lo - pad, color=PALETTE["navy2"], alpha=0.18, zorder=2)
    n_ann = len(spec.get("annotations", []))
    price.set_ylim(lo - pad, max(close) + pad * (3 if n_ann <= 1 else 6))
    price.yaxis.set_major_locator(MaxNLocator(nbins=4))
    price.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    price.tick_params(labelbottom=False)
    # 出来高は前日比で色分け（上昇=緑、下落=赤）
    colors = [PALETTE["up"] if i == 0 or close[i] >= close[i - 1] else PALETTE["down"] for i in range(len(close))]
    width = (max(dates) - min(dates)).days / max(len(dates), 1) * 0.7 or 0.7
    for line in spec.get("hlines", []):
        color = TONE.get(line.get("color", "gold"), PALETTE["gold"])
        ls = {"dashed": "--", "dotted": ":", "solid": "-"}.get(line.get("style", "dashed"), "--")
        price.axhline(line["y"], color=color, linestyle=ls, linewidth=2.2, zorder=3.5)
        if line.get("label"):
            price.annotate(line["label"], (0.005, line["y"]), xycoords=("axes fraction", "data"),
                           xytext=(4, 6), textcoords="offset points", ha="left", va="bottom",
                           fontsize=SIZES["tick"], fontweight="bold", color=color, zorder=6,
                           bbox={"boxstyle": "round,pad=0.15", "fc": PALETTE["bg"], "ec": "none", "alpha": 0.85})
    anns = spec.get("annotations", [])
    for ann in anns:
        d = datetime.fromisoformat(ann["date"])
        if d not in dates:
            continue
        i = dates.index(d)
        y = ann.get("y", close[i])
        note = ann.get("style") == "note"
        if ann.get("highlight", not note):
            colors[i] = PALETTE["gold"]
            price.plot([d], [y], "o", color=PALETTE["gold"], markersize=13, zorder=4,
                       markeredgecolor="white", markeredgewidth=2)
        if ann.get("pos"):
            dx, dy, ha, va = annotation_offset(ann["pos"])
        else:  # 自動配置（従来どおり）: 端では内側に寄せ、近い注釈は段違いにする
            frac = i / max(len(dates) - 1, 1)
            ha, dx = ("right", 10) if frac > 0.8 else (("left", -10) if frac < 0.2 else ("center", 0))
            k = sum(1 for a2 in anns if a2 is not ann and a2["date"] > ann["date"] and not a2.get("pos"))
            dy, va = 34 + 44 * (k % 2), "bottom"
        style = {} if note else {"bbox": {"boxstyle": "round,pad=0.3", "fc": "#FFFFFF", "ec": PALETTE["gold"], "lw": 2}}
        price.annotate(ann["text"], (d, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                       fontsize=SIZES["tick"] if note else SIZES["annot"], fontweight="bold",
                       color=PALETTE["muted"] if note else PALETTE["gold_text"],
                       arrowprops=None if note else {"arrowstyle": "-", "color": PALETTE["gold"], "lw": 2},
                       zorder=5, **style)
    if spec.get("ylim"):
        price.set_ylim(*spec["ylim"])
    # 下向きの吹き出しが出来高の領域に隠れないよう、株価の領域を前面に出す
    price.set_zorder(vol.get_zorder() + 1)
    price.patch.set_visible(False)
    vd = [(d, v, c) for d, v, c in zip(dates, volume, colors) if v is not None]
    if vd:
        vol.bar([d for d, _, _ in vd], [v for _, v, _ in vd], color=[c for _, _, c in vd], width=width)
    vol.yaxis.set_major_locator(MaxNLocator(nbins=2, min_n_ticks=2))
    vol.yaxis.set_major_formatter(lambda v, _: fmt_volume(v))
    vol.tick_params(axis="y", labelsize=SIZES["tick"] - 4)
    vol.text(0.0, 1.04, "出来高（株）", transform=vol.transAxes, fontsize=SIZES["tick"] - 3, color=PALETTE["muted"])
    loc, fmt = _date_axis(dates)
    vol.xaxis.set_major_locator(loc)
    vol.xaxis.set_major_formatter(fmt)
    price.margins(x=0.04)
    return save_jpeg(fig, out)


def chart_b(spec: dict, out: Path, number: int) -> Path:
    """売上・営業利益の棒グラフ（予想は点線）。"""
    fig, ax = _canvas(spec, number)
    x0, y0, w, h = ax.get_position().bounds
    ax.remove()
    periods = spec["periods"]
    fc = spec.get("forecast_from", len(periods))
    unit = spec.get("unit", "億円")
    names = spec.get("series_labels") or ["売上高", "営業利益"]
    series = (("sales", names[0], PALETTE["navy"]), ("op_income", names[1], "#E07B00"))
    for k, (key, label, color) in enumerate(series):
        a = fig.add_axes((x0 + k * w * 0.53, y0, w * 0.47, h * 0.9))
        style_axes(a)
        a.yaxis.set_major_locator(MaxNLocator(nbins=4))
        vals = spec[key]
        for i, v in enumerate(vals):
            fore = i >= fc
            a.bar(i, v, width=0.66, color=color, alpha=0.35 if fore else 1.0, hatch="//" if fore else None,
                  edgecolor=color, linewidth=2.5, linestyle="--" if fore else "-")
            a.annotate(_fmt_num(v), (i, v), xytext=(0, 6), textcoords="offset points",
                       ha="center", va="bottom", fontsize=SIZES["value"], fontweight="bold", color=PALETTE["fg"])
        a.set_xticks(range(len(periods)), periods)
        a.set_title(f"{label}（{unit}）", loc="left", fontsize=SIZES["label"], fontweight="bold", color=color, pad=14)
        a.margins(y=0.2)
    if fc < len(periods):
        fig.text(0.96, 0.858, "斜線は会社予想", fontsize=SIZES["subtitle"] - 2, color=PALETTE["muted"], ha="right",
                 va="center")
    return save_jpeg(fig, out)


def fit_fontsize(text: str, col_w: float, base: float) -> float:
    """表のセル幅（axes 座標の割合）に収まるフォントサイズ（pt）。全角=1、半角=0.6 文字で概算。"""
    units = sum(1.0 if ord(ch) > 0x2E7F else 0.6 for ch in str(text)) or 1
    avail_px = col_w * 1920 * 0.885 * 0.9 - 0.02 * 1920
    fit = avail_px / units * 72 / 150
    return round(min(base, max(11, fit)), 1)


def _table(ax, header: list[str], rows: list[list[str]], col_w: list[float],
           cell_color=None, text_color=None, bold_col: int | None = None) -> None:
    blank_axes(ax)
    n = len(rows) + 1
    rh = 1 / n
    gap = 0.006
    xs = [sum(col_w[:j]) for j in range(len(col_w))]
    for j, label in enumerate(header):
        ax.add_patch(Rectangle((xs[j] + gap, 1 - rh + gap), col_w[j] - 2 * gap, rh - 2 * gap,
                               color=PALETTE["navy"]))
        ax.text(xs[j] + 0.02, 1 - rh / 2, label, color="white", fontsize=fit_fontsize(label, col_w[j], SIZES["table_head"]),
                fontweight="bold", va="center")
    for i, row in enumerate(rows):
        y = 1 - rh * (i + 2)
        for j, cell in enumerate(row):
            fc = cell_color(i, j) if cell_color else PALETTE["paper"]
            ax.add_patch(Rectangle((xs[j] + gap, y + gap), col_w[j] - 2 * gap, rh - 2 * gap, color=fc))
            tc = text_color(i, j) if text_color else PALETTE["fg"]
            longest = max(str(cell).split("\n"), key=len)
            ax.text(xs[j] + 0.02, y + rh / 2, str(cell), fontsize=fit_fontsize(longest, col_w[j], SIZES["table"]),
                    va="center", color=tc,
                    fontweight="bold" if (j == 0 or j == bold_col) else "normal", linespacing=1.5)


def chart_c(spec: dict, out: Path, number: int) -> Path:
    """同業比較表（数値の大小を色の濃さで）。"""
    fig, ax = _canvas(spec, number)
    cols, rows = spec["columns"], spec["rows"]
    shade = set(spec.get("shade_cols", range(len(cols))))
    ranges = {}
    for j in shade:
        vals = [r["values"][j] for r in rows if _is_num(r["values"][j])]
        ranges[j] = (min(vals), max(vals)) if vals else (0, 1)

    def alpha(i, j):
        lo, hi = ranges[j]
        v = rows[i]["values"][j]
        if not _is_num(v):
            return 0.0
        return 0.08 + 0.5 * ((v - lo) / (hi - lo) if hi > lo else 0.5)

    def cell_color(i, j):
        if j == 0 or (j - 1) not in shade or not _is_num(rows[i]["values"][j - 1]):
            return PALETTE["paper"]
        a = alpha(i, j - 1)
        r, g, b = (int(PALETTE["navy"][k:k + 2], 16) for k in (1, 3, 5))
        mix = lambda c: int(255 - (255 - c) * a)  # noqa: E731
        return f"#{mix(r):02X}{mix(g):02X}{mix(b):02X}"

    def text_color(i, j):
        return "white" if j > 0 and (j - 1) in shade and alpha(i, j - 1) > 0.45 else PALETTE["fg"]

    body = [[r["name"]] + [_fmt_num(v) for v in r["values"]] for r in rows]
    first = 0.28
    rest = (1 - first) / len(cols)
    _table(ax, ["銘柄"] + cols, body, [first] + [rest] * len(cols), cell_color, text_color)
    return save_jpeg(fig, out)


def chart_d(spec: dict, out: Path, number: int) -> Path:
    """指標カード（大きな数字のタイル）。最大6枚。"""
    fig, ax = _canvas(spec, number)
    blank_axes(ax)
    cards = spec["cards"][:6]
    ncol = 2 if len(cards) in (2, 4) else min(3, len(cards))
    nrow = -(-len(cards) // ncol)
    cw, chh, gx, gy = (1 - 0.05 * (ncol - 1)) / ncol, (1 - 0.08 * (nrow - 1)) / nrow, 0.05, 0.08
    big = SIZES["card_value"] if ncol <= 2 else SIZES["card_value"] - 10
    for k, c in enumerate(cards):
        col, row = k % ncol, k // ncol
        x, y = col * (cw + gx), 1 - (row + 1) * chh - row * gy
        tone = TONE.get(c.get("tone", "navy"), PALETTE["navy"])
        ax.add_patch(FancyBboxPatch((x, y), cw, chh, boxstyle="round,pad=0,rounding_size=0.02",
                                    fc=PALETTE["paper"], ec=PALETTE["grid"], lw=1.5))
        ax.add_patch(Rectangle((x, y), 0.016, chh, color=tone))
        ax.text(x + 0.04, y + chh * 0.8, c["label"], fontsize=SIZES["card_label"], color=PALETTE["muted"], va="center")
        ax.text(x + 0.04, y + chh * 0.48, c["value"], fontsize=big, fontweight="bold", color=PALETTE["fg"],
                va="center")
        if c.get("sub"):
            sub_color = PALETTE["fg"] if c.get("tone", "navy") == "navy" else tone
            ax.text(x + 0.04, y + chh * 0.16, c["sub"], fontsize=SIZES["card_sub"], color=sub_color, va="center",
                    fontweight="bold")
    return save_jpeg(fig, out)


def chart_e(spec: dict, out: Path, number: int) -> Path:
    """横棒の順位グラフ（騰落率）。highlight の1本だけゴールド。"""
    fig, ax = _canvas(spec, number)
    x0, y0, w, h = ax.get_position().bounds
    ax.set_position((x0 + 0.11, y0, w - 0.11, h))  # 業種名などの長いラベル用に左を空ける
    pairs = sorted(zip(spec["labels"], spec["values"]), key=lambda p: p[1])
    labels, values = [p[0] for p in pairs], [p[1] for p in pairs]
    hl = spec.get("highlight")
    colors = [PALETTE["gold"] if lab == hl else (PALETTE["up"] if v >= 0 else PALETTE["down"])
              for lab, v in zip(labels, values)]
    ax.barh(range(len(values)), values, color=colors, height=0.62)
    ax.set_yticks(range(len(labels)), labels, fontsize=SIZES["label"] if len(labels) <= 10 else SIZES["tick"] - 3,
                  color=PALETTE["fg"])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=PALETTE["grid"])
    ax.axvline(0, color="#8A8578", lw=1)
    unit = spec.get("unit", "%")
    span = (max(values) - min(values)) or 1
    for i, v in enumerate(values):
        ax.text(v + (0.01 * span if v >= 0 else -0.01 * span), i, f"{v:+.1f}{unit}",
                va="center", ha="left" if v >= 0 else "right", fontsize=SIZES["value"] if len(values) <= 10 else SIZES["tick"] - 3,
                fontweight="bold", color=PALETTE["fg"])
    ax.margins(x=0.12)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6, steps=[1, 2, 2.5, 5, 10]))
    dec = 0 if span >= 8 else 1
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.{dec}f}{unit}" if abs(v) > 1e-9 else f"0{unit}")
    return save_jpeg(fig, out)


def chart_f(spec: dict, out: Path, number: int) -> Path:
    """仕組み・たとえ話の図解。boxes+arrows のフロー図、または table（試作の図⑦型）。"""
    fig, ax = _canvas(spec, number)
    if "table" in spec:
        t = spec["table"]
        emph = t.get("emphasis_col")
        ncol = len(t["header"])
        widths = [0.17] + [(0.83) / (ncol - 1)] * (ncol - 1) if ncol > 1 else [1.0]
        _table(ax, t["header"], t["rows"], widths,
               cell_color=lambda i, j: PALETTE["soft"] if j == emph else PALETTE["paper"],
               text_color=lambda i, j: PALETTE["gold_text"] if j == emph else PALETTE["fg"], bold_col=emph)
        return save_jpeg(fig, out)
    blank_axes(ax)
    boxes = spec["boxes"]
    n = len(boxes)
    bw, gap = (1 - 0.08 * (n - 1)) / n, 0.08
    centers = []
    for i, b in enumerate(boxes):
        x = i * (bw + gap)
        emph = b.get("emphasis")
        ax.add_patch(FancyBboxPatch((x, 0.3), bw, 0.4, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc=PALETTE["soft"] if emph else PALETTE["paper"],
                                    ec=PALETTE["gold"] if emph else PALETTE["navy"], lw=2))
        ax.text(x + bw / 2, 0.5, b["text"], ha="center", va="center", fontsize=SIZES["box"], fontweight="bold",
                color=PALETTE["navy"], linespacing=1.6, wrap=True)
        if b.get("note"):
            ax.text(x + bw / 2, 0.2, b["note"], ha="center", va="top", fontsize=SIZES["tick"], color=PALETTE["muted"],
                    linespacing=1.5)
        centers.append((x, x + bw))
    for i, j in spec.get("arrows", []):
        (a0, a1), (b0, b1) = centers[i], centers[j]
        start, end = ((a1, 0.5), (b0, 0.5)) if b0 > a1 else ((a0, 0.5), (b1, 0.5))
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=22,
                                     color=PALETTE["navy"], lw=2, shrinkA=6, shrinkB=6))
    return save_jpeg(fig, out)


def render(spec: dict, out_path: Path, number: int) -> Path:
    kind = spec.get("type")
    out_path = Path(out_path)
    if kind == "A":
        return chart_a(spec, out_path, number)
    if kind == "B":
        return chart_b(spec, out_path, number)
    if kind == "C":
        return chart_c(spec, out_path, number)
    if kind == "D":
        return chart_d(spec, out_path, number)
    if kind == "E":
        return chart_e(spec, out_path, number)
    if kind == "F":
        return chart_f(spec, out_path, number)
    raise ValueError(f"unknown chart type: {kind!r}（A〜F のいずれか）")
