"""図表の共通スタイル（1280×720、配色、タイトル・出典・通し番号・ロゴ）。"""
from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from PIL import Image  # noqa: E402

from . import fonts  # noqa: E402

PALETTE = {
    "navy": "#1E3A5F",
    "navy2": "#3B6EA8",
    "gold": "#D4A017",
    "gold_text": "#8A6D12",
    "up": "#16A34A",
    "down": "#DC2626",
    "bg": "#FAF8F3",
    "paper": "#FFFFFF",
    "fg": "#1F2328",
    "muted": "#5E6470",
    "grid": "#E5E1D8",
    "soft": "#FBF3DC",
}
# スマホ（幅約360px）で拡大せずに読める大きさ（pt、1280×720 を 1.5 倍で書き出す前提）
SIZES = {
    "title": 36, "subtitle": 18, "source": 13, "number": 30,
    "tick": 18, "label": 20, "annot": 22, "value": 20,
    "card_label": 22, "card_value": 50, "card_sub": 22,
    "table_head": 21, "table": 20, "box": 24,
}
TONE = {"up": PALETTE["up"], "down": PALETTE["down"], "navy": PALETTE["navy"], "gold": PALETTE["gold"]}

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 7.2, 150  # 1280×720 を 1.5 倍（1920×1080）で書き出す
BODY_RECT = (0.075, 0.14, 0.885, 0.64)  # 本体領域（figure 座標）
BRAND_DIR = Path(__file__).resolve().parent.parent / "assets" / "brand"
JPEG_QUALITY = 90


def circled(n: int) -> str:
    return chr(0x2460 + n - 1) if 1 <= n <= 20 else str(n)


def source_text(source: str, web_search: bool = False) -> str:
    return f"{source}（Web検索値）" if web_search else source


def new_canvas(title: str, subtitle: str, source: str, number: int,
               web_search: bool = False) -> tuple[Figure, Axes]:
    """タイトル・サブタイトル・出典・通し番号を描いたキャンバスと、本体用の Axes を返す。"""
    fonts.ensure_fonts()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=PALETTE["bg"])
    fig.add_artist(plt.Rectangle((0.0, 0.84), 0.012, 0.13, transform=fig.transFigure,
                                 color=PALETTE["navy"]))  # タイトル左の色帯（アクセント）
    t = fig.text(0.035, 0.925, title, fontsize=SIZES["title"], fontweight="bold", color=PALETTE["navy"], va="center")
    _shrink_to_width(fig, t, max_frac=0.89)
    if subtitle:
        fig.text(0.035, 0.858, subtitle, fontsize=SIZES["subtitle"], color=PALETTE["muted"], va="center")
    fig.text(0.962, 0.925, circled(number), fontsize=SIZES["number"], color=PALETTE["gold_text"],
             ha="center", va="center", fontweight="bold")
    fig.text(0.035, 0.035, source_text(source, web_search), fontsize=SIZES["source"], color=PALETTE["muted"],
             va="center")
    ax = fig.add_axes(BODY_RECT)
    style_axes(ax)
    return fig, ax


def _shrink_to_width(fig: Figure, text, max_frac: float, min_size: float = 22) -> None:
    """タイトルが通し番号にかからないよう、幅に収まるまで文字を小さくする。"""
    renderer = fig.canvas.get_renderer()
    while text.get_fontsize() > min_size:
        if text.get_window_extent(renderer).x1 <= fig.bbox.width * max_frac:
            return
        text.set_fontsize(text.get_fontsize() - 1)


def style_axes(ax: Axes) -> None:
    ax.set_facecolor(PALETTE["bg"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#8A8578")
    ax.spines["bottom"].set_linewidth(1.5)
    ax.tick_params(colors=PALETTE["fg"], labelsize=SIZES["tick"], length=0, pad=8)
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=1.2)
    ax.set_axisbelow(True)


def blank_axes(ax: Axes) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


def _paste_logo(im: Image.Image) -> Image.Image:
    logo_path = BRAND_DIR / "logo_navy.png"
    if not logo_path.exists():
        return im
    size = round(im.width * 0.06)
    logo = Image.open(logo_path).convert("RGBA").resize((size, size), Image.LANCZOS)
    alpha = logo.getchannel("A").point(lambda a: int(a * 0.85))
    logo.putalpha(alpha)
    x = im.width - size - round(im.width * 0.033)
    y = im.height - size - round(im.height * 0.02)
    base = im.convert("RGBA")
    base.alpha_composite(logo, (x, y))
    return base.convert("RGB")


def save_jpeg(fig: Figure, path: Path, logo: bool = False) -> Path:
    """JPEG で保存する。記事中の図にはロゴを入れない（2026-11-08 ユーザー指示）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    im = Image.open(buf).convert("RGB")
    if logo:
        im = _paste_logo(im)
    im.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return path
