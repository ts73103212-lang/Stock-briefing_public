"""図の型 A〜I（設計書 §5.2）。各関数は spec dict を受け取り JPEG を書き出す。

共通キー: type, title, subtitle, source, web_search(任意)
グラフ＝A・B・E・G・H・I、文字中心の図＝C・D・F（記事に入れる比率は editorial-rules.md の 8）
"""
from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from .style import PALETTE, SERIES, SIZES, TONE, blank_axes, new_canvas, save_jpeg, style_axes

GRAPH_TYPES = {"A", "B", "E", "G", "H", "I"}
TEXT_TYPES = {"C", "D", "F"}


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


def tick_decimals(span: float) -> int:
    """縦軸の目盛りの小数桁（株価・指数は整数、狭い値幅だけ小数1〜2桁）。"""
    if span >= 5:
        return 0
    return 1 if span >= 0.5 else 2


def has_volume(spec: dict) -> bool:
    """型Aで出来高の段を描くか（指数・為替など、出来高がすべて null か無いときは描かない）。"""
    return any(v is not None for v in (spec.get("volume") or []))


def _draw_hlines(ax, lines: list[dict]) -> None:
    """基準線（自社株買い価格・前回高値・平均など）。型A・G・I 共通。"""
    for line in lines:
        color = TONE.get(line.get("color", "gold"), PALETTE["gold"])
        ls = {"dashed": "--", "dotted": ":", "solid": "-"}.get(line.get("style", "dashed"), "--")
        ax.axhline(line["y"], color=color, linestyle=ls, linewidth=2.2, zorder=3.5)
        if line.get("label"):
            ax.annotate(line["label"], (0.005, line["y"]), xycoords=("axes fraction", "data"),
                        xytext=(4, 6), textcoords="offset points", ha="left", va="bottom",
                        fontsize=SIZES["tick"], fontweight="bold", color=color, zorder=6,
                        bbox={"boxstyle": "round,pad=0.15", "fc": PALETTE["bg"], "ec": "none", "alpha": 0.85})


def chart_a(spec: dict, out: Path, number: int) -> Path:
    """株価（終値線）＋出来高、重要日に注釈。指数・為替は出来高を null にすると上の段だけになる。"""
    fig, ax = _canvas(spec, number)
    x0, y0, w, h = ax.get_position().bounds
    ax.remove()
    with_vol = has_volume(spec)
    if with_vol:
        price = fig.add_axes((x0, y0 + h * 0.3, w, h * 0.7))
        vol = fig.add_axes((x0, y0, w, h * 0.25), sharex=price)
        style_axes(vol)
    else:
        price, vol = fig.add_axes((x0, y0, w, h)), None
    style_axes(price)
    dates = [datetime.fromisoformat(d) for d in spec["dates"]]
    close = spec["close"]
    volume = spec.get("volume") or [None] * len(close)
    price.plot(dates, close, color=PALETTE["navy"], linewidth=3.2, zorder=3)
    lo = min(close)
    pad = (max(close) - lo) * 0.08 or 1
    price.fill_between(dates, close, lo - pad, color=PALETTE["navy2"], alpha=0.18, zorder=2)
    n_ann = len(spec.get("annotations", []))
    price.set_ylim(lo - pad, max(close) + pad * (3 if n_ann <= 1 else 6))
    price.yaxis.set_major_locator(MaxNLocator(nbins=4))
    dec = tick_decimals(max(close) - lo)
    price.yaxis.set_major_formatter(lambda v, _: f"{v:,.{dec}f}")
    if with_vol:
        price.tick_params(labelbottom=False)
    # 出来高は前日比で色分け（上昇=緑、下落=赤）
    colors = [PALETTE["up"] if i == 0 or close[i] >= close[i - 1] else PALETTE["down"] for i in range(len(close))]
    width = (max(dates) - min(dates)).days / max(len(dates), 1) * 0.7 or 0.7
    _draw_hlines(price, spec.get("hlines", []))
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
    loc, fmt = _date_axis(dates)
    if with_vol:
        # 下向きの吹き出しが出来高の領域に隠れないよう、株価の領域を前面に出す
        price.set_zorder(vol.get_zorder() + 1)
        price.patch.set_visible(False)
        vd = [(d, v, c) for d, v, c in zip(dates, volume, colors) if v is not None]
        vol.bar([d for d, _, _ in vd], [v for _, v, _ in vd], color=[c for _, _, c in vd], width=width)
        vol.yaxis.set_major_locator(MaxNLocator(nbins=2, min_n_ticks=2))
        vol.yaxis.set_major_formatter(lambda v, _: fmt_volume(v))
        vol.tick_params(axis="y", labelsize=SIZES["tick"] - 4)
        vol.text(0.0, 1.04, "出来高（株）", transform=vol.transAxes, fontsize=SIZES["tick"] - 3,
                 color=PALETTE["muted"])
    (vol or price).xaxis.set_major_locator(loc)
    (vol or price).xaxis.set_major_formatter(fmt)
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


