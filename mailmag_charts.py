"""mailmag_charts.py ── 新天地メルマガ分析（チーム版）用のチャートと判定。

AI は画像を見ずに signals.json の数値だけで分析を書く（トークン節約）。
画像はメール本文にインライン添付するだけ（sha256 のファイル参照で渡すので、画像の中身はトークンにならない）。

使い方:
    python mailmag_charts.py render --spec WORK/chart_spec.json --out <repo>/WORK/mm_charts
        → jp_<code>.png（週足/日足＋判定の札）、us_<ticker>.png（米国株の日足＋日本株との連動）、
          signals.json（AI が読む数値）、manifest.json（ファイル・sha256）
    python mailmag_charts.py finalize --html WORK/draft.html --charts <repo>/WORK/mm_charts
        → 本文の {{chart:jp_8035}} を <img src="cid:attN"> に置き換えた draft_final.html、
          create_draft にそのまま渡せる attachments.json、画像を外した draft_noimg.html

chart_spec.json の形（読解担当が書く）:
    {"jp": [{"code": "8035", "name": "東京エレクトロン"}, ...],
     "us": [{"ticker": "NVDA", "name": "エヌビディア",
             "pairs": [{"code": "8035", "name": "東京エレクトロン"}]}, ...]}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

import briefing_charts as bc

BADGES = {"勝負": "#16A34A", "様子見": "#D4A017", "見送り": "#DC2626"}
PAIR_COLORS = ("#DC2626", "#16A34A")  # 日本株1・2（米国株は NAVY）
CORR_DAYS = 60


# ---------------------------------------------------------------- 日本株の判定

def jp_signals(d: pd.DataFrame) -> dict:
    """日足から「勝負時期か」の判定に使う数値と札を作る。"""
    c = d["Close"]
    last, prev = float(c.iloc[-1]), float(c.iloc[-2]) if len(c) > 1 else float(c.iloc[-1])
    ema5 = c.ewm(span=5, adjust=False).mean()
    ema25 = c.ewm(span=25, adjust=False).mean()
    w = bc.to_weekly(d)["Close"]
    ema13w = w.ewm(span=13, adjust=False).mean()
    vol = d["Volume"]
    vol20 = vol.iloc[-21:-1].mean() if len(vol) > 21 else vol.mean()
    high20 = d["High"].iloc[-21:-1].max() if len(d) > 21 else d["High"].max()
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = float(100 - 100 / (1 + gain.iloc[-1] / loss.iloc[-1])) if loss.iloc[-1] > 0 else 100.0

    s = {
        "close": round(last, 1),
        "change_pct": round((last / prev - 1) * 100, 2),
        "date": d.index[-1].strftime("%Y-%m-%d"),
        "dev25_pct": round(float(last / ema25.iloc[-1] - 1) * 100, 1),
        "vol_ratio": round(float(vol.iloc[-1] / vol20), 2) if vol20 else None,
        "to_high20_pct": round(float(last / high20 - 1) * 100, 1),
        "rsi14": round(rsi, 1),
        "weekly_up": bool(w.iloc[-1] > ema13w.iloc[-1] and ema13w.iloc[-1] > ema13w.iloc[-5])
        if len(w) > 5 else None,
        "daily_aligned": bool(last > ema5.iloc[-1] > ema25.iloc[-1]),
        "ema25_falling": bool(ema25.iloc[-1] < ema25.iloc[-6]) if len(ema25) > 6 else False,
    }
    score, tags = 0, []
    if s["weekly_up"]:
        score += 1; tags.append("週足上向き")
    if s["daily_aligned"]:
        score += 1; tags.append("日足 終値>EMA5>EMA25")
    if s["vol_ratio"] and s["vol_ratio"] >= 1.5 and s["change_pct"] > 0:
        score += 1; tags.append(f"出来高{s['vol_ratio']}倍で上昇")
    if s["to_high20_pct"] >= -3:
        score += 1; tags.append("20日高値圏" if s["to_high20_pct"] < 0 else "20日高値更新")
    if s["dev25_pct"] >= 15:
        score -= 1; tags.append(f"25日線から+{s['dev25_pct']}%（過熱）")
    if rsi >= 80:
        score -= 1; tags.append(f"RSI{s['rsi14']}（過熱）")
    if last < ema25.iloc[-1] and s["ema25_falling"]:
        score -= 2; tags.append("25日線の下で下向き")
        if s["change_pct"] >= 3 and last > ema5.iloc[-1] and (s["vol_ratio"] or 0) >= 1.0:
            score += 2; tags.append(f"反発初動（{s['change_pct']:+.1f}%でEMA5回復）")
    if rsi <= 30:
        tags.append(f"RSI{s['rsi14']}（売られ過ぎ）")
    s["score"] = score
    s["verdict"] = "勝負" if score >= 3 else "様子見" if score >= 0 else "見送り"
    s["tags"] = tags
    return s


# ---------------------------------------------------------------- 米国株と日本株の連動

def us_download(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, period="8mo", interval="1d", progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[bc.OHLCV].dropna()


def align_next_day(us_close: pd.Series, jp_close: pd.Series) -> pd.DataFrame:
    """日本株の各営業日に「その前日までに引けた直近の米国の終値」を対応させる。

    米国の t 日の引けは日本時間 t+1 日の早朝なので、日本の d 日には d より前の米国の日を当てる。
    戻り値の列: jp, us（それぞれ終値）
    """
    a = jp_close.rename("jp").to_frame().reset_index()
    b = us_close.rename("us").to_frame().reset_index()
    a.columns, b.columns = ["date", "jp"], ["date", "us"]
    a["date"], b["date"] = pd.to_datetime(a["date"]).dt.normalize(), pd.to_datetime(b["date"]).dt.normalize()
    m = pd.merge_asof(a.sort_values("date"), b.sort_values("date"), on="date",
                      allow_exact_matches=False, direction="backward")
    return m.dropna().set_index("date")


def pair_stats(aligned: pd.DataFrame, us_last_change_pct: float, days: int = CORR_DAYS) -> dict:
    """米国株の騰落率と、翌営業日の日本株の騰落率の関係（直近 days 日）。"""
    r = aligned.pct_change().dropna()
    r = r[r["us"] != 0].tail(days)  # 米国休場で同じ値が続いた日は除く
    if len(r) < 20:
        return {"n": len(r)}
    corr = float(r["us"].corr(r["jp"]))
    beta = float(r["us"].cov(r["jp"]) / r["us"].var())
    up = r[r["us"] > 0]
    dn = r[r["us"] < 0]
    return {
        "n": len(r),
        "corr": round(corr, 2),
        "beta": round(beta, 2),
        "jp_up_when_us_up_pct": round(float((up["jp"] > 0).mean() * 100), 0) if len(up) else None,
        "jp_down_when_us_down_pct": round(float((dn["jp"] < 0).mean() * 100), 0) if len(dn) else None,
        "implied_jp_pct": round(beta * us_last_change_pct, 2),
    }


def render_us(item: dict, us: pd.DataFrame, jps: dict[str, pd.DataFrame], out: Path) -> dict:
    t, name = item["ticker"], item.get("name", "")
    c = us["Close"]
    last, prev = float(c.iloc[-1]), float(c.iloc[-2])
    chg = (last / prev - 1) * 100
    sig = {"close": round(last, 2), "change_pct": round(chg, 2),
           "date": us.index[-1].strftime("%Y-%m-%d"), "pairs": []}

    fig = plt.figure(figsize=(12, 4.6), dpi=100)
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.05, wspace=0.14,
                          left=0.05, right=0.97, top=0.80, bottom=0.08)
    fig.suptitle(f"{t} {name}　終値 ${last:,.2f}（{chg:+.2f}%・{us.index[-1]:%m/%d}）",
                 x=0.05, ha="left", fontsize=12, fontweight="bold", color=bc.NAVY)
    bc.draw(fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0]), us.tail(80), (5, 25),
            "日足（約4か月）", "%m/%d", price_fmt="${:,.2f}")
    ax = fig.add_subplot(gs[:, 1])
    heading = f"米国株（前日）と日本株（翌営業日）の動き　直近{CORR_DAYS}日・始点=0%"
    lines = []
    for (p, col) in zip(item.get("pairs", [])[:2], PAIR_COLORS):
        jp = jps.get(p["code"])
        if jp is None or jp.empty:
            continue
        al = align_next_day(c, jp["Close"]).tail(CORR_DAYS + 1)
        st = pair_stats(align_next_day(c, jp["Close"]), chg)
        st.update(code=p["code"], name=p.get("name", ""))
        sig["pairs"].append(st)
        if len(lines) == 0:
            ax.plot(range(len(al)), (al["us"] / al["us"].iloc[0] - 1) * 100, color=bc.NAVY,
                    linewidth=1.6, label=f"{t}（1日ずらし）")
        ax.plot(range(len(al)), (al["jp"] / al["jp"].iloc[0] - 1) * 100, color=col, linewidth=1.3,
                label=f"{p['code']} {p.get('name', '')}")
        if "corr" in st:
            lines.append(f"{p['code']}: 相関{st['corr']:+.2f}・感応度{st['beta']:.2f}"
                         f"（米+1%→翌日{st['beta']:+.2f}%）")
        step = max(1, len(al) // 6)
        ax.set_xticks(list(range(len(al)))[::step])
        ax.set_xticklabels([x.strftime("%m/%d") for x in al.index[::step]], fontsize=7)
    ax.axhline(0, color=bc.MUTED, linewidth=0.6)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%")
    ax.grid(color=bc.GRID, linewidth=0.6)
    ax.tick_params(labelsize=7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    ax.set_title("\n".join([heading] + lines), fontsize=9, loc="left", color=bc.NAVY,
                 fontweight="bold", linespacing=1.4)
    fig.text(0.97, 0.01, "出典: Yahoo!ファイナンス（yfinance）", ha="right", fontsize=7, color=bc.MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png", facecolor="white")
    plt.close(fig)
    return sig


# ---------------------------------------------------------------- render / finalize

def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def render_all(spec: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    names = {j["code"]: j.get("name", "") for j in spec.get("jp", [])}
    for u in spec.get("us", []):
        for p in u.get("pairs", []):
            names.setdefault(p["code"], p.get("name", ""))
    chart_codes = [j["code"] for j in spec.get("jp", [])]
    codes = list(dict.fromkeys(chart_codes + list(names)))
    tickers = [u["ticker"] for u in spec.get("us", [])]

    def get_jp(code):
        try:
            return code, bc.fetch(code), None
        except Exception as e:
            return code, None, str(e)

    def get_us(t):
        try:
            return t, us_download(t), None
        except Exception as e:
            return t, None, str(e)

    with ThreadPoolExecutor(max_workers=8) as ex:  # 取得だけ並列。描画は matplotlib のため順に
        jp_data = list(ex.map(get_jp, codes))
        us_data = {t: (d, e) for t, d, e in ex.map(get_us, tickers)}

    signals = {"generated_at": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M JST"),
               "jp": {}, "us": {}}
    manifest: dict[str, dict] = {}
    jp_frames: dict[str, pd.DataFrame] = {}
    for code, data, err in jp_data:
        if data is None or data[0].empty:
            signals["jp"][code] = {"name": names.get(code, ""), "error": err or "データなし"}
            continue
        d, patched = data
        jp_frames[code] = d
        if code not in chart_codes:
            continue
        try:
            s = jp_signals(d)
            s["name"] = names.get(code, "")
            key = f"jp_{code}"
            p, last, _ = bc.render(code, s["name"], out / f"{key}.png",
                                   badge=(s["verdict"], BADGES[s["verdict"]]), data=(d, patched))
            signals["jp"][code] = s
            manifest[key] = {"file": p.name, "path": str(p.resolve()), "sha256": _sha(p), "last_bar": last}
            print(f"{p}  {s['verdict']}  {s['close']} ({s['change_pct']:+.2f}%)")
        except Exception as e:
            signals["jp"][code] = {"name": names.get(code, ""), "error": str(e)}
            print(f"SKIP {code}: {e}", file=sys.stderr)
    for u in spec.get("us", []):
        t = u["ticker"]
        d, err = us_data.get(t, (None, "未取得"))
        if d is None or len(d) < 30:
            signals["us"][t] = {"name": u.get("name", ""), "error": err or "データ不足"}
            continue
        try:
            key = f"us_{t}"
            p = out / f"{key}.png"
            s = render_us(u, d, jp_frames, p)
            s["name"] = u.get("name", "")
            signals["us"][t] = s
            manifest[key] = {"file": p.name, "path": str(p.resolve()), "sha256": _sha(p), "last_bar": s["date"]}
            print(f"{p}  {s['close']} ({s['change_pct']:+.2f}%)")
        except Exception as e:
            signals["us"][t] = {"name": u.get("name", ""), "error": str(e)}
            print(f"SKIP {t}: {e}", file=sys.stderr)
    (out / "signals.json").write_text(json.dumps(signals, ensure_ascii=False, separators=(",", ":")))
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    return signals


PLACEHOLDER = re.compile(r"\{\{chart:([A-Za-z0-9_.\-]+)\}\}")
IMG = ('<img src="cid:att{n}" alt="{key} チャート" width="100%" '
       'style="max-width:680px;height:auto;display:block;margin:6px 0;">')
MISSING = '<div style="font-size:12px;color:#5E6470;">（チャート取得不可）</div>'


MAX_ATTACHMENTS = 10  # Gmail の create_draft は添付10件まで（2026-11-28 の試し実行で確認）
STACKED = '<div style="font-size:12px;color:#5E6470;margin:4px 0;">（チャートは上の画像の{k}段目）</div>'


def plan_groups(keys: list[str], limit: int = MAX_ATTACHMENTS) -> list[list[str]]:
    """添付が limit 件に収まるよう、出現順に並んだ同じ種類（jp_/us_）の銘柄を数枚ずつ束ねる。"""
    segs: list[list[str]] = []
    for k in keys:
        if segs and segs[-1][0].split("_")[0] == k.split("_")[0]:
            segs[-1].append(k)
        else:
            segs.append([k])
    g = 1
    while sum(-(-len(s) // g) for s in segs) > limit and g < max(len(s) for s in segs):
        g += 1
    return [s[i:i + g] for s in segs for i in range(0, len(s), g)]


def stack_images(paths: list[Path], out: Path) -> Path:
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    canvas = Image.new("RGB", (max(i.width for i in ims), sum(i.height for i in ims)), "white")
    y = 0
    for im in ims:
        canvas.paste(im, (0, y))
        y += im.height
    canvas.save(out, optimize=True)
    return out


def finalize(html: str, manifest: dict, out_dir: Path | None = None,
             limit: int = MAX_ATTACHMENTS) -> tuple[str, list[dict], str]:
    """{{chart:key}} を本文の出現順に cid:attN へ置き換え、添付リストを作る。

    銘柄が limit を超えるときは、続けて並ぶ銘柄を数枚ずつ縦に重ねた1枚にまとめ、
    先頭の銘柄の位置に画像を置き、残りの銘柄には「上の画像のk段目」と書く。
    """
    keys = list(dict.fromkeys(k for k in PLACEHOLDER.findall(html) if k in manifest))
    atts: list[dict] = []
    where: dict[str, tuple[int, int, bool]] = {}  # key → (添付番号, 段, 画像を置く銘柄か)
    for gi, grp in enumerate(plan_groups(keys, limit)):
        if len(grp) == 1:
            f = manifest[grp[0]]
            path, name, sha = f["path"], f["file"], f["sha256"]
        else:
            out = Path(out_dir or Path(manifest[grp[0]]["path"]).parent) / f"group_{gi:02d}.png"
            stack_images([Path(manifest[k]["path"]) for k in grp], out)
            path, name, sha = str(out.resolve()), out.name, _sha(out)
        for n, k in enumerate(grp):
            where[k] = (len(atts), n + 1, n == 0)
        atts.append({"content": f"sha256:{sha}:{path}", "filename": name,
                     "mimeType": "image/png", "inline": True})

    def sub(m):
        key = m.group(1)
        if key not in where:
            return MISSING
        n, k, head = where[key]
        return IMG.format(n=n, key=key) if head else STACKED.format(k=k)

    final = PLACEHOLDER.sub(sub, html)
    noimg = PLACEHOLDER.sub("", html)
    return final, atts, noimg


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("render")
    r.add_argument("--spec", required=True)
    r.add_argument("--out", required=True)
    f = sp.add_parser("finalize")
    f.add_argument("--html", required=True)
    f.add_argument("--charts", required=True)
    a = ap.parse_args()
    if a.cmd == "render":
        bc.setup_font()
        render_all(json.loads(Path(a.spec).read_text()), Path(a.out))
    else:
        html_path = Path(a.html)
        mpath = Path(a.charts) / "manifest.json"
        manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
        final, atts, noimg = finalize(html_path.read_text(), manifest, Path(a.charts))
        html_path.with_name("draft_final.html").write_text(final)
        html_path.with_name("draft_noimg.html").write_text(noimg)
        html_path.with_name("attachments.json").write_text(json.dumps(atts, ensure_ascii=False, indent=1))
        print(f"attachments={len(atts)}  → {html_path.with_name('draft_final.html')}")


if __name__ == "__main__":
    main()
