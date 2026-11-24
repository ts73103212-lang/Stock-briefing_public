"""吹き出しの組版と、横2コマ×4段の段画像の出力（設計書 §7.5）。

CLI: python -m manga_pipeline.compose --script script.json --panels DIR --out DIR

script.json:
  {"title": "…", "panels": [{"n": 1, "bubbles": [{"speaker": "mirai", "text": "1行目\\n2行目", "x": 0.38}]}, …]}
  - panels は n=1..8 の8件。bubbles は1〜2個。x は話者の横位置（0〜1）。
  - セリフは公開リポジトリに置かない（作業は WORK/ で行う）。
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- 見本の数値（設計書 §7.5） ---
PANEL = 660            # 1コマの一辺
ROW_MARGIN = 12        # 段画像の外側の余白
PANEL_GAP = 16         # コマ間
ROW_W = ROW_MARGIN * 2 + PANEL * 2 + PANEL_GAP   # 1360
ROW_H = ROW_MARGIN * 2 + PANEL                   # 684
FONT_SIZE = 34
LINE_SPACING = 8
BUBBLE_TOP = 14        # 吹き出しの上端（コマ上端から）
BUBBLE_MARGIN = 14     # 吹き出しとコマ端の最小距離
BUBBLE_GAP = 10        # 吹き出しが2つのときの縦の間隔
PAD_X = 24
PAD_Y = 19             # 見本は上下 18〜20px
RADIUS = 28
BUBBLE_BORDER = 3
TAIL_LEN = 34          # 吹き出しの下端から尻尾の先まで
TAIL_HALF = 14         # 尻尾の付け根の半幅
FRAME = 4              # コマの枠
NUM_D = 34             # 番号の丸の直径
NUM_COLOR = (0x1E, 0x3A, 0x5F)
NUM_FONT = 22
NUM_INSET = 8          # 番号の丸とコマ端の距離

MAX_LINES = 3
MAX_CHARS = 12
SPEAKERS = {"corgi", "mirai", "gonda"}
JPEG_QUALITY = 85
MAX_BYTES = 200 * 1024
MIN_QUALITY = 60


def wrap_lines(text: str) -> list[str]:
    """セリフを \\n で行に分ける。4行以上、または13字以上の行があれば ValueError（全角も半角も1字）。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("bubble text is empty")
    lines = text.split("\n")
    if len(lines) > MAX_LINES:
        raise ValueError(f"too many lines ({len(lines)} > {MAX_LINES}): {text!r}")
    for line in lines:
        if len(line) > MAX_CHARS:
            raise ValueError(f"line too long ({len(line)} > {MAX_CHARS}): {line!r}")
    return lines


