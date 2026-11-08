"""見出し画像（1280×670、設計書 §5.3）。左にコーギー、右にタイトルの要点。"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

from . import fonts
from .style import BRAND_DIR, JPEG_QUALITY

W, H = 1920, 1005  # 1280×670 を 1.5 倍
LEFT_W = 728

# kind: (左パネル, 右パネル, ラベル色, タイトル色, リード色)
THEMES = {
    "theme": ("#1E3A5F", "#24466F", "#E2C26A", "#FFFFFF", "#DCE4EE"),
    "stock": ("#2E8B57", "#2A7D4F", "#F3E3A6", "#FFFFFF", "#E3F1E8"),
    "paid": ("#E6C46E", "#F5E6B8", "#8A6D12", "#1E3A5F", "#1F2328"),
}
# 設計書 §5.4: テーマ＝シルクハット版、注目銘柄＝ハンチング帽版。有料は試作どおりシルクハット版。
CORGI = {"theme": "corgi_tophat.png", "stock": "corgi_hunting.png", "paid": "corgi_tophat.png"}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(fonts.ensure_fonts()[weight]), size)


NO_LINE_START = set("、。，．,.）)」』】！？!?ー…・ぁぃぅぇぉっゃゅょァィゥェォッャュョ")
BREAK_AFTER = set("、。，,）)」』】！？!? ─—")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """文字単位で折り返す。行頭禁則（句読点・小書き文字）は前の行に追い出す。"""
    lines: list[str] = []
    for para in text.split("\n"):
        line = ""
        for ch in para:
            if draw.textlength(line + ch, font=font) > max_w and line and ch not in NO_LINE_START:
                lines.append(line)
                line = ch
            else:
                line += ch
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
                  out_path: Path) -> Path:
    if kind not in THEMES:
        raise ValueError(f"unknown header kind: {kind!r}")
    left, right, c_label, c_title, c_lead = THEMES[kind]
    im = Image.new("RGB", (W, H), right)
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, LEFT_W, H), fill=left)
    corgi = _corgi(kind)
    if corgi is not None:
        size = 640
        corgi = corgi.resize((size, size), Image.LANCZOS)
        im.paste(corgi, ((LEFT_W - size) // 2, (H - size) // 2), corgi)
    x, max_w = 808, W - 808 - 110
    y = 170
    if label:
        draw.text((x, y), label, font=_font("bold", 36), fill=c_label)
    size = 84
    while True:
        f_title = _font("bold", size)
        lines = _balanced_wrap(draw, title, f_title, max_w)
        if len(lines) <= 3 or size <= 56:
            break
        size -= 6
    block_h = len(lines) * size * 1.75
    y = 300 + max(0, (3 - len(lines))) * size * 0.35
    for ln in lines:
        draw.text((x, y), ln, font=f_title, fill=c_title)
        y += size * 1.75
    if lead:
        f_lead = _font("regular", 42)
        y = max(y + 40, 300 + block_h + 60)
        for ln in _wrap(draw, lead, f_lead, max_w)[:3]:
            draw.text((x, y), ln, font=f_lead, fill=c_lead)
            y += 80
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out_path