# ---- 型G: 折れ線の比較 ----

def rebase_100(values: list) -> list:
    """最初の有効値を100にそろえる（指数化）。null はそのまま。"""
    base = next((v for v in values if v is not None), None)
    if not base:
        raise ValueError("指数化できない系列（有効な値がないか、起点が0）")
    return [None if v is None else v / base * 100 for v in values]


def spread_positions(ys: list[float], gap: float, lo: float = 0.0, hi: float = 1.0) -> list[float]:
    """ラベルの縦位置（0〜1）を、順番を保ったまま gap 以上離す（端からはみ出さない）。"""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in order]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    if pos and pos[-1] > hi:
        pos[-1] = hi
        for k in range(len(pos) - 2, -1, -1):
            pos[k] = min(pos[k], pos[k + 1] - gap)
    if pos and pos[0] < lo:
        shift = lo - pos[0]
        pos = [p + shift for p in pos]
    out = [0.0] * len(ys)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def _fit_size(text: str, avail_px: float, base: float, floor: float = 12) -> float:
    units = sum(1.0 if ord(ch) > 0x2E7F else 0.6 for ch in str(text)) or 1
    return round(min(base, max(floor, avail_px / units * 72 / 150)), 1)


def _fmt_level(v: float, unit: str, dec: int) -> str:
    return f"{v:,.{dec}f}{unit}"