def bubble_box(text_w: int, text_h: int, x: float, top: int = BUBBLE_TOP) -> tuple[int, int, int, int]:
    """吹き出しの矩形 (left, top, right, bottom) をコマ内の座標で返す。話者の x を中心に、コマ端から14px以上離す。"""
    w = text_w + PAD_X * 2
    h = text_h + PAD_Y * 2
    cx = round(x * PANEL)
    left = min(max(cx - w // 2, BUBBLE_MARGIN), PANEL - BUBBLE_MARGIN - w)
    return left, top, left + w, top + h


def _font(size: int) -> ImageFont.FreeTypeFont:
    from note_pipeline.fonts import ensure_fonts

    return ImageFont.truetype(str(ensure_fonts()["bold"]), size)


def _validate(script: dict) -> list[dict]:
    panels = script.get("panels") if isinstance(script, dict) else None
    if not isinstance(panels, list) or sorted(p.get("n") for p in panels) != list(range(1, 9)):
        raise ValueError("script.panels must have n = 1..8 exactly once")
    for p in panels:
        bubbles = p.get("bubbles")
        if not isinstance(bubbles, list) or not 1 <= len(bubbles) <= 2:
            raise ValueError(f"panel {p['n']}: bubbles must have 1..2 items")
        for b in bubbles:
            if b.get("speaker") not in SPEAKERS:
                raise ValueError(f"panel {p['n']}: unknown speaker {b.get('speaker')!r}")
            x = b.get("x")
            if not isinstance(x, (int, float)) or isinstance(x, bool) or not 0 <= x <= 1:
                raise ValueError(f"panel {p['n']}: x must be 0..1")
            wrap_lines(b.get("text"))
    return sorted(panels, key=lambda p: p["n"])


def _draw_bubbles(img: Image.Image, bubbles: list[dict], font: ImageFont.FreeTypeFont) -> None:
    draw = ImageDraw.Draw(img)
    top = BUBBLE_TOP
    for b in bubbles:
        lines = wrap_lines(b["text"])
        text_w = max(round(font.getlength(line)) for line in lines)
        text_h = FONT_SIZE * len(lines) + LINE_SPACING * (len(lines) - 1)
        l, t, r, btm = bubble_box(text_w, text_h, b["x"], top)
        # 尻尾：吹き出しの下端から、話者の x の方へ 34px 下まで
        sx = min(max(round(b["x"] * PANEL), BUBBLE_MARGIN), PANEL - BUBBLE_MARGIN)
        base_c = min(max(sx, l + RADIUS + TAIL_HALF), r - RADIUS - TAIL_HALF)
        tail = [(base_c - TAIL_HALF, btm - BUBBLE_BORDER), (base_c + TAIL_HALF, btm - BUBBLE_BORDER),
                (sx, btm + TAIL_LEN)]
        draw.polygon(tail, fill="white", outline="black", width=BUBBLE_BORDER)
        draw.rounded_rectangle((l, t, r, btm), radius=RADIUS, fill="white", outline="black",
                               width=BUBBLE_BORDER)
        # 尻尾の付け根の枠線を消して、吹き出しとつなげる
        draw.rectangle((base_c - TAIL_HALF + BUBBLE_BORDER, btm - BUBBLE_BORDER - 1,
                        base_c + TAIL_HALF - BUBBLE_BORDER, btm), fill="white")
        for i, line in enumerate(lines):
            cy = t + PAD_Y + i * (FONT_SIZE + LINE_SPACING) + FONT_SIZE // 2
            draw.text((l + PAD_X, cy), line, font=font, fill="black", anchor="lm")
        top = btm + BUBBLE_GAP


def _panel_image(path: Path, panel: dict, font: ImageFont.FreeTypeFont,
                 num_font: ImageFont.FreeTypeFont) -> Image.Image:
    with Image.open(path) as src:
        img = src.convert("RGB").resize((PANEL, PANEL), Image.LANCZOS)
    _draw_bubbles(img, panel["bubbles"], font)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, PANEL - 1, PANEL - 1), outline="black", width=FRAME)
    x1 = PANEL - FRAME - NUM_INSET
    y1 = PANEL - FRAME - NUM_INSET
    draw.ellipse((x1 - NUM_D, y1 - NUM_D, x1, y1), fill=NUM_COLOR)
    draw.text((x1 - NUM_D / 2, y1 - NUM_D / 2), str(panel["n"]), font=num_font, fill="white", anchor="mm")
    return img


def _save_jpeg(img: Image.Image, out: Path) -> None:
    quality = JPEG_QUALITY
    while True:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality, optimize=True)
        if buf.tell() <= MAX_BYTES or quality <= MIN_QUALITY:
            break
        quality -= 5
    if buf.tell() > MAX_BYTES:
        raise ValueError(f"{out.name}: {buf.tell()} bytes > {MAX_BYTES} even at quality {quality}")
    out.write_bytes(buf.getvalue())


def compose_rows(script: dict, panel_dir: Path, out_dir: Path) -> list[Path]:
    """8コマを横2コマ×4段に組み、row1.jpg〜row4.jpg のパスを返す。"""
    panels = _validate(script)
    panel_dir, out_dir = Path(panel_dir), Path(out_dir)
    paths = {p["n"]: panel_dir / f"p{p['n']}.png" for p in panels}
    for path in paths.values():
        if not path.exists():
            raise FileNotFoundError(path)
    font, num_font = _font(FONT_SIZE), _font(NUM_FONT)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for k in range(4):
        row = Image.new("RGB", (ROW_W, ROW_H), "white")
        for j in range(2):
            p = panels[k * 2 + j]
            row.paste(_panel_image(paths[p["n"]], p, font, num_font),
                      (ROW_MARGIN + j * (PANEL + PANEL_GAP), ROW_MARGIN))
        out = out_dir / f"row{k + 1}.jpg"
        _save_jpeg(row, out)
        rows.append(out)
    return rows


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--panels", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    script = json.loads(a.script.read_text(encoding="utf-8"))
    for p in compose_rows(script, a.panels, a.out):
        print(p)


if __name__ == "__main__":
    main()
