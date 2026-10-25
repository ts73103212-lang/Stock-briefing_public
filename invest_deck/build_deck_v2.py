#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""20代・投資知識ゼロ向け『なぜ株式・インデックス投資は長期で増えるのか』16ページPDF(改訂版)。
数値は content_v2.json(根拠データ)と content.json(積立シミュレーション等)から読み込む。"""
import json, os, io, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "investment_deck_v2.pdf")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
D = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
V = json.load(open(os.path.join(HERE, "content_v2.json"), encoding="utf-8"))
DS = V["datasets"]
NPAGES = 16

# ---------- fonts ----------
fm.fontManager.addfont(FONT)
plt.rcParams["font.family"] = fm.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False
pdfmetrics.registerFont(TTFont("IPAP", FONT))
F = "IPAP"

# ---------- palette (意味を統一) ----------
BG = "#FBFAF6"; INK = "#1F2933"; MUTE = "#7B8794"; LIGHT = "#D9DDE1"
GRAY = "#8A9099"                      # 元本 / 預金
RED = "#D0453D"; RED_L = "#F2C9C5"    # インフレ・実質目減り・税・暴落
GREEN = "#1FA36B"; GREEN_L = "#A9E0C6"
BLUE = "#2563C9"; BLUE_L = "#B7CDF2"
TEAL = "#1B8C94"
NAVY = "#0F2A3D"
PALE_G = "#EEF7F2"; PALE_B = "#EEF3FC"; PALE_R = "#FBEDEC"; PALE_N = "#F1F2F4"

W, H = landscape(A4)   # 841.9 x 595.3
M = 40

# ---------- helpers ----------
def man(v, approx=True):
    s = f"{round(v/1e4):,}万円"
    return ("約" + s) if approx else s

def man_f(v):
    return f"約{int(v//10000):,}万円"

def yen(v):
    return f"{round(v):,}円"

def new_fig(wpt, hpt):
    fig = plt.figure(figsize=(wpt/72, hpt/72), dpi=100)
    fig.patch.set_alpha(0)
    return fig

def clean(ax, left=False, bottom=True, labelsize=10):
    ax.patch.set_alpha(0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    ax.spines["bottom"].set_color(LIGHT)
    ax.spines["left"].set_color(LIGHT)
    ax.tick_params(colors=MUTE, length=0, labelsize=labelsize)

def to_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=260, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return ImageReader(buf)

def put(c, img, x, y, w, h):
    c.drawImage(img, x, y, w, h, mask="auto")

def txt(c, x, y, s, size=12, color=INK, align="l"):
    c.setFont(F, size); c.setFillColor(HexColor(color))
    {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[align](x, y, s)

def fit(c, x, y, s, maxw, size, color=INK, align="l"):
    while pdfmetrics.stringWidth(s, F, size) > maxw and size > 8:
        size -= 1
    txt(c, x, y, s, size, color, align)
    return size

NB = set("0123456789,.%&/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
def wrap(s, size, maxw):
    lines, cur = [], ""
    for ch in s:
        if pdfmetrics.stringWidth(cur + ch, F, size) > maxw and cur:
            if cur[-1] in NB and ch in NB or (cur[-1] in "0123456789," and ch in "万円%年"):
                j = len(cur)
                while j > 0 and cur[j-1] in NB: j -= 1
                if j > 0:
                    lines.append(cur[:j]); cur = cur[j:] + ch; continue
            if ch in "、。,.)」』）":       # 行頭禁則(簡易)
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ""
        cur += ch
    if cur:
        lines.append(cur)
    return lines

def para(c, x, y, s, size, maxw, color=INK, lead=1.55):
    for ln in wrap(s, size, maxw):
        txt(c, x, y, ln, size, color); y -= size * lead
    return y

def bg(c, color=BG):
    c.setFillColor(HexColor(color)); c.rect(0, 0, W, H, stroke=0, fill=1)

def box(c, x, y, w, h, fill, stroke=None, r=10, lw=1.4, dash=None):
    c.setFillColor(HexColor(fill))
    if stroke:
        c.setStrokeColor(HexColor(stroke)); c.setLineWidth(lw)
    if dash: c.setDash(*dash)
    c.roundRect(x, y, w, h, r, stroke=1 if stroke else 0, fill=1)
    c.setDash()

def arrow(c, x1, y1, x2, y2, color=MUTE, lw=2.4, head=8):
    c.setStrokeColor(HexColor(color)); c.setFillColor(HexColor(color)); c.setLineWidth(lw)
    ang = np.arctan2(y2 - y1, x2 - x1)
    xe, ye = x2 - head*0.6*np.cos(ang), y2 - head*0.6*np.sin(ang)
    c.line(x1, y1, xe, ye)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head*np.cos(ang - 0.45), y2 - head*np.sin(ang - 0.45))
    p.lineTo(x2 - head*np.cos(ang + 0.45), y2 - head*np.sin(ang + 0.45))
    p.close(); c.drawPath(p, stroke=0, fill=1)

def ctext(c, cx, y, s, size, color=INK, maxw=None):
    """中央揃え(幅に収まるよう縮小)"""
    if maxw:
        while pdfmetrics.stringWidth(s, F, size) > maxw and size > 7: size -= 0.5
    txt(c, cx, y, s, size, color, "c")

ASSUME = ("前提: 年率3/5/7%は仮定で将来を保証しません。インフレ年2%、預金金利0.1%、月末積立・月次複利、"
          "手数料・信託報酬・税は除く(NISA前提)。")
def src_title(i):
    t = V["sources"][i]["title"]
    return re.split(r"[(:]", t)[0].strip()

def footer(c, n, src, dark=False, assume=ASSUME):
    col = "#9FB3C4" if dark else MUTE
    y = 30
    for ln in wrap("出典: " + src + "  " + assume, 7, W - 2*M - 50):
        txt(c, M, y, ln, 7, col); y -= 10
    txt(c, W - M, 30, f"{n} / {NPAGES}", 9, col, "r")

# 前ページの疑問(つなぎ)
Q = {
    2: "そもそも「株を買う」って、何を買っているの?",
    3: "会社が稼ぐ力は、何から生まれるの? まずは「人」から。",
    4: "人が増えるだけ? それとも他にも理由がある?",
    5: "人も工夫も増えると、会社や経済は実際どうなった?",
    6: "経済が大きくなったなら、株価の実際の動きは?",
    7: "ずっと右肩上がりなら安心…? 途中は平気だった?",
    8: "回復しなかったケースはないの?",
    9: "じゃあ、どう持てば1社の失敗や1国の低迷に強くなる?",
    10: "「年3%・5%・7%」って、ただの願望じゃない?",
    11: "増える理由はわかった。では何もしないと、どうなる?",
    12: "投資で、なぜ差が開いていくの?",
    13: "いくら・どれくらい続ければいい?",
    14: "いつ始めるのがいい?",
    15: "利益が出たら、税金はどうなる?",
    16: "わかった。で、今日から何をすればいい?",
}
def header(c, n, title, catch, color=GREEN):
    q = Q.get(n)
    if q:
        txt(c, M, H - 36, "Q.  " + q, 11.5, MUTE)
    c.setFillColor(HexColor(color)); c.rect(M, H - 56, 28, 4, stroke=0, fill=1)
    txt(c, M, H - 80, title, 22, INK)
    fit(c, M, H - 120, catch, W - 2*M, 30, color)

def hero(c, x, ytop, label, big, sub, color, w=212, size=46):
    txt(c, x, ytop, label, 11, MUTE)
    fit(c, x, ytop - 52, big, w, size, color)
    y = ytop - 78
    for s in sub:
        y = para(c, x, y, s, 11, w, INK, 1.5) - 4
    return y

def parse_ym(s):
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", s)
    y, mo = int(m.group(1)), int(m.group(2)); d = int(m.group(3)) if m.group(3) else 1
    return y + (mo - 1)/12 + (d - 1)/365

# ---------- data (v1: 積立シミュレーション) ----------
S = D["extra"]["series_10000_30y"]
T = {(t["monthly"], t["years"]): t for t in D["tables"]}
PM = {p["years"]: p for p in D["power_of_money"]}
DEP = {p["years"]: p for p in D["deposit_1m"]}
AGE = {a["start_age"]: a for a in D["age"]}
INFL = D["assumptions"]["inflation"]
TAX = D["tax"]; TAX2 = D["tax2"]; NISA = D["nisa"]; STRESS = D["stress"]
g = lambda k: np.array(S[k]) / 1e4
SRC = "試算は本資料の想定に基づく自作計算"

# ---------- data (v2: 根拠データ) ----------
POP = {p["year"]: p["value"] for p in DS["world_population"]["points"] if isinstance(p["value"], (int, float)) and p["year"] <= 2050}
GDP = [(p["year"], p["world_gdp_current_usd_trillion"]) for p in DS["world_gdp_nominal"]["points"]]
SP = [(1926.0, 1.0)] + [(p["year"], p["total_return_index_1926eq1"]) for p in DS["sp500_long"]["points"]
                          if p.get("total_return_index_1926eq1") is not None]
SPN = DS["sp500_stats"]
DD = DS["drawdowns"]["rows"]
NK = DS["nikkei_yearend"]["points"]

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("20代のうちに知りたい、NISA積立のはじめ方(なぜ投資でお金は増えるのか)")
c.setAuthor("")

# =====================================================================
# P1 表紙
# =====================================================================
bg(c, NAVY)
fig = new_fig(400, 380)
ax = fig.add_axes([0.02, 0.10, 0.96, 0.80]); ax.patch.set_alpha(0)
xs = np.array([p[0] for p in SP]); ys = np.array([p[1] for p in SP])
xf = np.linspace(xs[0], xs[-1], 300); yf = np.exp(np.interp(xf, xs, np.log(ys)))
ax.fill_between(xf, 0.5, yf, color=GREEN, alpha=0.18, lw=0)
ax.plot(xf, yf, color=GREEN_L, lw=3.2)
ax.set_yscale("log"); ax.set_ylim(0.5, 6e4); ax.set_xlim(1924, 2027)
ax.axis("off")
ax.text(1928, 9000, "米国株(S&P500)の例", color="#C9D3DC", fontsize=12, ha="left")
ax.text(1928, 2600, f"1926年を1とすると", color="#C9D3DC", fontsize=11, ha="left")
ax.text(1928, 600, f"約{round(ys[-1], -2):,.0f}倍", color="white", fontsize=34, ha="left")
ax.text(2024, 0.8, "2023年6月・配当込み", color="#9FB3C4", fontsize=9, ha="right")
put(c, to_img(fig), 420, 90, 390, 370)
txt(c, M + 4, H - 70, "20代のための はじめてのNISA", 13, GREEN_L)
y = H - 150
for ln in ["なぜ投資すると、", "お金が増えるの?"]:
    txt(c, M + 4, y, ln, 40, "#FFFFFF"); y -= 56
txt(c, M + 4, y - 4, "20代のうちに知りたい、NISA積立のはじめ方", 15, "#C9D3DC")
y -= 62
for b in ["投資って、なんで儲かるの?", "減り続けることはないの?", f"{NPAGES}ページで、理由と数字を順番に見ていきます"]:
    c.setFillColor(HexColor(GREEN)); c.circle(M + 10, y + 4, 4, stroke=0, fill=1)
    txt(c, M + 24, y, b, 14, "#FFFFFF"); y -= 28
footer(c, 1, "Robert Shiller data (Yale) をもとにした独自計算(米国株の例)", dark=True,
       assume="前提: 米国株の過去の結果であり、世界全体や将来の成果を保証するものではありません。")
c.showPage()

# =====================================================================
# P2 株とは
# =====================================================================
bg(c); header(c, 2, "株を買う = 会社の「オーナーの一人」になること",
              "寝ている間も、世界中の会社が働いてくれる。", GREEN)
# 上段: あなた → ファンド → 会社
yb, hb = 300, 130
box(c, M, yb, 150, hb, "#FFFFFF", GREEN, 14)
ctext(c, M + 75, yb + 88, "あなた", 20, GREEN)
ctext(c, M + 75, yb + 58, "月1,000円〜", 13, INK)
ctext(c, M + 75, yb + 36, "(少額でOK)", 11, MUTE)
box(c, 300, yb, 230, hb, PALE_G, GREEN, 14)
ctext(c, 415, yb + 92, "インデックスファンド", 17, GREEN, 210)
ctext(c, 415, yb + 66, "株をまとめて持つ「大きな箱」", 11.5, INK, 210)
ctext(c, 415, yb + 44, "(投資信託の一種)", 10.5, MUTE)
ctext(c, 415, yb + 22, "=たくさんの会社の一部を一度に買える", 9.5, MUTE, 215)
# 会社群
names = ["食品", "自動車", "IT", "医薬", "銀行", "小売"]
for i, nm in enumerate(names):
    cx = 640 + (i % 3) * 54; cy = yb + 82 - (i // 3) * 62
    box(c, cx, cy, 48, 50, "#FFFFFF", BLUE, 8, 1.2)
    ctext(c, cx + 24, cy + 20, nm, 11, BLUE, 44)
txt(c, 640, yb + 140, "世界の会社", 15, BLUE)
txt(c, 640, yb - 12, "(まだまだたくさん…)", 10, MUTE)
# 矢印(出資: 上、利益: 下)
arrow(c, M + 154, yb + 95, 296, yb + 95, GREEN)
arrow(c, 534, yb + 95, 634, yb + 95, GREEN)
ctext(c, 225, yb + 107, "お金を出す", 10.5, GREEN)
ctext(c, 584, yb + 107, "出資", 10.5, GREEN)
arrow(c, 634, yb + 28, 534, yb + 28, BLUE)
arrow(c, 296, yb + 28, M + 154, yb + 28, BLUE)
ctext(c, 584, yb + 12, "利益が戻る", 10.5, BLUE)
ctext(c, 225, yb + 12, "分け前が戻る", 10.5, BLUE)
# 用語
txt(c, M, 262, "ことば: ", 10.5, MUTE)
txt(c, M + 44, 262, "株=会社の持ち分(の証明) / 配当=会社の利益から株主に配られるお金 / 株価=その持ち分の値段", 10.5, INK)
# 下段 2 カード
cw = (W - 2*M - 28) / 2
box(c, M, 80, cw, 160, "#F1F2F4", GRAY, 12)
txt(c, M + 20, 212, "預金 = 銀行に「お金を貸す」", 16, "#5B6470")
para(c, M + 20, 186, "決まった利息(いまは低い)をもらう。お金は安全だが、増え方は小さい。", 12.5, cw - 40, INK)
txt(c, M + 20, 108, "貸す人 = 会社の成長は関係しない", 11.5, GRAY)
box(c, M + cw + 28, 80, cw, 160, PALE_G, GREEN, 12)
txt(c, M + cw + 48, 212, "株 = 会社の「持ち主」になる", 16, GREEN)
para(c, M + cw + 48, 186, "会社が成長して稼ぎが増えれば、配当や株価の上昇で自分の取り分も増える。", 12.5, cw - 40, INK)
txt(c, M + cw + 48, 108, "ただし、会社が不調なら下がることもある", 11.5, RED)
footer(c, 2, "仕組みの図解(数値なし)", assume="前提: 株価は上下し、元本割れの可能性があります。会社名は図の説明用の業種例です。")
c.showPage()

# =====================================================================
# P3 人口
# =====================================================================
bg(c); header(c, 3, "なぜ増える①: 世界の人が増えてきた",
              "人が増えると、働く人も買う人も増える。", BLUE)
fig = new_fig(520, 360)
ax = fig.add_axes([0.11, 0.12, 0.80, 0.80]); clean(ax, labelsize=11)
yrs = sorted(POP); vals = [POP[y_]/1e8 for y_ in yrs]
act = [y_ for y_ in yrs if y_ <= 2024]; actv = [POP[y_]/1e8 for y_ in act]
proj = [y_ for y_ in yrs if y_ >= 2024]; projv = [POP[y_]/1e8 for y_ in proj]
ax.fill_between(act, 0, actv, color=BLUE_L, alpha=0.55, lw=0)
ax.plot(act, actv, color=BLUE, lw=3.2)
ax.plot(proj, projv, color=BLUE, lw=2.6, ls=(0, (3, 2.5)))
for y_, off, lab_, col in ((1950, 14, "1950年\n約{:.0f}億人", BLUE), (2024, 6, "2024年\n約{:.0f}億人", BLUE), (2050, 6, "2050年(予測)\n約{:.0f}億人", MUTE)):
    v_ = POP[y_]/1e8
    ax.plot([y_], [v_], "o", color=col, ms=8, zorder=5)
    ax.text(y_, v_ + off, lab_.format(v_), ha="center" if y_ != 1950 else "left", fontsize=13, color=col, va="bottom")
ax.set_ylim(0, 125); ax.set_xlim(1945, 2057)
ax.set_xticks([1950, 1980, 2010, 2050]); ax.set_xticklabels(["1950", "1980", "2010", "2050"])
ax.set_yticks([0, 50, 100]); ax.set_yticklabels(["0", "50億", "100億"])
ax.grid(axis="y", color="#ECEDEF", lw=0.8); ax.set_axisbelow(True)
put(c, to_img(fig), M, 80, 520, 360)
mult = POP[2024]/POP[1950]
y = hero(c, 590, 440, "1950年 → 2024年", f"約{mult:.1f}倍", [
    f"世界の人口は約{POP[1950]/1e8:.0f}億人から約{POP[2024]/1e8:.0f}億人へ。70年あまりで3倍以上に。",
    f"国連の予測では2050年に約{POP[2050]/1e8:.0f}億人。ただし増え方は、少しずつゆるやかになる見込み。",
], BLUE, size=48)
box(c, 590, 100, 212, 66, PALE_B, None, 8)
para(c, 602, 146, "人の数だけで増え続けるわけではない。次は「1人あたり」の力を見てみよう。", 11, 190, BLUE)
footer(c, 3, f"{src_title(0)}、{src_title(2)}(1960-2024)",
       assume="前提: 実線は実績、点線は国連の中位推計(予測)。予測は将来の保証ではありません。")
c.showPage()

# =====================================================================
# P4 技術・工夫
# =====================================================================
bg(c); header(c, 4, "なぜ増える②: 技術と工夫で、1人がつくれる量が増える",
              "人が増える × 道具が進化する = 経済が大きくなる。", GREEN)
yb, hb = 215, 235
# パネル1 人
px, pw = M, 235
box(c, px, yb, pw, hb, "#FFFFFF", BLUE, 14)
ctext(c, px + pw/2, yb + hb - 30, "① 人の数", 17, BLUE)
for k, (n_, lab_, x0_) in enumerate(((round(POP[1950]/1e8), "1950年", px + 16), (round(POP[2024]/1e8), "2024年", px + 100))):
    cols_ = 5 if n_ < 30 else 9
    pitch = 11 if n_ < 30 else 10.5
    wdt = cols_ * pitch
    for i in range(n_):
        cx_ = x0_ + (i % cols_) * pitch + 5; cy_ = yb + 80 + (i // cols_) * pitch
        c.setFillColor(HexColor(BLUE if k else BLUE_L)); c.circle(cx_, cy_, 3.6, stroke=0, fill=1)
    ctext(c, x0_ + wdt/2, yb + 52, lab_, 11, INK)
    ctext(c, x0_ + wdt/2, yb + 36, f"約{n_}億人", 11, BLUE)
ctext(c, px + pw/2, yb + 14, "(●1つ=1億人)", 9.5, MUTE)
# パネル2 道具
qx = 330; qw = 235
box(c, qx, yb, qw, hb, "#FFFFFF", GREEN, 14)
ctext(c, qx + qw/2, yb + hb - 30, "② 1人あたりの生産", 17, GREEN)
steps_ = ["手作業", "機械", "電気", "コンピュータ", "AI"]
for i, s_ in enumerate(steps_):
    sx = qx + 16 + i*43; sh = 22 + i*22
    c.setFillColor(HexColor([GREEN_L, "#7FD0AB", "#4DBB8C", GREEN, "#118557"][i]))
    c.rect(sx, yb + 56, 40, sh, stroke=0, fill=1)
    ctext(c, sx + 20, yb + 40, s_, 8 if len(s_) > 3 else 10, INK, 42)
ctext(c, qx + qw/2, yb + 14, "道具や工夫が進むほど、同じ1人でも多くつくれる", 9, MUTE, 220)
# パネル3 結果
rx = 607; rw = 195
box(c, rx, yb, rw, hb, PALE_G, GREEN, 14)
ctext(c, rx + rw/2, yb + hb - 30, "③ 経済の大きさ", 17, GREEN)
ctext(c, rx + rw/2, yb + 150, "モノ・サービスの", 13, INK)
ctext(c, rx + rw/2, yb + 130, "量が増える", 13, INK)
arrow(c, rx + rw/2, yb + 118, rx + rw/2, yb + 88, GREEN)
ctext(c, rx + rw/2, yb + 62, "会社の売上・", 13, INK)
ctext(c, rx + rw/2, yb + 42, "利益が増える", 13, GREEN)
ctext(c, M + pw + 47, yb + 108, "×", 30, MUTE)
ctext(c, qx + qw + 21, yb + 108, "=", 30, MUTE)
box(c, M, 110, W - 2*M, 70, PALE_B, None, 10)
txt(c, M + 22, 150, "ポイント", 11, MUTE)
para(c, M + 22, 130, "人が増えるだけでなく、機械・電気・コンピュータ・AIのように「工夫」が積み重なるほど、1人がつくれる量も増える。この両方が、経済が大きくなってきた理由です。ただし将来も続く保証はありません。", 12.5, W - 2*M - 44, INK, 1.5)
footer(c, 4, f"{src_title(0)}(人口の目盛り)。図は仕組みの説明",
       assume="前提: 世界の経済規模の長期倍率は最新データで確認中のため、このページでは数値を載せていません。")
c.showPage()

# =====================================================================
# P5 GDP
# =====================================================================
bg(c); header(c, 5, "なぜ増える③: 経済が大きくなり、会社の利益が増える",
              "世界の経済規模は、長い目で見て大きくなってきた。", GREEN)
fig = new_fig(520, 300)
ax = fig.add_axes([0.02, 0.12, 0.96, 0.78]); clean(ax, labelsize=11)
gx = [str(y_) if y_ != 2023 else "2023" for y_, _ in GDP]; gv = [v_ for _, v_ in GDP]
cm = matplotlib.colors.LinearSegmentedColormap.from_list("b", [BLUE_L, BLUE])
ax.bar(range(len(gv)), gv, 0.68, color=[cm(i/(len(gv)-1)) for i in range(len(gv))])
for i, v_ in enumerate(gv):
    ax.text(i, v_ + 2.5, f"{v_:,.1f}兆" if v_ >= 10 else f"{v_:.1f}兆", ha="center", fontsize=12 if i in (0, len(gv)-1) else 10.5,
            color=BLUE if i in (0, len(gv)-1) else INK)
ax.set_xticks(range(len(gv))); ax.set_xticklabels([f"{x_}年" for x_ in gx], fontsize=10)
ax.set_yticks([]); ax.set_ylim(0, 125)
ax.text(-0.4, 118, "世界のGDP(名目・米ドル)", fontsize=13, color=INK, va="center")
put(c, to_img(fig), M, 175, 520, 300)
y = hero(c, 590, 440, "1960年 → 2023年", f"約{GDP[0][1]:.1f}兆→約{GDP[-1][1]:.0f}兆ドル", [
    "これは「名目」の数字(物価上昇の分もふくむ)。",
    "物価の影響をのぞいた「実質」でも長期で拡大してきたとされますが、倍率は確認中のため載せていません。",
], BLUE, size=30)
box(c, 590, 262, 212, 36, RED_L, None, 6)
ctext(c, 696, 275, "名目 = 物価上昇を含む金額", 11, RED, 200)
# フロー
fy = 78; fh = 70; fw = 210; gap = (W - 2*M - 3*fw) / 2
chips = [("経済が大きくなる", "売れるモノ・サービスが増える", BLUE), ("会社の利益が増える", "稼ぎが増えれば配当の元も増える", GREEN), ("株価も長期では", "利益に近づいていく傾向", GREEN)]
for i, (a_, b_, col) in enumerate(chips):
    x0_ = M + i*(fw + gap)
    box(c, x0_, fy, fw, fh, "#FFFFFF", col, 10)
    ctext(c, x0_ + fw/2, fy + 44, a_, 14.5, col, fw - 12)
    ctext(c, x0_ + fw/2, fy + 22, b_, 10.5, INK, fw - 12)
    if i < 2: arrow(c, x0_ + fw + 6, fy + fh/2, x0_ + fw + gap - 6, fy + fh/2, MUTE)
footer(c, 5, f"{src_title(2)} GDP(名目US$・当年価格)",
       assume="前提: 名目値のため物価上昇を含みます。2023年のみ年値、他は10年ごと。短期の株価は気分でも動き、利益と連動しない時期もあります。")
c.showPage()

# =====================================================================
# P6 100年の株価
# =====================================================================
bg(c); header(c, 6, "100年の株価: ギザギザでも、大きな右肩上がり",
              f"米国株の例: 1926年を1として約{round(SP[-1][1], -2):,.0f}倍(配当込み)。", GREEN)
fig = new_fig(540, 375)
ax = fig.add_axes([0.08, 0.10, 0.82, 0.86]); clean(ax, labelsize=11)
xf = np.linspace(SP[0][0], SP[-1][0], 400); yf = np.exp(np.interp(xf, xs, np.log(ys)))
ax.set_yscale("log"); ax.set_ylim(0.7, 2e5); ax.set_xlim(1926, 2031)
ax.fill_between(xf, 0.7, yf, color=GREEN_L, alpha=0.35, lw=0)
ax.plot(xf, yf, color=GREEN, lw=3)
ax.plot(xs[1:], ys[1:], "o", color=GREEN, ms=4, zorder=4)
bands = [(1929.75, 1932.5, "大恐慌 1929-32", "l", 2.2e3), (1987.6, 1987.95, "ブラックマンデー 1987", "r", 1.0e4),
         (2000.2, 2002.8, "ITバブル 2000-02", "r", 2.8e4), (2007.8, 2009.2, "リーマン 2007-09", "r", 7.5e4), (2020.1, 2020.3, "コロナ 2020", "r", 1.6e5)]
for a_, b_, lab_, al, yy_ in bands:
    ax.axvspan(a_, b_, color=RED, alpha=0.4, lw=0)
    if al == "l":
        ax.text(b_ + 1, yy_, lab_, color=RED, fontsize=10.5, ha="left", va="center")
    else:
        ax.text(b_ + 0.3, yy_, lab_, color=RED, fontsize=10.5, ha="right", va="center")
ax.text(2024.5, ys[-1], f"約{round(ys[-1], -2):,.0f}倍", color=GREEN, fontsize=14, va="center", ha="left")
ax.set_yticks([1, 10, 100, 1000, 10000]); ax.set_yticklabels(["1", "10", "100", "1,000", "1万"])
ax.set_xticks([1930, 1950, 1970, 1990, 2010]); ax.set_xticklabels(["1930", "1950", "1970", "1990", "2010"])
ax.minorticks_off(); ax.grid(axis="y", color="#ECEDEF", lw=0.8); ax.set_axisbelow(True)
put(c, to_img(fig), M - 5, 72, 540, 375)
y = hero(c, 590, 440, "米国株(S&P500)の例", f"約{round(ys[-1], -2):,.0f}倍", [
    f"1926年〜2023年6月、配当を再投資した場合。年平均で名目約{SPN['tr_nominal_cagr_pct']['1926-']:.0f}%、物価を引くと実質約{SPN['tr_real_cagr_pct']['1926-']:.0f}%。",
], GREEN, size=44)
box(c, 590, 215, 212, 94, PALE_N, None, 8)
txt(c, 602, 292, "グラフの見かた(対数)", 11, GREEN)
para(c, 602, 275, "1→10→100と、同じ倍率が同じ間隔。傾きが一定=一定の割合で増えた、という意味です。", 10.5, 192, INK, 1.45)
box(c, 590, 80, 212, 118, PALE_R, None, 8)
para(c, 602, 180, "これはアメリカの株の結果です。世界全体や将来を保証するものではありません。下がった時期も、はっきり見えています。", 11, 192, RED, 1.5)
footer(c, 6, f"{src_title(8)}、{src_title(10)}、{src_title(11)}(年率の確認)",
       assume="前提: 米国S&P500の配当再投資(総収益)を独自計算。10年ごとの月平均値をつないだ概略図で、細かい上下は省略。2023年6月まで。")
c.showPage()

# =====================================================================
# P7 暴落と回復
# =====================================================================
bg(c); header(c, 7, "暴落は何度もあった。でも、そのたび回復してきた",
              "ただし、戻るまでに数年〜十数年かかることもある。", RED)
rows = []
for r in DD:
    pk = parse_ym(r["peak"]); tr_ = parse_ym(r["trough"])
    rec_s = r.get("recovery_price") or r["recovery"]
    rc = parse_ym(rec_s)
    ym = re.search(r"約(\d+(?:\.\d+)?)年", rec_s)
    dur_txt = f"約{ym.group(1)}年" if ym else f"約{round((rc - pk)*12)}か月"
    extra = None
    if "recovery_total_return" in r:
        extra = (parse_ym(r["recovery_total_return"]) - pk, re.search(r"約(\d+)年", r["recovery_total_return"]).group(1))
    yr_lab = f"{int(pk)}-{str(int(tr_))[-2:]}" if int(pk) != int(tr_) else f"{int(pk)}"
    rows.append(dict(name=r["event"], drop=r["drop_pct"], t=tr_ - pk, rec=rc - pk, dur=dur_txt, extra=extra, yr=yr_lab))
fig = new_fig(762, 305)
ax = fig.add_axes([0.30, 0.14, 0.50, 0.76]); clean(ax, left=False, labelsize=10.5)
n = len(rows)
for i, r in enumerate(rows):
    yy_ = n - 1 - i
    ax.barh(yy_, r["t"], height=0.5, color=RED)
    ax.barh(yy_, r["rec"] - r["t"], left=r["t"], height=0.5, color=GREEN_L, edgecolor=GREEN, lw=1)
    fig.text(0.015, 0.14 + 0.76*(yy_ + 0.5)/n + 0.025, r["name"], fontsize=14, color=INK, va="center")
    fig.text(0.015, 0.14 + 0.76*(yy_ + 0.5)/n - 0.035, f"{r['yr']}年", fontsize=9.5, color=MUTE, va="center")
    fig.text(0.275, 0.14 + 0.76*(yy_ + 0.5)/n, f"{r['drop']}%", fontsize=19, color=RED, va="center", ha="right")
    fig.text(0.985, 0.14 + 0.76*(yy_ + 0.5)/n + (0.02 if r["extra"] else 0), r["dur"], fontsize=18, color="#127A4E", va="center", ha="right")
    if r["extra"]:
        ax.plot([r["extra"][0]]*2, [yy_ - 0.3, yy_ + 0.3], color=INK, lw=2)
        ax.text(r["extra"][0] - 0.3, yy_ + 0.36, f"配当込みなら約{r['extra'][1]}年", fontsize=9.5, color=INK, ha="right", va="bottom")
        fig.text(0.985, 0.14 + 0.76*(yy_ + 0.5)/n - 0.045, "(価格のみ)", fontsize=9, color=MUTE, va="center", ha="right")
ax.set_xlim(0, 26); ax.set_ylim(-0.6, n - 0.35); ax.set_yticks([])
ax.set_xticks([0, 5, 10, 15, 20, 25]); ax.set_xticklabels(["高値", "5年", "10年", "15年", "20年", "25年"])
ax.grid(axis="x", color="#ECEDEF", lw=0.8); ax.set_axisbelow(True)
fig.text(0.275, 0.96, "下落率", fontsize=10.5, color=MUTE, ha="right", va="center")
fig.text(0.985, 0.96, "元の高値に戻るまで", fontsize=10.5, color=MUTE, ha="right", va="center")
fig.text(0.30, 0.96, "■ 下落", fontsize=10.5, color=RED, va="center")
fig.text(0.36, 0.96, "■ 回復", fontsize=10.5, color=GREEN, va="center")
fig.text(0.44, 0.96, "(高値からの年数)", fontsize=10.5, color=MUTE, va="center")
put(c, to_img(fig), M, 148, 762, 305)
box(c, M, 70, W - 2*M, 62, PALE_G, GREEN, 10)
txt(c, M + 20, 98, "回復してきた。", 24, GREEN)
txt(c, M + 200, 98, "ただし数年〜十数年かかることも。保証ではなく、過去の事実です。", 16, INK)
footer(c, 7, f"{src_title(8)}(月平均の独自計算)、{src_title(15)}、{src_title(16)}",
       assume="前提: 米国S&P500。下落率は高値→安値の概算で、資料や計算方法により数%ちがいます。回復=元の高値(価格)を取り戻すまで。コロナは2020年2月→8月。")
c.showPage()

# =====================================================================
# P8 それでも減る場合
# =====================================================================
bg(c); header(c, 8, "それでも、減ることはある: 個別株と日本株の例",
              "1社に賭けると、ゼロになることもある。", RED)
# 左: 個別株図解
box(c, M, 90, 250, 375, "#FFFFFF", RED, 12)
txt(c, M + 16, 438, "個別の会社は倒れることがある", 13.5, RED)
txt(c, M + 16, 408, "1社に全部", 13, INK)
c.setFillColor(HexColor(RED_L)); c.roundRect(M + 16, 322, 80, 70, 8, stroke=0, fill=1)
c.setStrokeColor(HexColor(RED)); c.setLineWidth(2)
c.line(M + 16, 322, M + 96, 392); c.line(M + 16, 392, M + 96, 322)
ctext(c, M + 56, 348, "A社", 16, RED)
txt(c, M + 110, 365, "倒産 → 株価ゼロ", 12.5, RED)
txt(c, M + 110, 347, "→ 戻らない", 12.5, RED)
txt(c, M + 16, 304, "たくさんに分ける", 13, INK)
for i in range(30):
    cx_ = M + 16 + (i % 10) * 22; cy_ = 228 + (i // 10) * 22
    col = RED if i == 12 else GREEN
    c.setFillColor(HexColor(col if i == 12 else GREEN_L)); c.rect(cx_, cy_, 18, 18, stroke=0, fill=1)
    if i == 12:
        c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(1.5); c.line(cx_ + 3, cy_ + 3, cx_ + 15, cy_ + 15); c.line(cx_ + 3, cy_ + 15, cx_ + 15, cy_ + 3)
para(c, M + 16, 206, "1社が倒れても、全体への影響は小さくなる。", 12, 220, INK)
para(c, M + 16, 168, "これが「分散」。投資の基本の考え方です。", 12, 220, GREEN)
box(c, M + 16, 100, 218, 46, PALE_N, None, 6)
para(c, M + 26, 132, "分散=卵をひとつのかごに盛らない", 10.5, 200, MUTE)
# 右: 日経
fig = new_fig(520, 310)
ax = fig.add_axes([0.08, 0.10, 0.88, 0.76]); clean(ax, labelsize=11)
nx = [p["year"] for p in NK]; nv = [p["value"]/1e3 for p in NK]
hi = NK[0]["value"]/1e3
ax.fill_between(nx, nv, hi, where=[v_ < hi for v_ in nv], color=RED_L, alpha=0.6, lw=0, interpolate=True)
ax.plot(nx, nv, color="#4B5563", lw=2.6)
ax.axhline(hi, xmin=0.02, color=RED, ls=(0, (2, 2.5)), lw=1.4)
ax.plot([1989.98], [hi], "o", color=RED, ms=8, zorder=5)
ax.plot([NK[-1]["year"]], [NK[-1]["value"]/1e3], "o", color=GREEN, ms=9, zorder=5)
ax.text(1990.4, hi + 0.55, f"1989年末 {NK[0]['value']:,.0f}円(当時の最高値)", fontsize=11, color=RED, va="bottom")
ax.text(2020.3, 34.2, f"2024年2月に更新\n{NK[-1]['value']:,.0f}円", fontsize=11, color=GREEN, ha="right", va="center")
ax.annotate("", xy=(2024.1, 21), xytext=(1990.1, 21), arrowprops=dict(arrowstyle="<->", color=RED, lw=1.8))
ax.text(2007, 22.2, "高値を下回っていた期間 約34年", fontsize=14, color=RED, ha="center", va="bottom")
ax.set_xlim(1988, 2027); ax.set_ylim(0, 46)
ax.set_xticks([1990, 2000, 2010, 2020]); ax.set_xticklabels(["1990", "2000", "2010", "2020"])
ax.set_yticks([0, 10, 20, 30, 40]); ax.set_yticklabels(["0", "1万", "2万", "3万", "4万"])
ax.grid(axis="y", color="#ECEDEF", lw=0.8); ax.set_axisbelow(True)
fig.text(0.02, 0.97, "日経平均(おおまかな推移・円)", fontsize=11, color=MUTE, va="top")
put(c, to_img(fig), 310, 150, 500, 310)
box(c, 310, 70, 492, 70, PALE_G, GREEN, 10)
txt(c, 328, 108, "だから、1社・1つの国に偏らず、まとめて持つ。", 15.5, GREEN)
txt(c, 328, 84, "世界中に分けるのが「インデックス投資」(次のページ)。", 12, INK)
footer(c, 8, f"{src_title(13)}、{src_title(14)}",
       assume="前提: 日経平均の年末値の一部は概数で、グラフはおおまかな推移。1989年12月29日の終値と2024年2月22日の終値を比較。将来を保証しません。")
c.showPage()

# =====================================================================
# P9 インデックス投資とは
# =====================================================================
bg(c); header(c, 9, "インデックス投資 = 市場を、まるごと持つ",
              "弱った会社は外れ、伸びた会社が入る。自動で新陳代謝。", GREEN)
IC = DS["index_composition"]
# 左 500社
gx0, gy0 = M + 8, 190
box(c, M, 150, 250, 300, "#FFFFFF", GREEN, 12)
txt(c, M + 16, 424, "S&P500 = 米国の大会社 約500社", 12.5, GREEN)
rng = np.random.RandomState(3)
cells = [(i % 25, i // 25) for i in range(500)]
out_idx = set(rng.choice(500, 8, replace=False).tolist())
for i, (cx_, cy_) in enumerate(cells):
    x_ = M + 16 + cx_ * 9; y_ = 200 + (19 - cy_) * 9 + 20
    col = RED if i in out_idx else GREEN_L
    c.setFillColor(HexColor(col)); c.circle(x_ + 3, y_ + 3, 3.1, stroke=0, fill=1)
txt(c, M + 16, 198 - 6, "●1つ=1社", 9.5, MUTE)
txt(c, M + 16, 170, "赤=外れる会社の例 / これを丸ごと持つ", 10, MUTE)
# 右 2500社
rx0 = 330
box(c, rx0, 150, 250, 300, "#FFFFFF", BLUE, 12)
txt(c, rx0 + 16, 424, "MSCI ACWI = 世界の大会社 約2,500社", 12.5, BLUE)
out2 = set(rng.choice(2500, 40, replace=False).tolist())
for i in range(2500):
    x_ = rx0 + 18 + (i % 50) * 4.4; y_ = 222 + (49 - i // 50) * 3.9
    col = RED if i in out2 else BLUE_L
    c.setFillColor(HexColor(col)); c.circle(x_, y_, 1.25, stroke=0, fill=1)
txt(c, rx0 + 16, 192, "●1つ≒1社(米国・日本・欧州・新興国など)", 9.5, MUTE)
txt(c, rx0 + 16, 170, "先進国+新興国の大会社をまとめて持つ", 10, MUTE)
# 右端: 新陳代謝
nx0 = 610
box(c, nx0, 150, 192, 300, PALE_G, None, 12)
ctext(c, nx0 + 96, 424, "定期的な入れ替え", 14, GREEN)
box(c, nx0 + 16, 340, 160, 60, "#FFFFFF", RED, 8, 1.2)
ctext(c, nx0 + 96, 376, "衰えた会社", 12, RED)
ctext(c, nx0 + 96, 356, "指数から外れる", 11, INK)
arrow(c, nx0 + 96, 336, nx0 + 96, 308, MUTE)
ctext(c, nx0 + 96, 292, "→ 自動で入れ替え", 11, MUTE)
box(c, nx0 + 16, 214, 160, 60, "#FFFFFF", GREEN, 8, 1.2)
ctext(c, nx0 + 96, 250, "成長した会社", 12, GREEN)
ctext(c, nx0 + 96, 230, "新しく入ってくる", 11, INK)
para(c, nx0 + 16, 190, "自分で選ばなくても、新陳代謝される。", 10.5, 165, INK, 1.4)
box(c, M, 70, W - 2*M, 62, PALE_N, None, 10)
txt(c, M + 20, 106, "インデックス", 12.5, GREEN)
txt(c, M + 90, 106, "=株価の動きを測る「ものさし」。インデックスファンドは、そのものさしの全部に連動するよう運用する投資信託。", 11.5, INK)
txt(c, M + 20, 84, "少額から、たくさんの会社に一度に分散できる。ただし、市場全体が下がる時は一緒に下がります。", 11.5, INK)
footer(c, 9, f"{src_title(12)}、{src_title(8)}",
       assume="前提: 構成社数は時期により変動(MSCI ACWIは約2,460〜2,515社と公表)。図の点の位置に意味はありません。赤い点は入れ替わる会社のイメージ。")
c.showPage()

# =====================================================================
# P10 3%・5%・7%の根拠
# =====================================================================
bg(c); header(c, 10, "年3%・5%・7%は、どこから来た数字?",
              "過去の実績より、かなり控えめに置いた仮定。", GREEN)
fig = new_fig(470, 330)
ax = fig.add_axes([0.02, 0.14, 0.96, 0.66]); clean(ax, labelsize=12)
labs = ["1926年〜", "1950年〜", "1980年〜", "2000年〜"]; keys = ["1926-", "1950-", "1980-", "2000-"]
nom = [SPN["tr_nominal_cagr_pct"][k] for k in keys]; rea = [SPN["tr_real_cagr_pct"][k] for k in keys]
bw = 0.38
ax.bar(np.arange(4) - bw/2 - 0.01, nom, bw, color=BLUE_L, edgecolor=BLUE, lw=1)
ax.bar(np.arange(4) + bw/2 + 0.01, rea, bw, color=BLUE)
for i in range(4):
    ax.text(i - bw/2 - 0.01, nom[i] + 0.3, f"{nom[i]:.1f}", ha="center", fontsize=12.5, color=BLUE)
    ax.text(i + bw/2 + 0.01, rea[i] + 0.3, f"{rea[i]:.1f}", ha="center", fontsize=12.5, color=BLUE)
for lv, col, lbl in ((7, BLUE, ""), (5, TEAL, ""), (3, GREEN, "")):
    ax.axhline(lv, color=col, lw=1, ls=(0, (3, 3)), alpha=0.8)
ax.text(3.62, 7.2, "7%", color=BLUE, fontsize=12, ha="left", va="bottom")
ax.text(3.62, 5.2, "5%", color=TEAL, fontsize=12, ha="left", va="bottom")
ax.text(3.62, 3.2, "3%", color=GREEN, fontsize=12, ha="left", va="bottom")
ax.set_xticks(range(4)); ax.set_xticklabels(labs, fontsize=12)
ax.set_yticks([]); ax.set_ylim(0, 14); ax.set_xlim(-0.55, 3.85)
fig.text(0.02, 0.97, "米国株(S&P500・配当込み)の年率(%)", fontsize=12, color=INK, va="top")
fig.text(0.02, 0.89, "■ 名目(額面)", fontsize=10.5, color=BLUE, va="top")
fig.text(0.22, 0.89, "■ 実質(物価を引いた価値)", fontsize=10.5, color=BLUE, va="top")
fig.text(0.60, 0.89, "…… 本資料の想定(7・5・3%)", fontsize=10.5, color=MUTE, va="top")
put(c, to_img(fig), M, 135, 470, 330)
# 右
rx = 535; rw = 267
box(c, rx, 330, rw, 135, "#FFFFFF", BLUE, 12)
txt(c, rx + 16, 440, "過去の実績は、区間でぶれる", 13.5, BLUE)
para(c, rx + 16, 416, f"1926年〜は名目約{nom[0]:.0f}%・実質約{rea[0]:.0f}%。でも2000年〜は名目約{nom[3]:.1f}%・実質約{rea[3]:.1f}%と低め。始める時期で結果は大きく変わる。", 11.5, rw - 32, INK, 1.5)
box(c, rx, 225, rw, 90, PALE_G, GREEN, 12)
txt(c, rx + 16, 292, "7%・5%・3%の位置づけ", 13, GREEN)
para(c, rx + 16, 272, "7%は過去の「実質」に近い水準。5%と3%は、そこから大きく割り引いた慎重な仮定です。", 11.5, rw - 32, INK, 1.5)
box(c, rx, 90, rw, 120, PALE_R, RED, 12)
txt(c, rx + 16, 186, "名目と実質のちがい", 13, RED)
txt(c, rx + 16, 154, "年3% − 物価2% ≒ 実質1%", 17, RED)
para(c, rx + 16, 130, "額面が増えても、物価が上がると買えるモノの増え方は小さい。将来の保証ではありません。", 11, rw - 32, INK, 1.45)
box(c, M, 70, 470, 48, PALE_N, None, 8)
para(c, M + 14, 102, "年率=1年あたり平均で何%増えたか。1926年〜は米国の長期実績と外部の公表値(約10.3%、実質7.0%)とも整合。", 10.5, 442, MUTE, 1.4)
footer(c, 10, f"{src_title(8)}(独自計算)、{src_title(10)}、{src_title(11)}",
       assume="前提: 2023年6月まで。1950年〜・1980年〜・2000年〜は独自計算。将来の年率は上下し、元本割れもありえます。米国株の結果で世界全体の保証ではありません。")
c.showPage()


p = D["pages"][1]
bg(c); header(c, 11, p["title"], p["catch"], RED)
fig = new_fig(520, 390)
ax = fig.add_axes([0.02, 0.1, 0.80, 0.84]); clean(ax)
yy = np.arange(0, 31)
real = 1e6 / (1 + INFL) ** yy / 1e4
ax.fill_between(yy, 100, real, step="post", color=RED_L, alpha=0.8, lw=0)
ax.fill_between(yy, 0, real, step="post", color="#E7E9EC", lw=0)
ax.step(yy, real, where="post", color=RED, lw=2.4)
ax.axhline(100, color=GRAY, ls=(0, (1.5, 3)), lw=1.8)
ax.text(0.2, 102.5, "額面は100万円のまま", color=GRAY, fontsize=11)
for y_ in (10, 20, 30):
    v = PM[y_]["real_value"] / 1e4
    ax.plot([y_], [v], "o", color=RED, ms=9, zorder=5)
    ax.text(y_, v - 9, f"{round(v)}万円分", color=RED, fontsize=15, ha="center", va="top")
    ax.text(y_, 3, f"{y_}年後", color=MUTE, fontsize=11, ha="center")
ax.annotate("", xy=(20.3, 67), xytext=(20.3, 100), arrowprops=dict(arrowstyle="<->", color=RED, lw=1.4))
ax.text(20.8, 84, "目減り\n約33万円分", color=RED, fontsize=11, va="center")
ax.set_ylim(0, 110); ax.set_xlim(0, 31.5); ax.set_yticks([]); ax.set_xticks([])
ax.spines["bottom"].set_visible(True)
put(c, to_img(fig), M, 70, 520, 390)
hero(c, 590, 440, "20年後の100万円", f"約{round(PM[20]['real_value']/1e4)}万円分", [
    f"インフレ年2%だと、10年後 約{round(PM[10]['real_value']/1e4)}万円分、30年後 約{round(PM[30]['real_value']/1e4)}万円分まで価値が下がる。",
    f"預金金利0.1%でも、100万円は20年で{yen(DEP[20]['nominal'])}。数字は増えても、実質は約{int(DEP[20]['real']//1e4)}万円分。",
], RED, size=40)
y = 210
c.setFillColor(HexColor("#EEF7F2")); c.roundRect(590, 120, 212, 92, 8, stroke=0, fill=1)
para(c, 602, 194, "「減らさない」ためにも、お金に働いてもらう選択肢が要る。(インフレ2%は想定であり、保証ではありません)", 10.5, 190, GREEN)
footer(c, 11, "本資料の試算(インフレ年2%、預金金利0.1%の想定)")
c.showPage()

p = D["pages"][2]
bg(c); header(c, 12, p["title"], p["catch"], GREEN)
fig = new_fig(560, 400)
ax = fig.add_axes([0.07, 0.08, 0.68, 0.86]); clean(ax)
x = np.arange(31)
g = lambda k: np.array(S[k]) / 1e4
ax.fill_between(x, g("invest_3pct"), g("invest_7pct"), color=GREEN_L, alpha=0.55, lw=0)
ax.plot(x, g("invest_7pct"), color=BLUE, lw=1.6)
ax.plot(x, g("invest_3pct"), color=GREEN, lw=1.6)
ax.plot(x, g("invest_5pct"), color=TEAL, lw=3.2)
ax.plot(x, g("principal"), color=GRAY, lw=2.2, ls=(0, (1.5, 2.5)))
ax.plot(x, g("cash_real"), color=RED, lw=2.4)
def lab(yv, s, col, size=12):
    ax.text(30.6, yv, s, color=col, fontsize=size, va="center", clip_on=False)
lab(g("invest_7pct")[-1], f"年7%  {man(S['invest_7pct'][-1], False)}", BLUE)
lab(g("invest_5pct")[-1], f"年5%  {man(S['invest_5pct'][-1], False)}", TEAL, 14)
lab(g("invest_3pct")[-1], f"年3%  {man(S['invest_3pct'][-1], False)}", GREEN)
lab(g("principal")[-1], f"元本  {man(S['principal'][-1], False)}", GRAY)
lab(g("cash_real")[-1], f"預金(実質)  {man_f(S['cash_real'][-1])[1:]}", RED)
ax.set_xlim(0, 30); ax.set_ylim(0, 1250)
ax.set_xticks([0, 10, 20, 30]); ax.set_xticklabels(["0", "10年", "20年", "30年"])
ax.set_yticks([0, 400, 800, 1200]); ax.set_yticklabels(["0", "400万", "800万", "1,200万"])
ax.grid(axis="y", color="#ECEDEF", lw=0.8); ax.set_axisbelow(True)
put(c, to_img(fig), M - 10, 70, 560, 400)
hero(c, 600, 440, "月1万円 × 30年", f"{round(S['principal'][-1]/1e4)}万円→{round(S['invest_5pct'][-1]/1e4)}万円", [
    "元本360万円が、年5%なら約815万円に。増えた約455万円は、お金が生んだお金。",
    f"預金だと実質は{man_f(S['cash_real'][-1])}分。元本より減ってしまう。",
    "帯は年3〜7%の幅。保守的な仮定で、将来は保証されません。",
], GREEN, w=205, size=34)
footer(c, 12, "本資料の試算(月1万円積立)。過去の米国株の長期年率は区間により名目約6〜11%台・実質約4〜8%台だが、将来の保証はない")
c.showPage()

p = D["pages"][3]
bg(c); header(c, 13, p["title"], p["catch"], GREEN)
fig = new_fig(762, 285)
amts = [(1000, GREEN_L, "#5BBE93"), (10000, GREEN, GREEN), (30000, BLUE, BLUE)]
for i, (m, col, colstrong) in enumerate(amts):
    ax = fig.add_axes([0.035 + i*0.325, 0.10, 0.29, 0.68]); clean(ax)
    ys = [10, 20, 30]
    tot = [T[(m, y_)]["invest_5pct"]/1e4 for y_ in ys]
    pri = [T[(m, y_)]["principal"]/1e4 for y_ in ys]
    ax.bar(range(3), tot, width=0.62, color=colstrong)
    ax.bar(range(3), pri, width=0.62, color="#C9CDD2", edgecolor=GRAY, lw=1.0, ls=(0, (2, 2)))
    top = max(tot)
    for k in range(3):
        ax.text(k, tot[k] + top*0.03, f"{round(tot[k]):,}万", ha="center", fontsize=14 if k == 2 else 12, color=colstrong if m != 1000 else "#2E9B6E")
        ax.text(k, pri[k]/2, f"元本\n{round(pri[k]):,}万", ha="center", va="center", fontsize=8.5, color="#4B5563")
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{y_}年" for y_ in ys], fontsize=11)
    ax.set_yticks([]); ax.set_ylim(0, top*1.18)
    lbl = f"月{m:,}円"
    fig.text(0.035 + i*0.325 + 0.0, 0.93, lbl, fontsize=16, color=colstrong if m != 1000 else "#2E9B6E", va="center")
    fig.text(0.035 + i*0.325 + 0.29, 0.93, f"30年で {man(T[(m,30)]['invest_5pct'], False)}", fontsize=12, color=INK, va="center", ha="right")
put(c, to_img(fig), M, 160, 762, 285)
c.setFillColor(HexColor("#EEF7F2")); c.roundRect(M, 62, W - 2*M, 84, 10, stroke=0, fill=1)
t = T[(10000, 20)]
txt(c, M + 22, 112, "月1万円 × 20年", 14, MUTE)
s1 = f"元本{round(t['principal']/1e4)}万円が"
txt(c, M + 22, 82, s1, 16, GRAY)
xb = M + 22 + pdfmetrics.stringWidth(s1, F, 16) + 8
txt(c, xb, 82, f"{man(t['invest_5pct'])}", 40, GREEN)
txt(c, xb + pdfmetrics.stringWidth(man(t['invest_5pct']), F, 40) + 4, 82, "に", 16, GRAY)
para(c, M + 400, 118, "月1,000円でも20年で元本24万円が約41万円。金額が小さくても、続けるほど差がひらく。", 11.5, 340, INK)
txt(c, W - M - 12, 70, "※年5%の仮定 / 灰色の点線枠は元本", 8.5, MUTE, "r")
footer(c, 13, "本資料の試算(年5%・月末積立)")
c.showPage()

p = D["pages"][4]
bg(c); header(c, 14, p["title"], p["catch"], BLUE)
a25, a35 = AGE[25], AGE[35]
fig = new_fig(520, 390)
ax = fig.add_axes([0.02, 0.12, 0.96, 0.78]); clean(ax)
keys = [("principal", "元本"), ("invest_3pct", "年3%"), ("invest_5pct", "年5%"), ("invest_7pct", "年7%")]
bw = 0.36
for i, (k, name) in enumerate(keys):
    v25, v35 = a25[k]/1e4, a35[k]/1e4
    if k == "principal":
        c25, c35, e = "#B7BCC3", "#D5D8DC", GRAY
    else:
        c25, c35, e = BLUE, BLUE_L, BLUE
    big = (k == "invest_5pct")
    ax.bar(i - bw/2 - 0.01, v25, bw, color=c25)
    ax.bar(i + bw/2 + 0.01, v35, bw, color=c35)
    fs = 15 if big else 10.5
    ax.text(i - bw/2 - 0.01, v25 + 40, f"{round(v25):,}", ha="center", fontsize=fs, color=(BLUE if k != "principal" else GRAY))
    ax.text(i + bw/2 + 0.01, v35 + 40, f"{round(v35):,}", ha="center", fontsize=fs, color=(BLUE if k != "principal" else GRAY))
    ax.text(i, -150, name, ha="center", fontsize=13, color=INK)
ax.text(2.0 - bw/2 - 0.01, 60, "25歳\nスタート", ha="center", va="bottom", fontsize=9, color="white")
ax.text(2.0 + bw/2 + 0.01, 60, "35歳\nスタート", ha="center", va="bottom", fontsize=9, color=BLUE)
ax.text(-0.5, 2750, "65歳時点の資産(万円・月1万円)", fontsize=11, color=MUTE)
ax.set_ylim(-60, 2800); ax.set_xlim(-0.55, 3.55); ax.set_yticks([]); ax.set_xticks([])
put(c, to_img(fig), M, 70, 520, 390)
diff = a25["invest_5pct"] - a35["invest_5pct"]
hero(c, 590, 440, "年5%での差(65歳時点)", f"約{round(diff/1e4)}万円", [
    f"25歳スタート {man(a25['invest_5pct'], False)}、35歳スタート {man(a35['invest_5pct'], False)}。",
    f"元本の差は{round(D['age_diff']['principal_diff']/1e4)}万円だけなのに、結果の差は約{round(diff/1e4)}万円。",
], BLUE, size=44)
c.setFillColor(HexColor("#EEF3FC")); c.roundRect(590, 112, 212, 112, 8, stroke=0, fill=1)
txt(c, 604, 202, "35歳から追いつくには", 11, MUTE)
txt(c, 604, 170, f"月{D['age_catch_up']['monthly_needed_at_35']:,}円", 28, BLUE)
txt(c, 604, 140, f"(約{D['age_catch_up']['ratio']}倍の積立)", 13, INK)
footer(c, 14, "本資料の試算(月1万円を65歳まで:25歳開始=40年、35歳開始=30年)")
c.showPage()

p = D["pages"][6]
bg(c); header(c, 15, p["title"], p["catch"], GREEN)
# hero strip
c.setFillColor(HexColor("#EEF7F2")); c.roundRect(M, 345, W - 2*M, 62, 10, stroke=0, fill=1)
txt(c, M + 20, 366, f"月1万円×20年・年5%の利益 約{int(TAX['gain']//1e4)}万円に", 13, MUTE)
st = f"税金 {man_f(TAX['tax_normal'])}"
txt(c, M + 330, 366, st, 30, RED)
xa = M + 330 + pdfmetrics.stringWidth(st, F, 30) + 16
c.setStrokeColor(HexColor(MUTE)); c.setLineWidth(2.5); c.line(xa, 376, xa + 30, 376); c.line(xa + 22, 382, xa + 30, 376); c.line(xa + 22, 370, xa + 30, 376)
txt(c, xa + 42, 366, "0円", 38, GREEN)
txt(c, xa + 42 + pdfmetrics.stringWidth("0円", F, 38) + 6, 366, "(NISA)", 13, MUTE)
# 左: 積み上げ
fig = new_fig(330, 275)
ax = fig.add_axes([0.04, 0.12, 0.92, 0.76]); clean(ax)
pri = TAX["principal"]/1e4; gain_after = (TAX["gain"] - TAX["tax_normal"])/1e4; tax = TAX["tax_normal"]/1e4
tax_l = int(TAX["tax_normal"]//1e4); gain_l = int(TAX["gain"]//1e4)
bw = 0.55
ax.bar(0, pri, bw, color="#C9CDD2", edgecolor=GRAY, lw=1, ls=(0, (2, 2)))
ax.bar(0, gain_after, bw, bottom=pri, color=GREEN)
ax.bar(0, tax, bw, bottom=pri + gain_after, color=RED)
ax.bar(1, pri, bw, color="#C9CDD2", edgecolor=GRAY, lw=1, ls=(0, (2, 2)))
ax.bar(1, TAX["gain"]/1e4, bw, bottom=pri, color=GREEN)
ax.text(0, pri/2, f"元本\n{round(pri)}万", ha="center", va="center", color="#4B5563", fontsize=10)
ax.text(1, pri/2, f"元本\n{round(pri)}万", ha="center", va="center", color="#4B5563", fontsize=10)
ax.text(0, pri + gain_after/2, f"利益\n{round(gain_after)}万", ha="center", va="center", color="white", fontsize=11)
ax.text(1, pri + TAX["gain"]/2e4, f"利益\n{gain_l}万", ha="center", va="center", color="white", fontsize=11)
ax.text(0, pri + gain_after + tax/2, f"税 {tax_l}万", ha="center", va="center", color="white", fontsize=9.5)
ax.text(0, pri + gain_after + tax + 12, f"手取り {round(TAX['after_tax_normal']/1e4)}万", ha="center", fontsize=0.1)
ax.text(0, (pri + gain_after + tax) * 1.0 + 25, f"手取り\n約{round(TAX['after_tax_normal']/1e4)}万円", ha="center", va="bottom", color=INK, fontsize=12)
ax.text(1, TAX["nisa"]/1e4 + 25, f"手取り\n約{round(TAX['nisa']/1e4)}万円", ha="center", va="bottom", color=GREEN, fontsize=13)
ax.set_xticks([0, 1]); ax.set_xticklabels(["通常口座\n(税20.315%)", "NISA\n(非課税)"], fontsize=11)
ax.set_ylim(0, 560); ax.set_yticks([]); ax.set_xlim(-0.5, 1.5)
put(c, to_img(fig), M, 62, 330, 275)
# 右: 枠の図解
fig = new_fig(420, 275)
ax = fig.add_axes([0, 0, 1, 1]); ax.patch.set_alpha(0); ax.axis("off")
ax.set_xlim(0, 420); ax.set_ylim(0, 275)
ax.text(8, 258, "新NISAの「枠」", fontsize=13, color=MUTE, va="center")
# 年間枠
tz, gz = NISA["tsumitate_year"]/1e4, NISA["growth_year"]/1e4
tot_y = NISA["year_total"]/1e4
scale = 400 / tot_y
ax.add_patch(Rectangle((8, 190), tz*scale, 40, color=GREEN))
ax.add_patch(Rectangle((8 + tz*scale, 190), gz*scale, 40, color=BLUE))
ax.text(8 + tz*scale/2, 210, f"つみたて\n{int(tz)}万", color="white", fontsize=11, ha="center", va="center")
ax.text(8 + tz*scale + gz*scale/2, 210, f"成長投資枠 {int(gz)}万円", color="white", fontsize=12, ha="center", va="center")
ax.text(8, 238 + 0, "", fontsize=1)
ax.text(8, 176, f"年間で最大 {int(tot_y):,}万円(併用OK)", fontsize=12, color=INK, va="center")
# 生涯枠
life = NISA["lifetime"]/1e4; gl = NISA["growth_lifetime_sub_limit"]/1e4
ax.add_patch(FancyBboxPatch((8, 70), 400, 70, boxstyle="round,pad=0,rounding_size=6", fc=GREEN_L, ec=GREEN, lw=1.5))
ax.add_patch(FancyBboxPatch((8, 70), 400*gl/life, 70, boxstyle="round,pad=0,rounding_size=6", fc=BLUE_L, ec=BLUE, lw=1.5))
ax.text(8 + 200*gl/life, 105, f"うち成長投資枠は\n{int(gl):,}万円まで", fontsize=11, color=BLUE, ha="center", va="center")
ax.text(8 + 400*gl/life + (400 - 400*gl/life)/2, 105, "つみたて\n投資枠", fontsize=11, color="#127A4E", ha="center", va="center")
ax.text(8, 50, f"生涯の上限 {int(life):,}万円", fontsize=15, color=INK, va="center")
ax.text(412, 50, "非課税期間は無期限", fontsize=12, color=GREEN, va="center", ha="right")
ax.text(8, 22, f"つみたて投資枠は月{NISA['tsumitate_monthly_max']//10000}万円まで。月3万円なら生涯枠を埋めるのに約{int(NISA['years_to_fill_at_30000_monthly'])}年。", fontsize=9.5, color=MUTE, va="center")
put(c, to_img(fig), 410, 62, 392, 257)
footer(c, 15, f"本資料の試算(通常口座の譲渡益課税{TAX['tax_rate']*100:.3f}%で単純計算)。月3万円×30年・年5%の利益約{round(TAX2['gain']/1e4):,}万円なら税約{round(TAX2['tax_normal']/1e4)}万円。制度は変更される可能性があります")
c.showPage()

p = D["pages"][7]
bg(c); header(c, 16, p["title"], p["catch"], GREEN)
steps = [
    ("1", "口座をひらく", "証券口座を開設して、NISA口座を申し込む。", GREEN),
    ("2", "ファンドを選ぶ", "つみたて投資枠で、全世界株式かS&P500のインデックスファンドを選ぶ。", TEAL),
    ("3", "自動で積み立てる", "月1,000円〜で自動積立を設定。あとは続けるだけ。", BLUE),
]
cw, gap = 236, 28
x0 = M
for i, (n, t_, d_, col) in enumerate(steps):
    x = x0 + i*(cw + gap)
    top = 425 - i*26           # 階段状
    c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(HexColor(col)); c.setLineWidth(1.6)
    c.roundRect(x, top - 165, cw, 165, 12, stroke=1, fill=1)
    c.setFillColor(HexColor(col)); c.circle(x + 40, top - 42, 26, stroke=0, fill=1)
    txt(c, x + 40, top - 53, n, 32, "#FFFFFF", "c")
    txt(c, x + 78, top - 48, t_, 17, col)
    para(c, x + 22, top - 100, d_, 12.5, cw - 44, INK)
    if i < 2:
        xm = x + cw + gap/2; c.setStrokeColor(HexColor(MUTE)); c.setLineWidth(2.5)
        c.line(xm - 6, top - 60, xm + 6, top - 72); c.line(xm + 6, top - 72, xm - 6, top - 84)
c.setFillColor(HexColor("#EEF7F2")); c.roundRect(M, 120, W - 2*M, 56, 10, stroke=0, fill=1)
para(c, M + 20, 156, "先に、生活防衛資金(目安:生活費3〜6か月分)を確保。余裕資金で、無理のない金額から。長く続けることがいちばんの武器。", 12.5, W - 2*M - 40, INK)
# 免責
c.setFillColor(HexColor("#F1F2F4")); c.roundRect(M, 56, W - 2*M, 50, 6, stroke=0, fill=1)
disc = "※本資料は情報提供を目的としたもので、特定商品の推奨や将来の運用成果の保証ではありません。投資は元本割れの可能性があります。最終判断はご自身で。数値は年率3/5/7%・インフレ2%等の仮定に基づく試算で、税・手数料・信託報酬は考慮していません。"
yy_ = 96
for ln in wrap(disc, 8, W - 2*M - 24):
    txt(c, M + 12, yy_, ln, 8, MUTE); yy_ -= 11
txt(c, W - M, 30, "16 / 16", 9, MUTE, "r")
txt(c, M, 30, "出典: 本資料の試算(年3/5/7%・インフレ2%の仮定)。制度は2024年開始の新NISA。最新情報は金融庁等でご確認ください。", 7, MUTE)
c.showPage()

c.save()
print("saved", OUT)