def chart_g(spec: dict, out: Path, number: int) -> Path:
    """折れ線の比較（2〜4本）。normalize で起点=100、イベントの縦線、右端に最後の値のラベル。"""
    series = spec["series"]
    if not 2 <= len(series) <= 4:
        raise ValueError(f"型G の系列は2〜4本（今は{len(series)}本）")
    dates = [datetime.fromisoformat(d) for d in spec["dates"]]
    normalize = bool(spec.get("normalize"))
    unit = spec.get("unit", "")
    lines = []
    for s in series:
        vals = s["values"]
        if len(vals) != len(dates):
            raise ValueError(f"系列「{s['label']}」の値の数が dates と合わない")
        lines.append(rebase_100(vals) if normalize else list(vals))
    fig, ax = _canvas(spec, number)
    x0, y0, w, h = ax.get_position().bounds
    ax.set_position((x0, y0, w * 0.80, h))  # 右端のラベル用に空ける
    every = [v for vals in lines for v in vals if v is not None] + [hl["y"] for hl in spec.get("hlines", [])]
    if normalize:
        every.append(100)
    lo, hi = min(every), max(every)
    pad = (hi - lo) * 0.08 or 1
    n_ann = len(spec.get("annotations", []))
    ylo, yhi = lo - pad, hi + pad * (1 if n_ann == 0 else 3.5)
    ax.set_ylim(ylo, yhi)
    if normalize:
        ax.axhline(100, color="#8A8578", lw=1.5, zorder=1)
        ax.text(0.0, 1.03, f"起点（{dates[0]:%Y/%m/%d}）＝100", transform=ax.transAxes,
                fontsize=SIZES["tick"] - 3, color=PALETTE["muted"])
    elif unit:
        ax.text(0.0, 1.03, f"単位：{unit}", transform=ax.transAxes, fontsize=SIZES["tick"] - 3, color=PALETTE["muted"])
    _draw_hlines(ax, spec.get("hlines", []))
    ends = []
    for k, (s, vals) in enumerate(zip(series, lines)):
        pts = [(d, v) for d, v in zip(dates, vals) if v is not None]
        color = SERIES[k]
        ax.plot([d for d, _ in pts], [v for _, v in pts], color=color, linewidth=3.8 if k == 0 else 2.6,
                zorder=4 if k == 0 else 3, solid_capstyle="round")
        ax.plot([pts[-1][0]], [pts[-1][1]], "o", color=color, markersize=10, zorder=5,
                markeredgecolor="white", markeredgewidth=2)
        ends.append((s["label"], pts[-1][1], color))
    dec = tick_decimals(hi - lo)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.{dec}f}")
    # 右端のラベル（名前＋最後の値）。2行ぶんの間隔を空けて重ならないようにする
    axes_px = h * 1080
    fracs = [(v - ylo) / (yhi - ylo) for _, v, _ in ends]
    gap = 92 / axes_px
    ys = spread_positions(fracs, gap=gap, lo=gap / 2, hi=1 - gap / 2)
    avail = (1 - (x0 + w * 0.80) - 0.03) * 1920
    for (label, v, color), y in zip(ends, ys):
        value = f"{v - 100:+.1f}%" if normalize else _fmt_level(v, unit, dec)
        value = value.replace("-", "−")
        ax.text(1.02, y, label, transform=ax.transAxes, ha="left", va="bottom", color=color,
                fontsize=_fit_size(label, avail * 0.92, SIZES["tick"], floor=0), fontweight="bold")
        ax.text(1.02, y, value, transform=ax.transAxes, ha="left", va="top", color=color,
                fontsize=_fit_size(value, avail, SIZES["value"] + 2), fontweight="bold")
    # イベントの縦線（近いものは段違い）
    anns = sorted(spec.get("annotations", []), key=lambda a: a["date"])
    span = (max(dates) - min(dates)).total_seconds() or 1
    prev_x = None
    level = 0
    for ann in anns:
        d = datetime.fromisoformat(ann["date"])
        fx = (d - min(dates)).total_seconds() / span
        level = (level + 1) % 2 if prev_x is not None and fx - prev_x < 0.25 else 0
        prev_x = fx
        ax.axvline(d, color=PALETTE["muted"], linestyle=":", linewidth=2, zorder=2)
        ha, dx = ("right", -6) if fx > 0.7 else ("left", 6)
        ax.annotate(ann["text"], (d, 1.0), xycoords=("data", "axes fraction"), xytext=(dx, -8 - 40 * level),
                    textcoords="offset points", ha=ha, va="top", fontsize=SIZES["tick"], fontweight="bold",
                    color=PALETTE["fg"], zorder=6,
                    bbox={"boxstyle": "round,pad=0.25", "fc": PALETTE["bg"], "ec": PALETTE["grid"], "lw": 1.5})
    loc, fmt = _date_axis(dates)
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(fmt)
    ax.margins(x=0.02)
    return save_jpeg(fig, out)


# ---- 型H: レーダーチャート ----

def radar_scores(raw: dict[str, list[float]], higher_is_better: list[bool]) -> dict[str, list[int]]:
    """比べる会社群の中での順位を0〜100点にする（最良=100、最下位=0、同点は同じ点）。

    raw は {会社名: [項目ごとの実際の値]}。PER・PBR のように低いほど良い項目は higher_is_better を False に。
    """
    names = list(raw)
    n = len(names)
    if n < 2:
        raise ValueError("点数化には2社以上が必要")
    out = {name: [] for name in names}
    for j, up in enumerate(higher_is_better):
        col = [raw[name][j] for name in names]
        for name, v in zip(names, col):
            better = sum(1 for o in col if (o < v if up else o > v))
            ties = sum(1 for o in col if o == v) - 1
            out[name].append(round(100 * (better + 0.5 * ties) / (n - 1)))
    return out


