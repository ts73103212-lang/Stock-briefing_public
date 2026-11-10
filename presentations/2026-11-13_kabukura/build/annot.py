"""添付の週足チャート（証券アプリのスクリーンショット）に手書き風の書き込みを重ねる。

画像はPDFを200dpiで描画し、チャート部分を切り出したもの（1854×1042px、crop-NN.png）。
価格→y座標は軸ラベル2点で線形に合わせ、日付→x座標は日付目盛り（26/10 = x1587、1週 = 13.05px）で合わせる。
"""
from __future__ import annotations

import base64
import io
from datetime import date
from pathlib import Path

from PIL import Image

SRC = Path("/tmp/claude-0/-home-user-Stock-briefing-public/8a7f5c9f-29a7-5c14-9d80-8dcf137822fc/scratchpad/charts")
ASSET = Path(__file__).parent / "charts"  # 縮小済みJPEGを置く（リポジトリに保存）

# 価格軸の較正（v1, y1, v2, y2）。y は切り出し画像の座標
CAL = {
    "sbg": (1, 8000, 385, 2000, 612),
    "mhi": (2, 5000, 372, 1000, 625),
    "ndx": (3, 30000, 404, 20000, 593),
    "sox": (4, 14000, 364, 4000, 634),
    "n225": (6, 70000, 372, 30000, 625),
    "tsm": (7, 400, 385, 100, 612),
    "arm": (8, 400, 385, 100, 612),
    "mu": (9, 1200, 364, 200, 634),
    "iore": (10, 800, 385, 200, 612),
    "ds": (11, 6000, 364, 2000, 580),
    "nbis": (12, 250, 372, 100, 562),
    "crwv": (13, 150, 404, 50, 593),
    "spcx": (14, 220, 364, 120, 634),
    "advt": (19, 40000, 385, 10000, 612),
    "fjk": (20, 8000, 385, 2000, 612),
    "frk": (21, 6000, 364, 1000, 634),
    "kxa": (22, 35000, 357, 15000, 546),
    "mp": (23, 1500, 404, 500, 593),
    "mstr": (24, 500, 372, 100, 625),
}
TOP, BOTTOM = 245, 965  # 表示する縦範囲（ツールバーより下〜日付目盛り）
W = 1854
X_OCT1, PX_WEEK = 1587, 13.05
NOW = date(2026, 11, 10)
ZONE_X0, ZONE_X1 = 1672, 1850  # 価格軸の欄を塗りつぶして予想ゾーンにする
PANEL_Y1 = 712  # 価格パネルの下端

YEL, PINK, CYAN, WHITE, GREEN, RED = "#FFE14D", "#FF5FA2", "#5CE1E6", "#FFFFFF", "#7CFC8A", "#FF4D4D"
HAND = "font-family=\"Yomogi,'Klee One','Meiryo UI',sans-serif\""


def _img_b64(key: str, crop=None) -> str:
    """切り出し画像を縮小JPEGにしてbase64で返す（ASSETにキャッシュ）。"""
    ASSET.mkdir(exist_ok=True)
    out = ASSET / f"{key}.jpg"
    if not out.exists():
        n = CAL[key][0] if key in CAL else crop
        im = Image.open(SRC / f"crop-{n:02d}.png").convert("RGB").crop((0, TOP, W, BOTTOM))
        im.save(out, "JPEG", quality=72, optimize=True)
    return base64.b64encode(out.read_bytes()).decode()


