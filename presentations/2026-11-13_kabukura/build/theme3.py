import json
import math
from datetime import date
from pathlib import Path

from kit import sheet, bar_chart, timeline, line_chart, _t
from annot import Chart, YEL, PINK, CYAN, WHITE, GREEN

C, A, R = "#7E1A2C", "#B8860B", "#C1121F"
HERE = Path(__file__).parent


def btc_cycle_chart(w=700, h=310):
    """BTCの2週足（対数軸）に半減期・天井・底・200週線を描く。"""
    data = json.loads((HERE / "btc_2w.json").read_text())
    ds = [date.fromisoformat(d) for d, _ in data]
    vs = [v for _, v in data]
    ma = [None] * len(vs)
    for i in range(99, len(vs)):  # 100本×2週＝200週
        ma[i] = sum(vs[i - 99:i + 1]) / 100
    d0, d1 = date(2014, 9, 1), date(2027, 6, 30)
    pl, pr, pt, pb = 42, 10, 12, 20
    lo, hi = math.log10(150), math.log10(200000)
    def x(d):
        return pl + (d - d0).days / (d1 - d0).days * (w - pl - pr)
    def y(v):
        return pt + (hi - math.log10(v)) / (hi - lo) * (h - pt - pb)
    o = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    # 底の予想ゾーン
    o.append(f'<rect x="{x(date(2026,10,1)):.1f}" y="{pt}" width="{x(date(2027,1,31))-x(date(2026,10,1)):.1f}" height="{h-pt-pb}" fill="{R}" opacity="0.10"/>')
    o.append(_t(x(date(2026, 12, 1)), h - pb - 4, "底の予想", 8, R, "middle", "700"))
    for v in (1000, 10000, 100000):
        o.append(f'<line x1="{pl}" x2="{w-pr}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#E3E6EC" stroke-width="0.8"/>')
        o.append(_t(pl - 4, y(v) + 3, f"${v:,}", 8, "#5A6170", "end"))
    for yr in range(2015, 2028):
        o.append(_t(x(date(yr, 1, 1)), h - 6, f"{yr}" if yr % 2 else f"'{str(yr)[2:]}", 7.6, "#5A6170", "middle"))
    for hd in (date(2016, 7, 9), date(2020, 5, 11), date(2024, 4, 20)):
        o.append(f'<line x1="{x(hd):.1f}" x2="{x(hd):.1f}" y1="{pt}" y2="{h-pb}" stroke="#B8860B" stroke-width="1" stroke-dasharray="3 3"/>')
        o.append(_t(x(hd) + 3, h - pb - 4, "半減期", 7.6, "#8A6D12", "start", "700"))
    pts = " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in zip(ds, ma) if v)
    o.append(f'<polyline points="{pts}" fill="none" stroke="#9AA5B1" stroke-width="1.4" stroke-dasharray="4 2"/>')
    pts = " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in zip(ds, vs))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{C}" stroke-width="1.6"/>')
    tops = [(date(2017, 12, 16), 19497, "天井"), (date(2021, 11, 8), 67567, "天井"), (date(2025, 10, 6), 124753, "天井 $124,753（2025/10）")]
    bots = [(date(2015, 1, 14), 178, "底 -87%"), (date(2018, 12, 15), 3237, "底 -83%"), (date(2022, 11, 21), 15787, "底 -77%")]
    for d, v, lab in tops:
        o.append(f'<circle cx="{x(d):.1f}" cy="{y(v):.1f}" r="3" fill="#13803B"/>')
        o.append(_t(x(d) - (6 if v > 100000 else 0), y(v) - 6, lab, 8, "#13803B", "end" if v > 100000 else "middle", "700"))
    for d, v, lab in bots:
        o.append(f'<circle cx="{x(d):.1f}" cy="{y(v):.1f}" r="3" fill="{R}"/>')
        o.append(_t(x(d), y(v) + 13, lab, 8, R, "middle", "700"))
    # 今ここ
    o.append(f'<circle cx="{x(date(2026,11,10)):.1f}" cy="{y(71276):.1f}" r="4.5" fill="{A}" stroke="#fff" stroke-width="1.5"/>')
    o.append(_t(x(date(2026, 11, 10)) - 12, y(71276) + 40, "今ここ $71,276", 9, "#8A6D12", "end", "700"))
    o.append(_t(x(date(2026, 11, 10)) - 12, y(71276) + 51, "（天井から13か月・-43%）", 8, "#8A6D12", "end", "700"))
    o.append(f'<line x1="{x(date(2026,11,10))-10:.1f}" y1="{y(71276)+30:.1f}" x2="{x(date(2026,11,10))-2:.1f}" y2="{y(71276)+5:.1f}" stroke="#8A6D12" stroke-width="1"/>')
    o.append(_t(x(date(2026, 6, 30)) - 40, y(58559) + 14, "6/30 $58,559", 8, R, "end", "700"))
    o.append(_t(x(date(2020, 9, 1)), y(2600), "200週線（灰色の点線）", 8, "#5A6170", "middle", "700"))
    o.append("</svg>")
    return "".join(o)