def chart_h(spec: dict, out: Path, number: int) -> Path:
    """レーダーチャート（2〜3銘柄 × 5〜6項目、0〜100点）。項目名の下に実際の値（raw）を添える。"""
    items, series = spec["axes"], spec["series"]
    if not 5 <= len(items) <= 6:
        raise ValueError(f"型H の項目は5〜6個（今は{len(items)}個）")
    if not 2 <= len(series) <= 3:
        raise ValueError(f"型H の銘柄は2〜3つ（今は{len(series)}つ）")
    for s in series:
        if len(s["scores"]) != len(items):
            raise ValueError(f"「{s['label']}」の点数の数が項目数と合わない")
        if any(not _is_num(v) or not 0 <= v <= 100 for v in s["scores"]):
            raise ValueError(f"「{s['label']}」の点数は0〜100の数で")
    fig, ax = _canvas(spec, number)
    x0, y0, w, h = ax.get_position().bounds
    ax.remove()
    # 正方形の極座標を左寄りに置き、右に凡例
    ph = h * 0.74
    pw = ph * 1080 / 1920
    cx, cy = 0.37, y0 + h * 0.47
    pax = fig.add_axes((cx - pw / 2, cy - ph / 2, pw, ph), projection="polar")
    pax.set_facecolor(PALETTE["bg"])
    pax.set_theta_offset(math.pi / 2)
    pax.set_theta_direction(-1)
    n = len(items)
    angles = [2 * math.pi * k / n for k in range(n)]
    pax.set_ylim(0, 100)
    pax.set_xticks(angles, [""] * n)
    pax.set_yticks([20, 40, 60, 80, 100], ["", "", "", "", ""])
    pax.grid(color=PALETTE["grid"], linewidth=1.4)
    pax.spines["polar"].set_color("#C9C3B6")
    pax.spines["polar"].set_linewidth(1.5)
    for k, s in enumerate(series):
        vals = list(s["scores"]) + [s["scores"][0]]
        ang = angles + [angles[0]]
        color = SERIES[k]
        pax.fill(ang, vals, color=color, alpha=0.20 if k == 0 else 0.12, zorder=2 + k)
        pax.plot(ang, vals, color=color, linewidth=3.6 if k == 0 else 2.8, zorder=3 + k)
        pax.plot(angles, s["scores"], "o", color=color, markersize=9, zorder=4 + k,
                 markeredgecolor="white", markeredgewidth=1.5)
    for a, item in zip(angles, items):
        sx, sy = math.sin(a), math.cos(a)
        ha = "center" if abs(sx) < 0.2 else ("left" if sx > 0 else "right")
        raw = item.get("raw")
        if sy > 0.2:      # 上側: 下から raw → 項目名
            offs = ((0, 30), (0, 4)) if raw else ((0, 4), None)
            va = "bottom"
        elif sy < -0.2:   # 下側: 上から項目名 → raw
            offs = ((0, -4), (0, -36))
            va = "top"
        else:             # 横: 項目名を上、raw を下
            offs = ((8 if sx > 0 else -8, 2), (8 if sx > 0 else -8, -2))
            va = None
        pax.annotate(item["label"], (a, 104), xytext=offs[0], textcoords="offset points", ha=ha,
                     va=va or "bottom", fontsize=SIZES["label"], fontweight="bold", color=PALETTE["fg"],
                     annotation_clip=False)
        if raw:
            pax.annotate(raw, (a, 104), xytext=offs[1], textcoords="offset points", ha=ha, va=va or "top",
                         fontsize=SIZES["tick"] - 2, color=PALETTE["muted"], annotation_clip=False)
    # 凡例（右側）: 銘柄名と平均点
    lx, top = 0.66, y0 + h * 0.82
    step = min(0.17, h * 0.85 / len(series))
    for k, s in enumerate(series):
        y = top - k * step
        fig.add_artist(Rectangle((lx, y - 0.012), 0.022, 0.04, transform=fig.transFigure, color=SERIES[k]))
        fig.text(lx + 0.035, y + 0.008, s["label"], fontsize=_fit_size(s["label"], (0.96 - lx - 0.035) * 1920,
                                                                     SIZES["label"] + 4),
                 fontweight="bold", color=SERIES[k], va="center")
        avg = sum(s["scores"]) / len(s["scores"])
        fig.text(lx + 0.035, y - 0.045, f"平均 {avg:.0f}点", fontsize=SIZES["tick"], color=PALETTE["muted"],
                 va="center")
    if spec.get("note"):
        fig.text(lx, y0 + 0.01, spec["note"], fontsize=SIZES["tick"] - 4, color=PALETTE["muted"], va="bottom",
                 linespacing=1.5)
    return save_jpeg(fig, out)


