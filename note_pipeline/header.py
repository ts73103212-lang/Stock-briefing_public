"""見出し画像（1280×670、設計書 §5.3）。左にコーギー、右にタイトルの要点。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

from . import fonts
from .style import BRAND_DIR, JPEG_QUALITY

W, H = 1920, 1005  # 1280×670 を 1.5 倍
LEFT_W = 700

# kind: (グラデーション開始色, 終了色, アクセント色) — 暗い背景＋金のアクセントでインパクトを出す
THEMES = {
    "theme": ("#050F1E", "#1A3D6B", "#F5C542"),
    "stock": ("#03140C", "#0E5A36", "#F5C542"),
    "paid": ("#0E0A03", "#5A460F", "#FFD54A"),
}
# 設計書 §5.4: テーマ＝シルクハット版、注目銘柄＝ハンチング帽版。有料は試作どおりシルクハット版。
CORGI = {"theme": "corgi_tophat.png", "stock": "corgi_hunting.png", "paid": "corgi_tophat.png"}
HIGHLIGHT = set("0123456789０１２３４５６７８９%％+＋-−－.,，円億万兆倍")


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(fonts.ensure_fonts()[weight]), size)


def _hex(c: str) -> tuple[int, int, int]:
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _gradient(c0: str, c1: str) -> Image.Image:
    """左上→右下の斜めグラデーション。"""
    a, b = _hex(c0), _hex(c1)
    small = Image.new("RGB", (64, 34))
    px = small.load()
    for x in range(64):
        for y in range(34):
            t = min(1.0, (x / 63) * 0.7 + (1 - y / 33) * 0.3)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return small.resize((W, H), Image.BICUBIC)


def _decorate(im: Image.Image, accent: str) -> None:
    """背景に薄い上昇チャートと光の筋を描く（文字の邪魔をしない程度）。"""
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    ac = _hex(accent)
    pts = [(LEFT_W + 40 + i * 70, 860 - (i * 23) - (60 if i % 3 == 1 else 0)) for i in range(18)]
    d.line(pts, fill=ac + (60,), width=6)
    for i, (x, y) in enumerate(pts[::2]):
        h = 40 + (i * 37) % 120
        d.rectangle((x - 9, y - h // 2, x + 9, y + h // 2), fill=(255, 255, 255, 18))
    for k in range(4):
        d.line((LEFT_W + 200 * k, H, W, 120 + 150 * k), fill=(255, 255, 255, 10), width=40)
    im.paste(over, (0, 0), over)


def _draw_highlighted(draw: ImageDraw.ImageDraw, xy, text: str, font, base, accent) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=accent if ch in HIGHLIGHT else base)
        x += draw.textlength(ch, font=font)


NO_LINE_START = set("、。，．,.）)」』】！？!?ー…・ぁぃぅぇぉっゃゅょァィゥェォッャュョ")
BREAK_AFTER = set("、。，,）)」』】！？!? ─—")


_TOKEN_RE = re.compile(r"[+＋\-−－]?[0-9０-９][0-9０-９,，.．]*[%％円億万兆倍]*|[A-Za-z][A-Za-z0-9&.\-]*|.", re.S)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """折り返す。数字・英単語は途中で切らず、行頭禁則（句読点・小書き文字）は前の行に追い出す。"""
    lines: list[str] = []
    for para in text.split("\n"):
        line = ""
        for tok in _TOKEN_RE.findall(para):
            if draw.textlength(line + tok, font=font) > max_w and line and tok[0] not in NO_LINE_START:
                lines.append(line)
                line = tok
            else:
                line += tok
        lines.append(line)
    return lines


def _break_score(lines: list[str]) -> int:
    """句読点の直後で改行している行の数（多いほど自然）。"""
    return sum(1 for ln in lines[:-1] if ln and ln[-1] in BREAK_AFTER)


def _balanced_wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """行数を増やさない幅の中から、句読点の後で切れる・最終行が短すぎない折り返しを選ぶ。"""
    lines = _wrap(draw, text, font, max_w)
    n = len(lines)
    best, best_key = lines, None
    w = max_w
    while w > max_w * 0.45:
        cand = _wrap(draw, text, font, w)
        if len(cand) > n:
            break
        widths = [draw.textlength(c, font=font) for c in cand]
        key = (_break_score(cand), min(widths) / max(widths) if max(widths) else 0)
        if best_key is None or key > best_key:
            best, best_key = cand, key
        w -= 12
    return best


def _corgi(kind: str) -> Image.Image | None:
    for name in (CORGI[kind], "corgi_tophat.png"):
        p = BRAND_DIR / name
        if p.exists():
            return Image.open(p).convert("RGBA")
    return None


def render_header(kind: Literal["theme", "stock", "paid"], label: str, title: str, lead: str,
                  out_path: Path, callouts: list[str] | None = None) -> Path:
    """仮の見出し画像。暗いグラデーション＋大きな白文字（数字は金色）＋数字の強調枠。

    本番の見出しは、納品ページの「見出し画像の提案」（画像生成AI用プロンプト）で作ることを想定。
    """
    if kind not in THEMES:
        raise ValueError(f"unknown header kind: {kind!r}")
    c0, c1, accent = THEMES[kind]
    im = _gradient(c0, c1)
    _decorate(im, accent)
    draw = ImageDraw.Draw(im)
    corgi = _corgi(kind)
    if corgi is not None:
        size = 560
        cx, cy = LEFT_W // 2 + 20, H // 2
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((cx - size // 2 - 40, cy - size // 2 - 40, cx + size // 2 + 40, cy + size // 2 + 40),
                                     fill=_hex(accent) + (55,))
        im.paste(glow, (0, 0), glow)
        draw.ellipse((cx - size // 2 - 12, cy - size // 2 - 12, cx + size // 2 + 12, cy + size // 2 + 12),
                     fill=accent)
        corgi = corgi.resize((size, size), Image.LANCZOS)
        im.paste(corgi, (cx - size // 2, cy - size // 2), corgi)
    x, max_w = LEFT_W + 80, W - LEFT_W - 80 - 90
    y = 110
    if label:
        f_label = _font("bold", 40)
        tw = draw.textlength(label, font=f_label)
        draw.rounded_rectangle((x, y, x + tw + 48, y + 70), radius=35, fill=accent)
        draw.text((x + 24, y + 10), label, font=f_label, fill=c0)
        y += 120
    size = 104
    while True:
        f_title = _font("bold", size)
        lines = _balanced_wrap(draw, title, f_title, max_w)
        if len(lines) <= 3 or size <= 60:
            break
        size -= 8
    for ln in lines[:4]:
        # 影を付けて背景から浮かせる
        _draw_highlighted(draw, (x + 4, y + 5), ln, f_title, (0, 0, 0), (0, 0, 0))
        _draw_highlighted(draw, (x, y), ln, f_title, (255, 255, 255), _hex(accent))
        y += int(size * 1.32)
    y += 30
    callouts = [c for c in (callouts or []) if c][:3]
    if callouts:
        f_c = _font("bold", 54)
        cx = x
        for c in callouts:
            tw = draw.textlength(c, font=f_c)
            if cx + tw + 60 > W - 60:
                break
            draw.rounded_rectangle((cx, y, cx + tw + 56, y + 96), radius=14, fill=(0, 0, 0), outline=accent, width=5)
            draw.text((cx + 28, y + 14), c, font=f_c, fill=accent)
            cx += tw + 56 + 28
    elif lead:
        f_lead = _font("regular", 44)
        for ln in _wrap(draw, lead, f_lead, max_w)[:2]:
            draw.text((x, y), ln, font=f_lead, fill=(225, 230, 238))
            y += 70
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out_path