class Chart:
    def __init__(self, key: str, disp_px: float, view=(0, TOP, W, BOTTOM)):
        """view=(x0,y0,x1,y1)：拡大して見せる範囲（切り出し画像の座標）。"""
        self.key = key
        _, self.v1, self.y1, self.v2, self.y2 = CAL[key]
        self.view = view
        self.u = (view[2] - view[0]) / disp_px  # 表示1pxあたりのviewBox単位
        self.items: list[str] = []
        self.top_items: list[str] = []

    def y(self, v):
        return self.y1 + (v - self.v1) * (self.y2 - self.y1) / (self.v2 - self.v1)

    @staticmethod
    def x(d: str | date):
        """過去は実際の日付目盛り。11/10より先は右端の「予想ゾーン」（x1672〜1848）に圧縮して描く。"""
        if isinstance(d, str):
            d = date.fromisoformat(d)
        if d > NOW:
            return ZONE_X0 + 8 + (d - NOW).days / (date(2027, 3, 31) - NOW).days * (ZONE_X1 - ZONE_X0 - 14)
        return X_OCT1 + (d - date(2026, 10, 1)).days / 7 * PX_WEEK

    def _text(self, x, y, s, size=11, color=YEL, anchor="start", rot=0, weight="700"):
        fs = size * self.u
        tr = f' transform="rotate({rot} {x:.0f} {y:.0f})"' if rot else ""
        self.top_items.append(
            f'<text x="{x:.0f}" y="{y:.0f}" font-size="{fs:.0f}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}" {HAND}{tr} '
            f'paint-order="stroke" stroke="#0B1240" stroke-width="{fs*0.28:.0f}" stroke-linejoin="round">{s}</text>')

    def hline(self, v, label, color=YEL, x0=60, x1=1848, dash=True, size=10.5, lx=None, above=True):
        y = self.y(v)
        sw = 2.2 * self.u
        self.items.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="{sw:.1f}" stroke-dasharray="{"%d %d" % (8*self.u, 5*self.u) if dash else ""}" stroke-linecap="round"/>')
        self._text(lx if lx is not None else x0 + 10, y - 6 * self.u if above else y + 15 * self.u, label, size, color)

    def band(self, va, vb, label=None, color=PINK, x0=60, x1=1848, size=10.5, lx=None, op=0.28):
        ya, yb = sorted([self.y(va), self.y(vb)])
        self.items.append(f'<rect x="{x0}" y="{ya:.0f}" width="{x1-x0}" height="{yb-ya:.0f}" fill="{color}" opacity="{op}" rx="{6*self.u:.0f}"/>')
        if label:
            self._text(lx if lx is not None else x0 + 12, ya + (yb - ya) / 2 + 4 * self.u, label, size, WHITE)

    def path(self, pts, color=YEL, arrow=True, dash=False, width=3.2):
        xy = [(self.x(d), self.y(v)) for d, v in pts]
        d = f"M{xy[0][0]:.0f},{xy[0][1]:.0f} "
        for i in range(1, len(xy)):
            (xa, ya), (xb, yb) = xy[i - 1], xy[i]
            cx = (xa + xb) / 2
            d += f"Q{cx:.0f},{(ya if i % 2 else yb):.0f} {xb:.0f},{yb:.0f} "
        sw = width * self.u
        mk = f' marker-end="url(#ar-{self.key}-{len(self.items)})"' if arrow else ""
        if arrow:
            self.items.append(f'<defs><marker id="ar-{self.key}-{len(self.items)}" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>')
        self.items.append(f'<path d="{d}" fill="none" stroke="#0B1240" stroke-width="{sw*2.2:.0f}" stroke-linecap="round" opacity="0.55"/>')
        self.items.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw:.0f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{"%d %d" % (10*self.u, 6*self.u) if dash else ""}"{mk}/>')

    def circle(self, d, v, r=14, color=PINK, label=None, size=10, dx=1, dy=-1):
        x, y = self.x(d), self.y(v)
        rr = r * self.u
        self.items.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rr*1.25:.0f}" ry="{rr:.0f}" fill="none" stroke="{color}" stroke-width="{2.6*self.u:.0f}" transform="rotate(-8 {x:.0f} {y:.0f})"/>')
        if label:
            self._text(x + dx * rr * 1.4, y + dy * rr * 1.1, label, size, color, "start" if dx > 0 else "end")

    def note(self, d, v, s, color=WHITE, size=10, anchor="start", rot=0):
        x = self.x(d) if isinstance(d, (str, date)) else d
        self._text(x, self.y(v) if v is not None else 0, s, size, color, anchor, rot)

    def note_xy(self, x, y, s, color=WHITE, size=10, anchor="start", rot=0):
        self._text(x, y, s, size, color, anchor, rot)

    def sticker(self, x, y, lines, color=YEL, size=13, rot=-4, w=None):
        """「ズバリ」の付箋。x,yはviewBox座標（左上）。"""
        fs = size * self.u
        lh = fs * 1.25
        ww = w or max(len(t) for t in lines) * fs * 0.98 + fs
        hh = lh * len(lines) + fs * 0.6
        g = [f'<g transform="rotate({rot} {x:.0f} {y:.0f})">',
             f'<rect x="{x:.0f}" y="{y:.0f}" width="{ww:.0f}" height="{hh:.0f}" rx="{fs*0.25:.0f}" fill="{color}" stroke="#0B1240" stroke-width="{fs*0.08:.0f}"/>']
        for i, t in enumerate(lines):
            g.append(f'<text x="{x+fs*0.5:.0f}" y="{y+fs*0.3+lh*(i+0.85):.0f}" font-size="{fs*(1 if i else 1.0):.0f}" fill="#0B1240" font-weight="700" {HAND}>{t}</text>')
        g.append("</g>")
        self.top_items.append("".join(g))

    def zone(self):
        """価格軸の欄を紺で塗り、予想ゾーン（12月〜3月）の目盛りを描く。"""
        y0 = max(self.view[1], TOP)
        z = [f'<rect x="{ZONE_X0}" y="{y0}" width="{W-ZONE_X0}" height="{PANEL_Y1-y0}" fill="#141C5C"/>',
             f'<line x1="{ZONE_X0}" x2="{ZONE_X0}" y1="{y0}" y2="{PANEL_Y1}" stroke="#FFE14D" stroke-width="{1.2*self.u:.1f}" stroke-dasharray="{4*self.u:.0f} {4*self.u:.0f}" opacity="0.7"/>']
        for m, d in (("12月", "2026-12-01"), ("1月", "2027-01-01"), ("2月", "2027-02-01"), ("3月", "2027-03-01")):
            xx = self.x(d)
            z.append(f'<line x1="{xx:.0f}" x2="{xx:.0f}" y1="{y0}" y2="{PANEL_Y1}" stroke="#FFFFFF" stroke-width="{0.6*self.u:.1f}" opacity="0.18"/>')
        yb = min(self.view[3], PANEL_Y1) - 6 * self.u
        for m, d in (("12", "2026-12-15"), ("1", "2027-01-15"), ("2", "2027-02-14"), ("3月", "2027-03-15")):
            z.append(f'<text x="{self.x(d):.0f}" y="{yb:.0f}" font-size="{8.5*self.u:.0f}" fill="#AFC3E8" text-anchor="middle" {HAND}>{m}</text>')
        z.append(f'<text x="{(ZONE_X0+ZONE_X1)/2:.0f}" y="{y0 + 13*self.u:.0f}" font-size="{9.5*self.u:.0f}" fill="#FFE14D" text-anchor="middle" font-weight="700" {HAND}>予想ゾーン</text>')
        return "".join(z)

    def now(self, v, label, dy=-1):
        """現在値の白丸とラベル（最新の足の左上）。"""
        x, y = self.x(NOW), self.y(v)
        self.top_items.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{4.5*self.u:.0f}" fill="#FFFFFF" stroke="#0B1240" stroke-width="{1.5*self.u:.0f}"/>')
        self._text(x - 8 * self.u, y + dy * 12 * self.u, label, 10.5, WHITE, "end")

    def svg(self):
        b64 = _img_b64(self.key)
        h = BOTTOM - TOP
        x0, y0, x1, y1 = self.view
        return (f'<svg viewBox="{x0} {y0} {x1-x0} {y1-y0}" xmlns="http://www.w3.org/2000/svg" role="img" style="background:#121A5A;border-radius:3px">'
                f'<image href="data:image/jpeg;base64,{b64}" x="0" y="{TOP}" width="{W}" height="{h}"/>'
                + self.zone() + "".join(self.items) + "".join(self.top_items) + "</svg>")


def image_fig(path: Path, key: str, box=None, width=1236, quality=80) -> str:
    """任意の画像（BTCチャートなど）を縮小してbase64で返す。"""
    ASSET.mkdir(exist_ok=True)
    out = ASSET / f"{key}.jpg"
    if not out.exists():
        im = Image.open(path).convert("RGB")
        if box:
            im = im.crop(box)
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(out, "JPEG", quality=quality, optimize=True)
    return base64.b64encode(out.read_bytes()).decode()