# ---- 型I: 縦棒 ----

def bar_value_label(v: float, unit: str, signed: bool, decimals: int) -> str:
    text = f"{v:+,.{decimals}f}" if signed else f"{v:,.{decimals}f}"
    return text.replace("-", "−") + unit


def chart_i(spec: dict, out: Path, number: int) -> Path:
    """縦棒（時系列・カテゴリ）。正負で緑・赤、highlight の1本だけゴールド、値ラベル付き。"""
    labels, values = spec["labels"], spec["values"]
    if len(labels) != len(values):
        raise ValueError("型I の labels と values の数が合わない")
    unit = spec.get("unit", "%")
    # 「%」以外の単位（億円など）は軸の上に1回だけ書き、目盛り・値ラベルは数字だけにする（左のはみ出し防止）
    tick_unit = unit if unit == "%" else ""
    nums = [v for v in values if v is not None]
    signed = spec.get("signed", any(v < 0 for v in nums) or unit == "%")
    dec = spec.get("decimals", 1 if unit == "%" else (0 if max(abs(v) for v in nums) >= 100 else 1))
    by_sign = spec.get("color_by_sign", True)
    hl = spec.get("highlight")
    fig, ax = _canvas(spec, number)
    n = len(values)
    colors = [PALETTE["gold"] if lab == hl else
              ((PALETTE["up"] if v >= 0 else PALETTE["down"]) if by_sign else PALETTE["navy"])
              for lab, v in zip(labels, [v if v is not None else 0 for v in values])]
    xs = list(range(n))
    ax.bar([x for x, v in zip(xs, values) if v is not None], nums,
           color=[c for c, v in zip(colors, values) if v is not None], width=0.62, zorder=3)
    lo, hi = min(nums + [0]), max(nums + [0])
    span = (hi - lo) or 1
    ax.set_ylim(lo - (span * 0.16 if lo < 0 else 0), hi + span * 0.16)
    ax.axhline(0, color="#8A8578", lw=1.5, zorder=4)
    if not tick_unit:
        ax.text(0.0, 1.03, f"単位：{unit}", transform=ax.transAxes, fontsize=SIZES["tick"] - 3, color=PALETTE["muted"])
    vsize = SIZES["value"] if n <= 8 else (SIZES["tick"] - 2 if n <= 12 else SIZES["tick"] - 5)
    slot_px = ax.get_position().width * 1920 / max(n, 1) * 0.94  # 棒1本ぶんの幅に収める
    for x, v, lab in zip(xs, values, labels):
        if v is None:
            ax.text(x, 0, "—", ha="center", va="bottom", fontsize=vsize, color=PALETTE["muted"])
            continue
        text = bar_value_label(v, tick_unit, signed, dec)
        ax.annotate(text, (x, v), xytext=(0, 6 if v >= 0 else -6),
                    textcoords="offset points", ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=_fit_size(text, slot_px, vsize), fontweight="bold",
                    color=PALETTE["gold_text"] if lab == hl else PALETTE["fg"], zorder=5)
    _draw_hlines(ax, spec.get("hlines", []))
    ax.set_xticks(xs, labels, fontsize=SIZES["label"] if n <= 8 else (SIZES["tick"] - 1 if n <= 12 else SIZES["tick"] - 4))
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ydec = 0 if span >= 8 else 1
    ax.yaxis.set_major_formatter(
        lambda v, _: (f"{v:+,.{ydec}f}" if signed and abs(v) > 1e-9 else f"{v:,.{ydec}f}").replace("-", "−") + tick_unit)
    ax.margins(x=0.02)
    return save_jpeg(fig, out)


_RENDERERS = {"A": chart_a, "B": chart_b, "C": chart_c, "D": chart_d, "E": chart_e, "F": chart_f,
              "G": chart_g, "H": chart_h, "I": chart_i}


def render(spec: dict, out_path: Path, number: int) -> Path:
    kind = spec.get("type")
    if kind not in _RENDERERS:
        raise ValueError(f"unknown chart type: {kind!r}（A〜I のいずれか）")
    return _RENDERERS[kind](spec, Path(out_path), number)
