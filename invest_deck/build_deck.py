#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""20代向け『なぜ今NISAで積立投資か』8ページPDF生成。数値は content.json から読み込む。"""
import json, os, io
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
OUT = os.path.join(HERE, "investment_deck.pdf")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
D = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))

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

def clean(ax, left=False, bottom=True):
    ax.patch.set_alpha(0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    ax.spines["bottom"].set_color(LIGHT)
    ax.spines["left"].set_color(LIGHT)
    ax.tick_params(colors=MUTE, length=0, labelsize=10)

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

ASSUME = ("前提: 年率3/5/7%は仮定で将来を保証しません。インフレ年2%、預金金利0.1%、月末積立・月次複利、"
          "手数料・信託報酬・税は除く(NISA前提)。")
def footer(c, n, src, dark=False):
    col = "#9FB3C4" if dark else MUTE
    y = 30
    for ln in wrap("出典: " + src + "  " + ASSUME, 7, W - 2*M - 50):
        txt(c, M, y, ln, 7, col); y -= 10
    txt(c, W - M, 30, f"{n} / 8", 9, col, "r")

def header(c, n, title, catch, color=GREEN):
    c.setFillColor(HexColor(color)); c.rect(M, H - 52, 28, 4, stroke=0, fill=1)
    txt(c, M, H - 74, title, 22, INK)
    fit(c, M, H - 112, catch, W - 2*M, 30, color)

def hero(c, x, ytop, label, big, sub, color, w=212, size=46):
    txt(c, x, ytop, label, 11, MUTE)
    fit(c, x, ytop - 52, big, w, size, color)
    y = ytop - 78
    for s in sub:
        y = para(c, x, y, s, 11, w, INK, 1.5) - 4

# ---------- data ----------
S = D["extra"]["series_10000_30y"]
T = {(t["monthly"], t["years"]): t for t in D["tables"]}
PM = {p["years"]: p for p in D["power_of_money"]}
DEP = {p["years"]: p for p in D["deposit_1m"]}
AGE = {a["start_age"]: a for a in D["age"]}
INFL = D["assumptions"]["inflation"]
TAX = D["tax"]; TAX2 = D["tax2"]; NISA = D["nisa"]; STRESS = D["stress"]
HIST = D["history_notes"]
SRC = "試算は本資料の想定に基づく自作計算"

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("20代のうちに知りたい、NISA積立のはじめ方")
c.setAuthor("")

# =====================================================================
# P1 表紙
# =====================================================================
p = D["pages"][0]
bg(c, NAVY)
fig = new_fig(420, 400)
ax = fig.add_axes([0.02, 0.05, 0.96, 0.9]); ax.patch.set_alpha(0)
ax.axis("off")
yrs = list(range(0, 31, 3))
vals = [S["invest_5pct"][y]/1e4 for y in yrs]
pr = [S["principal"][y]/1e4 for y in yrs]
cols = [plt.matplotlib.colors.to_hex(plt.matplotlib.colors.LinearSegmentedColormap.from_list("g", [GREEN_L, GREEN, BLUE])(i/(len(yrs)-1))) for i in range(len(yrs))]
ax.bar(range(len(yrs)), vals, width=0.78, color=cols)
ax.plot(range(len(yrs)), pr, color="#C9D3DC", ls=(0, (1.5, 2.5)), lw=2)
ax.text(len(yrs)-1.0, vals[-1] + 25, "年5%なら", ha="center", color="#C9D3DC", fontsize=12)
ax.text(len(yrs)-1.0, vals[-1] + 90, f"{man(vals[-1]*1e4, False)}", ha="right", color="white", fontsize=26)
ax.text(-0.5, pr[-1] + 40, "元本 " + man(pr[-1]*1e4, False) + "(点線)", ha="left", va="bottom", color="#C9D3DC", fontsize=11)
ax.set_ylim(0, 1100); ax.set_xlim(-0.6, len(yrs)-0.4)
put(c, to_img(fig), 410, 80, 400, 380)
txt(c, M + 4, H - 70, "20代のための はじめてのNISA", 13, GREEN_L)
y = H - 170
for ln in ["時間は、", "お金より先に", "減っていく。"]:
    txt(c, M + 4, y, ln, 38, "#FFFFFF"); y -= 54
txt(c, M + 4, y - 10, p["title"], 15, "#C9D3DC")
y -= 64
for b in p["bullets"]:
    c.setFillColor(HexColor(GREEN)); c.circle(M + 10, y + 4, 4, stroke=0, fill=1)
    txt(c, M + 24, y, b, 14, "#FFFFFF"); y -= 28
footer(c, 1, "本資料の試算(右図は月1万円・年5%の仮定)", dark=True)
c.showPage()

# =====================================================================
# P2 預金の実質価値
# =====================================================================
p = D["pages"][1]
bg(c); header(c, 2, p["title"], p["catch"], RED)
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
footer(c, 2, "本資料の試算(インフレ年2%、預金金利0.1%の想定)")
c.showPage()

# =====================================================================
# P3 複利
# =====================================================================
p = D["pages"][2]
bg(c); header(c, 3, p["title"], p["catch"], GREEN)
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
footer(c, 3, "本資料の試算(月1万円積立。過去のS&P500・全世界株式の長期年率は概ね7〜10%台とされるが保証なし)")
c.showPage()

# =====================================================================
# P4 積立額 x 期間
# =====================================================================
p = D["pages"][3]
bg(c); header(c, 4, p["title"], p["catch"], GREEN)
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
footer(c, 4, "本資料の試算(年5%・月末積立)")
c.showPage()

# =====================================================================
# P5 年齢差
# =====================================================================
p = D["pages"][4]
bg(c); header(c, 5, p["title"], p["catch"], BLUE)
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
footer(c, 5, "本資料の試算(月1万円を65歳まで:25歳開始=40年、35歳開始=30年)")
c.showPage()

# =====================================================================
# P6 リスク
# =====================================================================
p = D["pages"][5]
bg(c); header(c, 6, p["title"], p["catch"], RED)
fig = new_fig(490, 380)
ax = fig.add_axes([0.11, 0.08, 0.65, 0.86]); clean(ax)
x = np.arange(21)
lo, mid, hi = g("invest_3pct")[:21], g("invest_5pct")[:21], g("invest_7pct")[:21]
ax.fill_between(x, lo, hi, color=GREEN_L, alpha=0.6, lw=0)
ax.plot(x, hi, color=BLUE, lw=1.4); ax.plot(x, lo, color=GREEN, lw=1.4)
ax.plot(x, mid, color=TEAL, lw=2.8)
ax.plot(x, g("principal")[:21], color=GRAY, lw=2.2, ls=(0, (1.5, 2.5)))
# 40%下落ストレス
b19 = STRESS["before_crash_19y"]/1e4; a20 = STRESS["after_-40pct_crash_end20y"]/1e4
ax.plot([19, 20], [b19, a20], color=RED, lw=3)
ax.plot([20], [a20], "o", color=RED, ms=9, zorder=6)
ax.text(19.6, 70, f"20年目直前に-40%下落しても\n{man(STRESS['after_-40pct_crash_end20y'], False)}(5%シナリオの例)", color=RED, fontsize=10.5, ha="right", va="top")
ax.annotate("", xy=(20, a20 - 8), xytext=(17.5, 62), arrowprops=dict(arrowstyle="-", color=RED, lw=1))
for yv, s, col in ((hi[-1], f"年7%  {man(S['invest_7pct'][20], False)}", BLUE), (mid[-1], f"年5%  {man(S['invest_5pct'][20], False)}", TEAL),
                   (lo[-1], f"年3%  {man(S['invest_3pct'][20], False)}", GREEN), (g("principal")[20], f"元本  {man(S['principal'][20], False)}", GRAY)):
    pass
ax.text(20.5, hi[-1], f"年7%\n{man(S['invest_7pct'][20], False)}", color=BLUE, fontsize=11, va="center")
ax.text(20.5, mid[-1] + 8, f"年5%\n{man(S['invest_5pct'][20], False)}", color=TEAL, fontsize=11, va="center")
ax.text(20.5, lo[-1] - 20, f"年3%\n{man(S['invest_3pct'][20], False)}", color=GREEN, fontsize=11, va="center")
ax.text(20.5, g("principal")[20] - 75, f"元本\n{man(S['principal'][20], False)}", color=GRAY, fontsize=11, va="center")
ax.set_xlim(0, 20); ax.set_ylim(0, 560)
ax.set_xticks([0, 10, 20]); ax.set_xticklabels(["0", "10年", "20年"])
ax.set_yticks([0, 200, 400]); ax.set_yticklabels(["0", "200万", "400万"])
ax.grid(axis="y", color="#ECEDEF", lw=0.8); ax.set_axisbelow(True)
fig.text(0.11, 0.975, "月1万円×20年:3つのシナリオ幅", fontsize=11, color=MUTE, va="top")
put(c, to_img(fig), M - 5, 80, 490, 380)

# 右: 過去の下落
fig = new_fig(290, 150)
ax = fig.add_axes([0.30, 0.05, 0.62, 0.78]); clean(ax, bottom=False)
drops = [("ITバブル後", 49, "2000-02"), ("リーマン期", 57, "2007-09"), ("コロナ期", 34, "2020年")]
for i, (nm, v, yr) in enumerate(drops[::-1]):
    ax.barh(i, v, color=RED, height=0.55, alpha=0.9 if v != 34 else 0.6)
    ax.text(v + 1.5, i, f"-{v}%", color=RED, fontsize=13, va="center")
    ax.text(-2, i, nm, color=INK, fontsize=11, va="center", ha="right")
    ax.text(-2, i - 0.34, yr, color=MUTE, fontsize=8, va="center", ha="right")
ax.set_xlim(0, 75); ax.set_yticks([]); ax.set_xticks([])
fig.text(0.02, 0.97, "S&P500の過去の下落(高値→安値・約)", fontsize=10, color=MUTE, va="top")
put(c, to_img(fig), 540, 300, 290, 150)
y = 285
y = para(c, 544, y, "コロナ下落は数か月で戻った一方、リーマン後は高値の回復まで数年かかった。", 11, 255, INK) - 4
y = para(c, 544, y, "長期・分散で回復してきたが、将来の回復は保証されない。元本割れの可能性もある。", 11, 255, RED) - 4
y = para(c, 544, y, "だから、短期で使うお金は投資に回さない。", 11, 255, INK)
c.setFillColor(HexColor("#FBEDEC")); c.roundRect(540, 80, 262, 62, 8, stroke=0, fill=1)
para(c, 552, 126, f"年3〜7%の幅で、月1万円20年は{man(S['invest_3pct'][20], False)}〜{man(S['invest_7pct'][20], False)}。下回る可能性もあります。", 10.5, 240, RED)
footer(c, 6, "S&P500の過去の下落率は高値から安値までの概算(" + HIST["S&P500_dotcom"] + "、" + HIST["S&P500_lehman"] + "、2020年約-34%)。将来を保証しません")
c.showPage()

# =====================================================================
# P7 新NISA
# =====================================================================
p = D["pages"][6]
bg(c); header(c, 7, p["title"], p["catch"], GREEN)
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
footer(c, 7, f"本資料の試算(通常口座の譲渡益課税{TAX['tax_rate']*100:.3f}%で単純計算)。月3万円×30年・年5%の利益約{round(TAX2['gain']/1e4):,}万円なら税約{round(TAX2['tax_normal']/1e4)}万円。制度は変更される可能性があります")
c.showPage()

# =====================================================================
# P8 3ステップ
# =====================================================================
p = D["pages"][7]
bg(c); header(c, 8, p["title"], p["catch"], GREEN)
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
txt(c, W - M, 30, "8 / 8", 9, MUTE, "r")
txt(c, M, 30, "出典: 本資料の試算(年3/5/7%・インフレ2%の仮定)。制度は2024年開始の新NISA。最新情報は金融庁等でご確認ください。", 7, MUTE)
c.showPage()

c.save()
print("saved", OUT)
