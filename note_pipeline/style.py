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
    "gold": "#C9A227",
    "gold_text": "#8A6D12",
    "up": "#2E8B57",
    "down": "#C0392B",
    "bg": "#FAF8F3",
    "paper": "#FFFFFF",
    "fg": "#1F2328",
    "muted": "#5E6470",
    "grid": "#E5E1D8",
    "soft": "#FBF3DC",
}
TONE = {"up": PALETTE["up"], "down": PALETTE["down"], "navy": PALETTE["navy"], "gold": PALETTE["gold"]}

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 7.2, 150  # 1280×720 を 1.5 倍（1920×1080）で書き出す
BODY_RECT = (0.06, 0.15, 0.88, 0.64)  # 本体領域（figure 座標）
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
    fig.text(0.045, 0.925, title, fontsize=26, fontweight="bold", color=PALETTE["navy"], va="center")
    if subtitle:
        fig.text(0.045, 0.868, subtitle, fontsize=12.5, color=PALETTE["muted"], va="center")
    fig.text(0.943, 0.928, circled(number), fontsize=24, color=PALETTE["gold_text"], ha="center", va="center")
    fig.text(0.045, 0.042, source_text(source, web_search), fontsize=9.5, color=PALETTE["muted"], va="center")
    ax = fig.add_axes(BODY_RECT)
    style_axes(ax)
    return fig, ax


def style_axes(ax: Axes) -> None:
    ax.set_facecolor(PALETTE["bg"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#B8B2A5")
    ax.tick_params(colors=PALETTE["muted"], labelsize=11, length=0)
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=1)
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


def save_jpeg(fig: Figure, path: Path, logo: bool = True) -> Path:
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