def pages():
    out = []
    # ---------- 3-1 仮説：2つの底が重なる＋ズバリ表 ----------
    vote = "".join(f"<div>{h}</div>" for h in ["名前", "4銘柄で1位は？", "3/31 BTC", "3/31 日経"]) + "".join("<div></div>" for _ in range(12))
    body = f"""
<div class="kpis">
  <div class="kpi"><div class="v">13<small>か月</small></div><div class="l">BTCの天井（2025/10/6）から<br>過去の「天井→底」は12〜13.5か月</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-43<small>%</small></div><div class="l">BTC 天井$124,753→$71,276<br>（11/12、200日線割れ）</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-32<small>%</small></div><div class="l">エヌビディア 6月高値から（11/12）<br>CEO辞任で寄り付き-13%</div></div>
  <div class="kpi"><div class="v">9<small>日</small>/38<small>日</small></div><div class="l">2018年・2022年の<br>SOXの底とBTCの底の差</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>仮説：お年玉は「半導体×暗号資産」</h2>
    <p>今年の年末から来年の頭にかけて、<b>2つの底</b>が重なる可能性があります。</p>
    <ul class="b">
      <li><b>暗号資産の底</b>：ビットコインは4年周期で動き、天井から12〜13.5か月で底を打ってきました。今回は天井から<b>ちょうど13か月</b>で、11/12に200日線を割りました（3-2）。</li>
      <li><b>AI株の底</b>：データセンター規制、ソフトバンクGの赤字、そして11/12のエヌビディアCEO辞任。AI相場の「顔」が消えた今が、不安のピークになりえます。1〜2月の大手決算で2027年の投資額が見えるまでが「不安の期間」です（Session 2）。</li>
      <li><b>共通の理由はお金の流れ</b>：どちらも金利と投資家のリスク許容度に左右される資産です。2018年は9日差、2022年は38日差で、SOXとBTCはほぼ同時に底を打ちました。</li>
    </ul>
    <div class="box tint2" style="margin-top:6px"><p class="small"><b>反対の見方も</b>：今回は6月にSOXが最高値をつけた週にBTCは安値でした。同期がずれている点と、12/9のFOMCで利上げが続けば両方とも底が先に延びる点は注意です。</p></div>
  </div>
  <div>
    <h2><span class="n">2</span>結論：お年玉4銘柄のズバリ表</h2>
    <table class="t">
      <tr><th>銘柄</th><th class="r">現在値</th><th class="r">仕込み値</th><th class="r">3月の目標</th><th class="r">上昇率</th><th class="r">撤退</th></tr>
      <tr style="background:#FBF3E4"><td style="white-space:nowrap"><b>メタプラネット</b><br><span class="small muted">3350・暗号資産</span></td><td class="r">229円</td><td class="r">205円</td><td class="r upc"><b>380円</b></td><td class="r upc">+85%</td><td class="r dn">190円</td></tr>
      <tr style="background:#FBF3E4"><td style="white-space:nowrap"><b>データセクション</b><br><span class="small muted">3905・AIデータセンター</span></td><td class="r">1,336円</td><td class="r">1,150円</td><td class="r upc"><b>2,600円</b></td><td class="r upc">+126%</td><td class="r dn">1,000円</td></tr>
      <tr style="background:#FBF3E4"><td style="white-space:nowrap"><b>スペースX</b><br><span class="small muted">SPCX・宇宙×AI</span></td><td class="r">$141</td><td class="r">$125</td><td class="r upc"><b>$180</b></td><td class="r upc">+44%</td><td class="r dn">$105</td></tr>
      <tr style="background:#FBF3E4"><td style="white-space:nowrap"><b>ブロードコム</b><br><span class="small muted">AVGO・専用AIチップ</span></td><td class="r">$362</td><td class="r">$310</td><td class="r upc"><b>$420</b></td><td class="r upc">+35%</td><td class="r dn">$280</td></tr>
    </table>
    <p class="cap">現在値は11/12終値。仕込み値は12月の損出し・需給イベント（12/9）の後に想定する水準。上昇率は仕込み値から3月の目標まで。</p>
    <div class="box tint" style="margin-top:6px"><h3>選んだ3つの条件</h3><p class="small">①底を打つ理由がある（周期・需給・イベント）　②底を打った後に一番大きく戻る　③先行指標で底打ちを確かめられる。日本株は暗号資産とAIデータセンターの「主役」を1本ずつ、米国株は宇宙×AIの旗振り役と、<b>エヌビディアが揺れた日に買われた専用チップの会社</b>を選びました。</p></div>
  </div>
</div>
<div class="cols" style="grid-template-columns:1fr 1.2fr">
  <div class="box">
    <h3>各銘柄の「先に見るもの」</h3>
    <ul class="b small">
      <li><b>メタプラネット</b>：BTCが$58,000〜62,000で二番底を作るか（3-2・3-3）</li>
      <li><b>データセクション</b>：11/16決算と、コアウィーブ・ネビウス・イオレ（3-4・3-5）</li>
      <li><b>スペースX</b>：12/9のロックアップ解除の売りが一巡するか（3-6）</li>
      <li><b>ブロードコム</b>：12/9決算のAI売上ガイダンスと、エヌビディアの後任CEO（3-6）</li>
    </ul>
  </div>
  <div>
    <h3>飲み会の当てっこシート（3/31に答え合わせ）</h3>
    <div class="vote">{vote}</div>
    <p class="cap">4銘柄から12/1終値→3/31終値の上昇率1位を予想。賞品は次回の飲み会で。</p>
  </div>
</div>"""
    out.append(sheet(3, 1, "お年玉は「半導体×暗号資産」：2つの底が重なる年末に仕込む4銘柄", "ビットコインの周期の底と、エヌビディアCEO辞任で不安がピークのAI株の底。メタプラネット・データセクション・スペースX・ブロードコム", body,
                     ["yfinance：BTC-USD・^SOX の終値から自前集計（天井・底・日付）", "techcentral：2013〜15年のBTC下落", "NVIDIA CEO Transition（2026/11/12）", "S&P Global：中間選挙とデータセンター規制（2026/10）"],
                     abstract="ビットコインは4年周期で動き、天井から12〜13.5か月で底を打ってきた。今回は天井から13か月にあたり、11/12に200日線を割った。一方AI株は、データセンター規制・ソフトバンクGの赤字・エヌビディアCEO辞任で不安がピークに近い。過去2回の底では半導体と暗号資産がほぼ同時に底を打った。この2つの底が重なる年末に、メタプラネット・データセクション・スペースX・ブロードコムの4銘柄を仕込む。",
                     kw="ビットコイン4年周期、エヌビディアCEO辞任、専用AIチップ、お年玉銘柄、ネオクラウド"))

    # ---------- 3-2 ビットコインの4年周期 ----------
    body = f"""
<div class="fig">{btc_cycle_chart()}<div class="cap"><b>Fig.2</b> ビットコインの価格（2週足、対数軸）と200週移動平均（灰色の点線）。半減期から約1年半で天井、そこから約1年で底を打つリズムを繰り返している。赤い帯が今回の底の予想時期。yfinanceから自前作成。</div></div>
<table class="t">
  <tr><th>周期</th><th>半減期</th><th>天井</th><th class="r">半減期→天井</th><th>底</th><th class="r">下落率</th><th class="r">天井→底</th></tr>
  <tr><td>1</td><td>2012/11</td><td>2013/11　$1,163</td><td class="r">約12か月</td><td>2015/1　$152</td><td class="r dn">-87%</td><td class="r">13.5か月</td></tr>
  <tr><td>2</td><td>2016/7</td><td>2017/12　$19,497</td><td class="r">約17か月</td><td>2018/12　$3,237</td><td class="r dn">-83%</td><td class="r">12.0か月</td></tr>
  <tr><td>3</td><td>2020/5</td><td>2021/11　$67,567</td><td class="r">約18か月</td><td>2022/11　$15,787</td><td class="r dn">-77%</td><td class="r">12.4か月</td></tr>
  <tr style="background:#FBF3E4"><td><b>4（今回）</b></td><td>2024/4</td><td><b>2025/10　$124,753</b></td><td class="r">約17.5か月</td><td><b>？</b>（6/30に$58,559）</td><td class="r dn">-53%（暫定）</td><td class="r"><b>13か月経過</b></td></tr>
</table>
<div class="cols">
  <div>
    <h2><span class="n">1</span>今回の底はどこか：2つの見方</h2>
    <table class="t">
      <tr><th>見方</th><th>根拠</th><th class="r">底の価格</th></tr>
      <tr><td><span class="tag u">楽観</span></td><td>下落率は87→83→77%と浅くなってきた。6/30の-53%で200週線を一瞬割って回復＝もう底</td><td class="r">$58,559（済）</td></tr>
      <tr><td><span class="tag c">演者</span></td><td>時期は今が底の予想時期。6/30安値と200週線の間で<b>二番底</b>を作って完成</td><td class="r"><b>$58,000〜62,000</b></td></tr>
      <tr><td><span class="tag r">悲観</span></td><td>浅くなる流れをそのまま延ばすと-65〜70%</td><td class="r dn">$37,000〜44,000</td></tr>
    </table>
  </div>
  <div>
    <h2><span class="n">2</span>演者のズバリ</h2>
    <div class="box tint"><p><b class="em" style="font-size:15px">BTCの底は年末〜1月、$60,000前後の二番底</b></p>
    <p class="small">11/12に200日線（$73,081）を割って$71,000台。ここから200週線（$68,014）を週足で割り込んでも慌てない。<b>$58,000を週足で割らなければ周期の底が完成</b>と見て、メタプラネットを仕込みます。逆に$58,000を割ると悲観シナリオに入るので、一度手を止めます。</p></div>
    <p class="small muted" style="margin-top:4px">200週線は2018年の底ではぴったり支え、2022年は34%下まで割り込みました。万能ではありません。</p>
  </div>
</div>"""
    out.append(sheet(3, 2, "ビットコインの4年周期：天井から13か月、今が「底の予想時期」", "過去3回の天井と底のリズムを今回に当てはめ、底の時期と価格をズバリ予想する", body,
                     ["yfinance：BTC-USD 週足・200週移動平均（自前集計、2014/9以降）", "techcentral：2013〜15年サイクル（$1,163→$152）", "半減期の日付：各種報道"]))

    # ---------- 3-3 メタプラネット ----------
    mp = Chart("mp", 343, view=(560, 300, 1854, 690))
    mp.circle("2025-06-16", 1895, r=16, color=YEL, label="上場来高値 1,895（2025/6）", dx=1, dy=0.2)
    mp.now(229, "11/12 229")
    mp.note_xy(1050, 520, "高値から -88%", PINK, 15)
    mpw = json.loads((HERE / "mp_w.json").read_text())
    fut = [("26/11/27", 255), ("26/12/04", 240), ("26/12/11", 225), ("26/12/18", 212), ("26/12/25", 205), ("27/01/08", 230), ("27/01/22", 265),
           ("27/02/05", 300), ("27/02/19", 330), ("27/03/05", 355), ("27/03/19", 380)]
    labs = [d[2:].replace("-", "/") for d, _ in mpw] + [d for d, _ in fut]
    past = [v for _, v in mpw] + [None] * len(fut)
    proj = [None] * (len(mpw) - 1) + [mpw[-1][1]] + [v for _, v in fut]
    ticks = [i for i, l in enumerate(labs) if l[3:5] in ("01", "04", "07", "10") and l[6:8] <= "07"]
    mpz = line_chart(labs, [(past, C, 2.0, "", "現在 229"), (proj, "#D4A017", 2.4, "5 3", "")], w=340, h=230, lo=150, hi=650, step=100,
                     hlines=[(384, "142週線 384", "#0E9C9C"), (318, "52週線 318", "#5A6170"), (197, "安値 197", R)], xticks=ticks, pr=66, bands=[(197, 215, R, "")])
    ms = Chart("mstr", 270, view=(1300, 340, 1854, 650))
    ms.hline(139.6, "52週線 140", CYAN, x0=1310, x1=1848, lx=1320)
    ms.hline(82.3, "2026年安値 82", PINK, x0=1310, x1=1848, lx=1320, above=True)
    ms.now(114.5, "11/12 114.5")
    ms.path([("2026-11-12", 114.5), ("2026-12-28", 100)], YEL)
    ms.path([("2026-12-28", 105), ("2027-03-20", 160)], GREEN, dash=True)
    lev = bar_chart(["BTC", "メタプラ", "MSTR"], [4.6, 8.9, 14.0], colors=["#9AA5B1", R, C], w=250, h=120, ymin=0, ymax=16, fmt="{:.1f}倍")
    body = f"""
<div class="cols">
  <div style="display:flex;flex-direction:column;gap:8px">
    <div class="fig">{mp.svg()}<div class="cap"><b>Fig.3</b> メタプラネット（3350）週足。上場来高値1,895円（2025/6）から-88%の暴落の全体像。</div></div>
    <div class="fig">{lev}<div class="cap"><b>Fig.5</b> 2022年の底から2024年までの上昇倍率（自前集計）。メタプラは2024年4月にBTC戦略を開始。</div></div>
  </div>
  <div class="fig">{mpz}<div class="cap"><b>Fig.4</b> 直近1年を拡大（週足終値、yfinance）。金色の点線が演者の想定：年末に安値197円付近で二番底→3月に380円。</div></div>
</div>
<div class="cols" style="grid-template-columns:1.15fr 1fr">
  <div>
    <h2><span class="n">1</span>なぜメタプラネットか</h2>
    <ul class="b">
      <li><b>BTCの底打ちを一番大きく受け取る</b>：前回の底（2022年）から、BTCは4.6倍、MSTRは14倍、メタプラは8.9倍になりました（Fig.5）。</li>
      <li><b>株価が保有BTCの価値を下回る</b>（mNAV 1倍前後※）：この状態での自社株買いは、1株あたりのBTCを増やします。10/14〜31に9,645万株（約1.6億ドル）を買い戻しました。</li>
      <li><b>保有は44,000BTC</b>（9/30）。520億円の転換社債（報道）で借入を返し、財務を整えています。</li>
    </ul>
    <h2 style="margin-top:6px"><span class="n">2</span>リスク</h2>
    <ul class="b small">
      <li>6/30安値からの戻りはBTC+22%に対しメタプラ+16%と弱い。BTCが戻っても出遅れる可能性</li>
      <li><b>MSCI指数からの除外が決定</b>（報道）。指数に連動する売りが11月末に出る</li>
      <li>優先株（MERCURY・MARS）の上場は延期中。資金調達の手段が細っている</li>
      <li>BTCが$58,000を割ると、2026年安値197円も割れる</li>
    </ul>
  </div>
  <div>
    <div class="fig">{ms.svg()}<div class="cap"><b>Fig.6</b> 参考：米ストラテジー（MSTR）週足。BTC保有84.9万BTC。BTCの約2倍動く。</div></div>
  </div>
</div>
<div class="box tint"><p class="small"><b>ズバリ：12月後半に205円近辺で仕込み、3月に380円（+85%）</b>。先に見るのはBTC。BTCが$58,000〜62,000で二番底を作るのを確かめてから買います。撤退ラインは190円（2026年安値197円を明確に割ったら）。</p></div>"""
    out.append(sheet(3, 3, "メタプラネット：BTCの底を一番大きく受け取る銘柄", "上場来高値から-88%。週足に二番底のルートと3月の目標を書き込む", body,
                     ["証券アプリ メタプラネット・ストラテジー 週足（2026/11/10、演者のスクリーンショット）", "techflowpost：メタプラネットQ3保有44,000BTC", "coincentral：メタプラネット自社株買い", "sec-api：Strategy Q3 2026", "yfinance：上昇倍率・移動平均（自前集計）"]))

    # ---------- 3-4 データセクション ----------
    dsc = Chart("ds", 700, view=(900, 300, 1854, 690))
    dsc.hline(2634, "26週線 2,634＝3月の目標", CYAN, x0=910, x1=1848, lx=920)
    dsc.hline(1351, "200週線 1,351", WHITE, x0=910, x1=1848, lx=920, above=True)
    dsc.band(1100, 1250, None, PINK, x0=910, x1=1848)
    dsc.note_xy(920, dsc.y(1100) + 34, "仕込みゾーン 1,100〜1,250（52週安値1,230）", PINK, 10.5)
    dsc.circle("2026-05-29", 6140, r=14, color=YEL, label="上場来高値 6,140（5/29）", dx=1, dy=0.3)
    dsc.circle("2026-11-10", 1399, r=12, color=PINK, label="11/10 説明会で-10%", dx=-1, dy=-3.0)
    dsc.now(1336, "11/12 1,336")
    dsc.path([("2026-11-12", 1336), ("2026-11-20", 1480), ("2026-12-28", 1150)], YEL)
    dsc.path([("2026-12-28", 1150), ("2027-03-20", 2600)], GREEN, dash=True)
    dsc.sticker(1000, 340, ["ズバリ", "仕込み1,150円→3月2,600円"], YEL, size=13)
    body = f"""
<div class="fig">{dsc.svg()}<div class="cap"><b>Fig.7</b> データセクション（3905）週足に演者が書き込み。上場来高値6,140円（5/29）から-78%（11/12終値1,336円）。11/16の中間決算と12月の損出し・増資懸念で1,100〜1,250円まで下げ、3月に26週線（2,634円）近くまで戻すルート。</div></div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>なぜデータセクションか</h2>
    <ul class="b">
      <li><b>日本で数少ない、本格的なネオクラウド</b>（GPUを貸すAIデータセンター）。米AIインフラ企業と5年で<b>1,399億23百万円</b>（偶然にも11/10の株価と同じ数字）の契約を結び、10/23に提供を始めました。顧客のデポジットは入金済みと説明しています。</li>
      <li>今期予想は売上<b>1,622億円</b>（前期336億円）、経常利益125億円。豪州ではB300を1万基並べる計画。</li>
      <li>高値から-78%と、<b>12月の損出しで最も売られやすい</b>銘柄の一つ。売り切った後の1月の戻りが大きい。</li>
    </ul>
  </div>
  <div>
    <h2><span class="n">2</span>リスク（下げの理由）</h2>
    <ul class="b small">
      <li><b>11/10</b>：「AIデータセンター稼働状況説明会」で前場+8%から引けは-10%（1,399円）。期待に届かなかった可能性</li>
      <li><b>11/12</b>：ネビウスが好決算でも2026年見通しを下限寄せして-19%。<b>「数字より見通し」で売られる局面</b>。同日データセクションは-3.4%</li>
      <li><b>資金調達</b>：新株予約権は予定548億円に対し271億円しか集まらず。追加の増資・借入の可能性</li>
      <li><b>需給</b>：信用買い残1,169万株・信用倍率5.87倍（10/30）と重い</li>
      <li><b>顧客</b>：テンセントが同社のデータセンター経由でGPUを使っているとの報道（FT）。米国の輸出規制に絡む論点</li>
      <li>国内・豪州・タイの3案件のフル稼働が遅れているとの報道</li>
    </ul>
  </div>
</div>
<table class="t">
  <tr><th>日付</th><th>イベント</th><th>見るポイント</th></tr>
  <tr><td><b>11/11</b></td><td>コアウィーブ Q3決算 <span class="tag u">済</span></td><td>受注残1,325億ドル（+138%）、2026年売上を上方修正。株価+24.7%、翌日-8.6%（3-5）</td></tr>
  <tr><td><b>11/12</b></td><td>ネビウス Q3決算 <span class="tag r">済</span></td><td>売上9.8億ドル（+571%）でも2026年見通しを30〜32億ドルに下限寄せ。-19%</td></tr>
  <tr><td><b>11/16</b></td><td><b>データセクション 中間決算</b></td><td>1Qの一時収入を除いた実力、米国案件の売上計上、資金調達の方針</td></tr>
  <tr><td>12月</td><td>米国案件の全面稼働・追加受注</td><td>GPU10万〜30万基への拡張計画の進み具合</td></tr>
</table>
<div class="box tint"><p class="small"><b>ズバリ：12月後半に1,150円近辺で仕込み、3月に2,600円（+126%）</b>。現在1,336円。ただし11/16の決算で資金調達（増資）の方針が出れば、一度は1,000円割れもありえます。撤退ラインは1,000円。</p></div>"""
    out.append(sheet(3, 4, "データセクション：日本のネオクラウドは「損出しの後」が勝負", "高値から-78%。11/16の中間決算と12月の需給を越えた後の戻りをズバリ予想する", body,
                     ["証券アプリ データセクション 週足（2026/11/10、演者のスクリーンショット）", "voix.jp：1,399億円の大口契約", "TDnet：第23回新株予約権の行使期間満了（10/19）", "Yahoo!ファイナンス：11/10説明会", "ebc.com：信用残・3案件の遅延", "Financial Times：テンセントのGPU利用報道"]))

    # ---------- 3-5 なぜCRWV・NBIS・イオレを見るのか ----------
    def neo(key, view, lines, stick, sy, sx):
        c = Chart(key, 343, view=view)
        for v, lab, col, above in lines:
            c.hline(v, lab, col, x0=view[0] + 10, x1=1848, lx=view[0] + 18, above=above, size=10.5)
        c.sticker(sx, sy, stick, YEL, size=11)
        return c.svg()
    cw = neo("crwv", (1300, 330, 1854, 640), [(86.7, "52週線 86.7", CYAN, True), (43.7, "11/5安値 43.7", PINK, False)], ["決算：受注残1,325億$で+24.7%", "翌日は-8.6%"], 345, 1330)
    nb = neo("nbis", (1300, 300, 1854, 620), [(160.8, "52週線 161", CYAN, True), (73.9, "52週安値 74", PINK, True)], ["決算：売上+571%でも", "見通し下限寄せで-19%"], 315, 1330)
    io = neo("iore", (1200, 360, 1854, 620), [(485, "52週線 485", CYAN, True), (332, "52週安値 332", PINK, False)], ["国内GPU小型株の", "温度計"], 375, 1450)
    body = f"""
<div class="cols">
  <div class="fig">{cw}<div class="cap"><b>Fig.8</b> コアウィーブ（CRWV）。高値138ドルから-60%（11/12終値55.6ドル）。決算で+24.7%の翌日に-8.6%。</div></div>
  <div class="fig">{nb}<div class="cap"><b>Fig.9</b> ネビウス（NBIS）。高値287ドルから-56%（125ドル）。決算で2026年見通しを下限寄せ、-19%。</div></div>
  <div class="fig">{io}<div class="cap"><b>Fig.10</b> イオレ（2334）。GPUサーバー販売から「ネオクラウド」へ転換中の東証グロース株。</div><p class="small muted" style="margin-top:6px">イオレとデータセクションに直接の取引関係は確認できていません。両社は6月にそろって天井をつけ、同じ「国内のGPU小型株」として資金が出入りしています。</p></div>
  <div>
    <h2><span class="n">1</span>同じ構造、同じリスク</h2>
    <p class="small">ネオクラウドはどこも「<b>借金でGPUを買い、AI企業に貸して回収する</b>」商売です。だから共通のリスクで一緒に動きます。</p>
    <ul class="b small">
      <li><b>GPUの陳腐化</b>：3〜4年で価値が大きく落ちる。担保価値と借り換えに響く</li>
      <li><b>借入依存</b>：2026〜28年に借り換えが集中。CRWVの社債が売られると、業界全体の調達コストが上がる</li>
      <li><b>顧客の集中</b>：データセクションは実質1社、CRWVはマイクロソフトとOpenAI</li>
      <li><b>データセンター規制</b>：中間選挙で住民投票の多くが否決。テキサスは優遇税制を見直し</li>
    </ul>
    <div class="box tint" style="margin-top:6px"><p class="small"><b>結果</b>：コアウィーブは受注残1,325億ドル・2026年見通しの上方修正で+24.7%。ネビウスは売上+571%でも見通しの下限寄せで-19%。<b>「数字が良くても、見通しが少しでも弱ければ売られる」</b>のが今のAI株です。データセクションの11/16決算も同じ目で見られます。<b>仕込みは決算を通過した12月後半まで待つ</b>、が結論。</p></div>
  </div>
</div>
<div>
  <div>
    <h2><span class="n">2</span>3社がデータセクションの「先行指標」になる理由</h2>
    <table class="t">
      <tr><th style="width:22%">見るもの</th><th style="width:42%">どこで見るか</th><th>データセクションにとっての意味</th></tr>
      <tr><td><b>① GPUの単価</b></td><td>CRWV・NBISの新規契約の単価（H100で1時間2〜6ドル、B200で4〜9ドル）</td><td>1,399億円契約の妥当性と、更新時の単価</td></tr>
      <tr><td><b>② 受注残</b></td><td>CRWV 1,325億ドル（9月末、+138%）、NBIS 400億ドル超（ただしRPOは+3%）</td><td>需要が続くか＝豪州・タイ案件が埋まるか</td></tr>
      <tr><td><b>③ 借金のコスト</b></td><td>CRWVの社債の利回り（10月に額面80割れの報道）、NBISの転換社債の条件</td><td>次の資金調達が増資か借入か。希薄化のリスク</td></tr>
      <tr><td><b>④ 稼働の速さ</b></td><td>両社の稼働電力（MW）の立ち上がり、遅延の有無</td><td>3案件の遅延報道と比べる</td></tr>
      <tr><td><b>⑤ 株価の温度</b></td><td>CRWVの52週線との距離、イオレの値動き</td><td>米国と国内の投資家がGPU株をまだ買う気があるか</td></tr>
    </table>
  </div>
  <div>
  </div>
</div>
"""
    out.append(sheet(3, 5, "なぜコアウィーブ・ネビウス・イオレを見るのか", "データセクションと同じ「借金でGPUを買って貸す」商売。5つの先行指標", body,
                     ["証券アプリ CRWV・NBIS・イオレ 週足（2026/11/10、演者のスクリーンショット）", "techtimes：CoreWeave Q3 決算プレビュー", "BusinessWire：CoreWeave 新規容量を高単価で契約（9/17）", "gurufocus：Nebius Q2 2026", "yfinance：52週線・52週高安"]))

    # ---------- 3-6 米国株2選：ブロードコムとスペースX ----------
    wj = json.loads((HERE / "avgo_w.json").read_text())
    def series(key, last):
        pts = [(d, v) for d, v in wj[key] if d >= "2026-05-25"]
        pts[-1] = ("2026-11-12", last)
        return pts
    av, nv, mv = series("avgo", 362.1), series("nvda", 163.5), series("mrvl", 162.6)
    labs = [d[2:].replace("-", "/") for d, _ in av]
    ticks = [i for i, (d, _) in enumerate(av) if d[8:10] <= "07"]
    base = {"avgo": max(v for _, v in av), "nvda": max(v for _, v in nv), "mrvl": max(v for _, v in mv)}
    rel = line_chart(labs, [([v / base["nvda"] * 100 for _, v in nv], "#5A6170", 1.8, "", f"NVIDIA {nv[-1][1]/base['nvda']*100:.0f}"),
                            ([v / base["mrvl"] * 100 for _, v in mv], "#B8860B", 1.8, "", f"マーベル {mv[-1][1]/base['mrvl']*100:.0f}"),
                            ([v / base["avgo"] * 100 for _, v in av], C, 2.4, "", f"ブロードコム {av[-1][1]/base['avgo']*100:.0f}")],
                     w=340, h=180, lo=40, hi=110, step=20, xticks=ticks, pr=78, hlines=[(100, "6月高値=100", "#9AA5B1")])
    fut = [("26/11/27", 350), ("26/12/09", 335), ("26/12/26", 310), ("27/01/23", 345), ("27/02/20", 385), ("27/03/19", 420)]
    labs2 = labs + [d for d, _ in fut]
    past = [v for _, v in av] + [None] * len(fut)
    proj = [None] * (len(av) - 1) + [av[-1][1]] + [v for _, v in fut]
    ticks2 = [i for i, l in enumerate(labs2) if l[3:5] in ("06", "08", "10", "12", "02") and l[6:8] <= "07"]
    avc = line_chart(labs2, [(past, C, 2.0, "", ""), (proj, "#D4A017", 2.4, "5 3", "")], w=340, h=180, lo=260, hi=500, step=40,
                     hlines=[(480, "52週高値 480", "#9AA5B1"), (366, "200日線 366", "#0E9C9C"), (290, "11/5安値 290", R)], xticks=ticks2, pr=70, bands=[(300, 320, R, "")])
    sp = Chart("spcx", 343, view=(1330, 340, 1854, 690))
    sp.hline(211.4, "上場来高値 211", WHITE, x0=1340, x1=1848, lx=1350, above=False)
    sp.hline(135, "公開価格 135", CYAN, x0=1340, x1=1848, lx=1350)
    sp.band(108, 125, None, PINK, x0=1340, x1=1848)
    sp.note_xy(1350, sp.y(125) - 8 * sp.u, "仕込み 108〜125", PINK, 11)
    sp.now(141, "11/12 141")
    sp.path([("2026-11-12", 141), ("2026-12-09", 122)], YEL)
    sp.path([("2026-12-09", 122), ("2027-03-20", 180)], GREEN, dash=True)
    sp.sticker(1420, 360, ["ズバリ", "12/9後125→3月180"], YEL, size=12)
    tl = timeline([(0, "12/1頃|マーベル決算", False), (8, "12/9|ブロードコム決算・SPCX解除・FOMC", True), (14, "12月中旬|損出しピーク", False), (27, "12/28|年内受渡最終日", True),
                   (34, "1/4|大発会・NISA新枠", True), (58, "1月下旬|大手決算・投資計画", False), (75, "2月|メタプラ通期決算", False), (84, "2月下旬|NVIDIA決算", False), (118, "3/31|答え合わせ", True)],
                  w=700, color=C, accent=R)
    body = f"""
<div class="cols">
  <div class="fig">{avc}<div class="cap"><b>Fig.11</b> ブロードコム（AVGO）週足終値（yfinance）。金色の点線が演者の想定：12/9決算と年末の損出しで300〜320ドルまで押し、3月に420ドル。</div></div>
  <div class="fig">{rel}<div class="cap"><b>Fig.12</b> 6月高値を100とした3社の値動き（週足）。マーベルは11/2の買収発表で急落、エヌビディアはCEO辞任で下げ幅を広げた。ブロードコムが最も崩れていない。</div></div>
</div>
<div class="cols" style="grid-template-columns:1.1fr 1fr">
  <div>
    <h2><span class="n">1</span>なぜ「エヌビディア」ではなく「ブロードコム」か</h2>
    <ul class="b">
      <li><b>GPUの王が揺れた日に買われた株</b>：11/12、エヌビディアが寄り付き-13%の日に、ブロードコムは<b class="upc">+4.9%</b>、AMDは+3.7%。大手クラウドは「GPU一辺倒」を見直し、自社専用チップ（ASIC）を急ぎます。Google TPU、Meta MTIA（Q4に量産出荷）、OpenAI Jalapeño（第1世代を出荷中）の設計と量産を担うのがブロードコムです。</li>
      <li><b>数字が大きく、見通しが具体的</b>：Q3のAI半導体売上は<b>167億ドル（+221%）</b>、Q4ガイダンスは217億ドル、FY27のAI売上は約1,150億ドルの見通し。フリーCF比率46%、予想PERは約19倍です。<b>12/9の決算</b>が年内最大の材料。</li>
      <li><b>計算と接続の両輪</b>：ASICが増えてもGPUが増えても、チップ同士をつなぐEthernetスイッチ（Tomahawk 6、102.4Tbps）が売れます。光電融合（CPO）と3.5Dパッケージで「電力と発熱の壁」を解く技術も持ち、どちらが勝っても取り分がある会社です。</li>
    </ul>
  </div>
  <div>
    <h2><span class="n">2</span>3社の違い：マーベルではなくブロードコムの理由</h2>
    <table class="t">
      <tr><th>会社</th><th>何を作る</th><th class="r">11/12</th><th class="r">高値比</th><th class="r">予想PER</th></tr>
      <tr><td><b>エヌビディア</b></td><td>汎用GPU＋CUDA。CEO不在、11/17決算は暫定CEO</td><td class="r">$163.5</td><td class="r dn">-32%</td><td class="r">約10倍</td></tr>
      <tr><td><b>ブロードコム</b></td><td>顧客専用ASIC＋Ethernet＋VMware。顧客はGoogle・Meta・OpenAI</td><td class="r">$362.1</td><td class="r dn">-24%</td><td class="r">約19倍</td></tr>
      <tr><td><b>マーベル</b></td><td>顧客専用ASIC＋光DSP。顧客はAmazon中心。11/2のLumentum買収（1,150億ドル、株数+50%）で1週間に-28%</td><td class="r">$162.6</td><td class="r dn">-49%</td><td class="r">約22倍</td></tr>
    </table>
    <p class="small" style="margin-top:4px">マーベルは最も近い競合（3月にエヌビディアが20億ドル出資）ですが、顧客がAmazonに偏り、買収で株数が5割増える<b>希薄化の消化に時間がかかります</b>。先に戻るのは、顧客が3社に分かれ、ネットワークでも稼ぐブロードコムと見ます。</p>
    <div class="box tint2 small"><b>リスク</b>：顧客3社への集中、12/9決算で「期待超え」が必要（9月はAI見通しに失望して売られた）、年末48,000円シナリオではSOXと一緒に下げる（β≈1.1）。だから<b>仕込みは310ドル前後まで待つ</b>。</div>
  </div>
</div>
<div class="cols" style="grid-template-columns:1fr 1.2fr">
  <div class="fig">{sp.svg()}<div class="cap"><b>Fig.13</b> スペースX（SPCX）週足。6/12上場、公開価格135ドル。12/9のロックアップ解除の売りで125ドル前後まで下げてから、3月に180ドルを狙う。</div></div>
  <div>
    <h2><span class="n">3</span>スペースX：需給の底がはっきりしている</h2>
    <ul class="b small">
      <li><b>12/9に180日ロックアップの一部が解除予定※</b>。解除前に売られ、解除後に戻るのが上場株の典型。同じ日にブロードコム決算とFOMCが重なる「12/9」が、米国株2銘柄の仕込みの日。</li>
      <li>Q2売上78億ドル（前年比+92%）。Starlinkが稼ぎ、AI向けの投資も始めた「宇宙×AI」の旗振り役。7/7にNASDAQ100採用、S&amp;P500採用は早くても2027年6月以降。</li>
      <li>リスク：AI投資で利益が圧迫される。エヌビディア騒動でAI関連の資金が細れば、ロックアップの売りが長引く。</li>
    </ul>
  </div>
</div>
"""
    out.append(sheet(3, 6, "米国株2選：ブロードコムとスペースX", "エヌビディアが揺れた日に買われた「専用チップ」の会社と、12/9の需給を越えた宇宙×AIの旗振り役", body,
                     ["Broadcom 2026年度Q3決算（9月）・Q4決算予定 12/9", "Broadcom企業分析資料（2026/11/13、演者の参考資料）：カスタムAI半導体・Ethernet・3.5D/CPO", "OpenAI：Jalapeño 推論チップ", "Reuters：11/12 Broadcom +4.9%・AMD +3.7%", "Motley Fool：Marvell Lumentum買収と株価（11/7）", "Fortune：SpaceX lockup expiration（2026/8/5）", "yfinance：株価・移動平均・予想PER（11/13取得）"]))
    return out
