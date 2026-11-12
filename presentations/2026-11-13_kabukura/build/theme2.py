from kit import sheet, bar_chart, hbar_chart, timeline
from annot import Chart, YEL, PINK, CYAN, WHITE, GREEN

C, A = "#0B4F5C", "#0E9C9C"


def pages():
    out = []
    # ---------- 2-1 ----------
    fig1 = bar_chart(["2000-02|ITバブル".split("|")[0], "2008|金融危機".split("|")[0], "2022|利上げ".split("|")[0], "2026今回"], [-80, -60, -45, -38],
                     colors=["#9AA5B1", "#9AA5B1", "#9AA5B1", "#C1121F"], fmt="{:.0f}%", w=330, h=150, ymin=-90, ymax=0)
    body = f"""
<div class="kpis">
  <div class="kpi"><div class="v">10,372</div><div class="l">SOX指数（11/12終値）<br>11/11 +5.7%→CEO辞任で-1.8%</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-29<small>%</small></div><div class="l">6/22高値14,634→11/12終値<br>（11/5安値9,011では-38%）。弱気相場入り</div></div>
  <div class="kpi"><div class="v">+4.8<small>%</small></div><div class="l">200日線10,874までの距離<br>回復＝トレンド転換の目安</div></div>
  <div class="kpi"><div class="v">725<small>B$</small></div><div class="l">米大手4社の2026年AI投資<br>（中央値・据え置き〜増額）</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>なぜ売られたか</h2>
    <ul class="b">
      <li><b>AI投資の回収への疑問</b>：7月だけでSOXは約-21%、2008年以来最悪の月でした。</li>
      <li><b>10/30 インテル決算ショック</b>：1日で-28.6%（1974年以来最大）。PC市場は2026年-12%の見通しです。</li>
      <li><b>11/3 中間選挙で民主党が大勝</b>：データセンター関連の住民投票は41件中40件が否決。電力料金の高騰が争点になりました。</li>
      <li><b>メモリ株の利益確定</b>：10/29〜11/6にMU・SKハイニックスがともに約-26%。</li>
      <li><b>11/12 エヌビディアCEO辞任</b>：不倫問題と独立調査の末、ファン氏が即時辞任。寄り付き-13%、時価総額は一時-6,010億ドル。AI相場の「顔」が消えた。</li>
    </ul>
    <h2 style="margin-top:6px"><span class="n">2</span>それでも業績は過去最高</h2>
    <ul class="b">
      <li>NVIDIAの今期売上ガイダンスは<b>108B$</b>（市場予想は約104B$）。前四半期のデータセンター売上は前年比+117%。</li>
      <li>AMDのQ3売上は+45%。アドバンテストは通期営業利益見通しを<b>9,670億円</b>に上方修正し、2,800億円の自社株買いも決めました。</li>
      <li>Metaは2026年のAI投資を125〜145B$に引き上げ。アマゾン・アルファベットは「2027年はさらに大幅増」と発言しています。</li>
    </ul>
  </div>
  <div>
    <div class="fig">{fig1}<div class="cap"><b>Fig.1</b> SOX指数の高値からの最大下落率（過去の大相場との比較）。2008年は概算※。今回は11/5安値まで。</div></div>
    <div class="box tint" style="margin-top:8px">
      <h3>本セッションの問い</h3>
      <p class="small">今回の下げは2000年型（需要そのものが消える）か、2022年型（金利とバリュエーションの調整）か。演者は<b>「株価は売られたが、事業は売られていない」2022年型に近い</b>と考えます。ただし政治（データセンター規制）という新しいリスクが加わった点は2022年と違います。</p>
    </div>
    <div class="box" style="margin-top:8px">
      <h3>巻き返しの3条件</h3>
      <ul class="b small">
        <li><span class="em">①</span> 11/17 NVIDIA決算（暫定CEOクレス氏の初決算）で「108B$超え＋強気の次期ガイダンス」、後任CEOの道筋</li>
        <li><span class="em">②</span> SOXが200日線（10,874）を終値で回復</li>
        <li><span class="em">③</span> 1〜2月の大手決算で2027年AI投資の増額が見える</li>
      </ul>
    </div>
  </div>
  <div class="span2">
    <h2><span class="n">3</span>SOX指数の節目</h2>
    <table class="t">
      <tr><th>節目</th><th class="r">水準</th><th class="r">現在値10,372から</th><th>意味</th></tr>
      <tr><td>6/22 年初来高値</td><td class="r">14,634</td><td class="r upc">+41.1%</td><td>ここまで戻れば「完全回復」。2027年のAI投資増額が前提</td></tr>
      <tr><td>75日線</td><td class="r">11,709</td><td class="r upc">+12.9%</td><td>中期の上値メド。戻り売りが出やすい</td></tr>
      <tr><td><b>200日線</b></td><td class="r"><b>10,874</b></td><td class="r upc"><b>+4.8%</b></td><td><b>回復＝トレンド転換の合図（巻き返しの条件②）</b></td></tr>
      <tr><td>11/5 安値</td><td class="r">9,011</td><td class="r dn">-13.1%</td><td>割れたら2番底を探る展開。撤退ライン</td></tr>
    </table>
  </div>
</div>"""
    out.append(sheet(2, 1, "半導体は「弱気相場」入り、そこへCEO辞任。それでも業績は過去最高", "高値から-38%の調整は2000年型か2022年型か。巻き返しの3条件を考える", body,
                     ["newsbytesapp: SOX in bear territory (2026/11)", "Fortune: chip stocks volatility (2026/8/2)", "Al Jazeera: midterms and data centres (2026/11/7)", "NVIDIA IR: Q3 FY27 conference call (11/17)", "インテル決算報道（2026/10/30）", "yfinance 株価・移動平均（11/9取得）"],
                     abstract="SOX指数は6月の高値14,634から11/5の9,011まで約38%下落し、弱気相場に入った。11/12にはエヌビディアのCEOが辞任した。理由はAI投資の回収への疑問、インテル決算、中間選挙後のデータセンター規制懸念である。一方で主要企業の業績とAI投資計画は上方修正が続く。株価と業績の差が、巻き返しの余地になる。",
                     kw="SOX、弱気相場、AI capex、NVIDIA決算、200日線"))

    # ---------- 2-2 ----------
    capex = hbar_chart(["アマゾン", "アルファベット", "マイクロソフト※", "Meta"], [220, 200, 170, 135], colors=[C, C, "#7FA9B0", C], fmt="{:.0f}B$", w=330, row=22, label_w=92, vmax=260)
    wsts = bar_chart(["2025", "2026", "2027"], [0.80, 1.51, 1.90], colors=["#9AA5B1", C, A], fmt="{:.2f}兆$", w=330, h=140, ymin=0, ymax=2.2)
    body = f"""
<div class="cols">
  <div class="span2">
    <h2><span class="n">1</span>AIバリューチェーンと日米の代表銘柄</h2>
    <table class="t">
      <tr><th>層</th><th>役割</th><th>米国・海外</th><th>日本</th><th>今の位置づけ</th></tr>
      <tr><td><b>GPU / ASIC</b></td><td>AIの計算</td><td>NVIDIA（CEO交代）, Broadcom, AMD</td><td>ソシオネクスト</td><td>CEO辞任でGPU一強の前提が揺れ、11/12はBroadcom +4.9%・AMD +3.7%。専用ASICは2027年に60〜90B$の市場</td></tr>
      <tr><td><b>ファウンドリ</b></td><td>先端品の製造</td><td>TSMC</td><td>ラピダス（非上場）</td><td>先端品はほぼ独占。台湾リスクは常に意識</td></tr>
      <tr><td><b>メモリ / HBM</b></td><td>AI向け高速メモリ</td><td>Micron, SKハイニックス</td><td>キオクシア</td><td>業績の伸びは最大、値動きも最大のサイクル株</td></tr>
      <tr><td><b>製造装置</b></td><td>工場の設備</td><td>ASML, AMAT, Lam</td><td>東京エレクトロン, ディスコ, レーザーテック, SCREEN</td><td>投資計画の影響が半年〜1年遅れて出る</td></tr>
      <tr><td><b>検査・テスト</b></td><td>完成品の検査</td><td>Teradyne</td><td>アドバンテスト</td><td>AI向けテスターがけん引。上方修正済み</td></tr>
      <tr><td><b>電力・DC</b></td><td>電源・冷却・配線</td><td>Vertiv, Constellation</td><td>フジクラ</td><td><span class="dn">選挙後の規制リスクが最も大きい層</span></td></tr>
      <tr><td><b>クラウド / ソフト</b></td><td>AIで稼ぐ側</td><td>MSFT, GOOGL, META, AMZN, PLTR</td><td>さくらインターネット</td><td>投資額を決める側。相対的に底堅い</td></tr>
      <tr><td><b>AI投資会社</b></td><td>出資・保有</td><td>—</td><td>ソフトバンクG</td><td>OpenAI関連のレバレッジ。上下に振れやすい</td></tr>
    </table>
  </div>
  <div>
    <h2><span class="n">2</span>お金の流れ：誰が払い、誰が受け取るか</h2>
    <p>AI半導体の需要は、ほぼ<b>米大手4社のAI投資（capex）</b>で決まります。4社の2026年計画は合計<b>約710〜740B$</b>で、Moody'sは2027年に「1兆$に迫る」と見ています。</p>
    <div class="fig">{capex}<div class="cap"><b>Fig.2</b> 米大手4社の2026年AI投資計画（B$=10億ドル、レンジは中央値）。※マイクロソフトは暦年換算の二次情報※。</div></div>
  </div>
  <div>
    <h2><span class="n">3</span>市場規模は2年で倍以上</h2>
    <p>WSTS（世界半導体市場統計）の2026年春季予測では、2026年は<b>1.51兆$（+89.9%）</b>、2027年は約1.9兆$（+26.6%）。メモリだけで2027年に1.06兆$です。</p>
    <div class="fig">{wsts}<div class="cap"><b>Fig.3</b> 世界半導体市場の予測（WSTS 2026年6月）。2025年は2026年の伸び率から逆算。秋季予測は12月公表予定。</div></div>
  </div>
  <div class="span2 box tint2">
    <h3>演者の見方：今は「受け取る側」の株価だけが先に崩れた</h3>
    <p class="small">払う側（大手4社）は投資計画を下げていません。にもかかわらず、受け取る側の半導体株は高値から2〜6割下げています。<b>1〜2月の大手決算で2027年の投資額が示された時</b>が、この差が埋まるかどうかの分かれ目です。逆に投資額の伸びが鈍れば、装置・メモリ・電力の順に下げが深くなる点に注意します。エヌビディアのCEO辞任は、払う側が「GPU一辺倒」を見直す口実になり、専用チップのブロードコムに資金が動きました（Session 3-6）。</p>
  </div>
</div>"""
    out.append(sheet(2, 2, "AIのお金の流れ：払う側は減らさず、受け取る側の株価だけが下げた", "バリューチェーン8層と、需要を決める米大手4社のAI投資", body,
                     ["WSTS 2026年春季予測（JEITA, 2026/6/2）", "DatacenterDynamics: Moody's hyperscaler capex forecasts", "各社決算資料（Meta, Amazon, Alphabet 2026年Q3）", "Broadcom 決算説明（ASIC市場機会）"]))

    # ---------- 2-3 チャートで読む米国の半導体 ----------
    sx = Chart("sox", 700, view=(1250, 345, 1854, 585))
    sx.hline(10852, "戻りの目標 10,874（200日線）", CYAN, x0=1260, x1=1848, lx=1270)
    sx.hline(9011, "11/5安値 9,011（撤退ライン）", WHITE, x0=1260, x1=1848, lx=1270, above=True)
    sx.band(8124, 8700, "78.6%押し 8,124〜", PINK, x0=1260, x1=1848, lx=1450)
    sx.hline(7017, "142週線 7,017", WHITE, x0=1260, x1=1848, lx=1450, above=True)
    sx.now(10372, "11/12 10,372")
    sx.path([("2026-11-12", 10372), ("2026-11-24", 10870), ("2026-12-28", 8500)], YEL)
    sx.path([("2026-12-28", 8500), ("2027-02-10", 10000)], GREEN, dash=True)
    sx.sticker(1330, 356, ["ズバリ", "年末 SOX 8,500"], YEL, size=13)
    def small(key, view, lines, path, stick, sy):
        c = Chart(key, 343, view=view)
        for v, lab, col, above in lines:
            c.hline(v, lab, col, x0=view[0] + 10, x1=1848, lx=view[0] + 18, above=above, size=10.5)
        c.now(path[0][1], f"{path[0][1]:,}")
        c.path(path, YEL)
        c.sticker(view[0] + 40, sy, ["ズバリ " + stick], YEL, size=12)
        return c.svg()
    nd = small("ndx", (1350, 350, 1854, 600), [(28006, "200日線 28,006", CYAN, True), (25000, "25,000", PINK, False)],
               [("2026-11-12", 28170), ("2026-11-24", 28600), ("2026-12-28", 25000)], "25,000", 362)
    ts = small("tsm", (1350, 300, 1854, 520), [(401, "200日線 401", CYAN, True), (381, "52週線 381", WHITE, False), (340, "340", PINK, False)],
               [("2026-11-12", 405.2), ("2026-11-24", 425), ("2026-12-28", 340)], "340ドル", 312)
    mu = small("mu", (1350, 330, 1854, 600), [(934, "13週線 934", CYAN, True), (666, "52週線 666", WHITE, True), (600, "600", PINK, False)],
               [("2026-11-12", 774), ("2026-11-24", 850), ("2026-12-28", 600)], "600ドル", 342)
    body = f"""
<div class="fig">{sx.svg()}<div class="cap"><b>Fig.4</b> SOX指数（米半導体株）の週足に演者が書き込み。11/17のNVIDIA決算で200日線まで戻した後、年末に78.6%押し（8,124〜）を試すルート。緑の点線は年明けの戻り。</div></div>
<div class="cols">
  <div class="fig">{nd}<div class="cap"><b>Fig.5</b> NASDAQ100。200日線（28,006）の攻防。割れれば25,000。</div></div>
  <div class="fig">{ts}<div class="cap"><b>Fig.6</b> TSMC（ADR）。下げは浅いが、52週線381を割ると340まで。</div></div>
  <div class="fig">{mu}<div class="cap"><b>Fig.7</b> マイクロン。13週線を割り、52週線666が最後の砦。</div></div>
  <div>
    <h2><span class="n">1</span>4枚のチャートから読めること</h2>
    <ul class="b">
      <li><b>SOXは「戻り売り」の形</b>：13週・26週線が下向きに転じ、200日線（10,874）が上値の壁です。11/11に+5.7%であと4.8%まで迫りましたが、翌日のCEO辞任で失速。11/17の決算で届いても、そこは売られやすい。</li>
      <li><b>強弱がはっきり分かれた</b>：TSMCは52週線の上で踏ん張り、マイクロンは13週線を大きく割りました。下げの主役はメモリと装置です。</li>
    </ul>
    <p class="small" style="margin-top:6px">SOXの8,124〜8,500は、2025年11月の安値6,352から6月高値14,634への上昇の<b>78.6%押し</b>。Session 1の日経48,000〜50,000円とほぼ同じ「今年の上げをほぼ帳消し」の水準です。</p>
  </div>
</div>
<div>
  <div>
    <h2><span class="n">2</span>ズバリ表（年末の想定）</h2>
    <table class="t">
      <tr><th>指数・銘柄</th><th class="r">現在</th><th class="r">戻り目標</th><th class="r">年末ズバリ</th><th class="r">現在から</th></tr>
      <tr><td><b>SOX</b></td><td class="r">10,372</td><td class="r">10,874</td><td class="r dn"><b>8,500</b></td><td class="r dn">-18%</td></tr>
      <tr><td>NASDAQ100</td><td class="r">28,170</td><td class="r">28,600</td><td class="r dn">25,000</td><td class="r dn">-11%</td></tr>
      <tr><td>TSMC</td><td class="r">$405</td><td class="r">$425</td><td class="r dn">$340</td><td class="r dn">-16%</td></tr>
      <tr><td>マイクロン</td><td class="r">$774</td><td class="r">$850</td><td class="r dn">$600</td><td class="r dn">-22%</td></tr>
    </table>
  </div>
</div>"""
    out.append(sheet(2, 3, "チャートで読む米国の半導体：200日線まで戻して再び売られる", "SOX・NASDAQ100・TSMC・マイクロンの週足に、戻りの目標と年末の下値を書き込む", body,
                     ["証券アプリ SOX・NASDAQ100・TSMC・マイクロン 週足（2026/11/10、演者のスクリーンショット）", "yfinance：200日線・52週線・13週線・52週安値（11/10取得、自前計算）", "NVIDIA IR：Q3 FY27決算（11/17）"]))

    # ---------- 2-4 チャートで読む日本の半導体・電線 ----------
    def jp(key, view, lines, path, stick, sy):
        c = Chart(key, 343, view=view)
        for v, lab, col, above in lines:
            c.hline(v, lab, col, x0=view[0] + 10, x1=1848, lx=view[0] + 18, above=above, size=10.5)
        c.now(path[0][1], f"{path[0][1]:,}")
        c.path(path, YEL)
        c.sticker(view[0] + 30, sy, ["ズバリ", stick], YEL, size=12)
        return c.svg()
    ad = jp("advt", (1350, 330, 1854, 590), [(31897, "戻り目標 31,900（26週線）", CYAN, True), (27811, "52週線 27,811", WHITE, False), (20200, "日経5万円なら 20,200", PINK, False)],
            [("2026-11-12", 29985), ("2026-11-24", 32000), ("2026-12-28", 21000)], "年末 21,000円", 342)
    kx = jp("kxa", (1350, 320, 1854, 680), [(15448, "戻り目標 15,400（13週線）", CYAN, True), (13113, "52週線 13,113", WHITE, False), (4000, "日経5万円なら 4,000", PINK, False)],
            [("2026-11-12", 9300), ("2026-11-24", 11000), ("2026-12-28", 4500)], "年末 4,500円", 332)
    fj = jp("fjk", (1350, 340, 1854, 640), [(4410, "52週線 4,410", CYAN, True), (2637, "52週安値 2,637", WHITE, True), (2306, "142週線 2,306", PINK, False)],
            [("2026-11-12", 3002), ("2026-11-24", 3500), ("2026-12-28", 2300)], "年末 2,300円", 352)
    fr = jp("frk", (1350, 330, 1854, 650), [(3123, "52週線 3,123", CYAN, True), (1500, "142週線 1,500", PINK, False)],
            [("2026-11-12", 2285), ("2026-11-24", 2600), ("2026-12-28", 1500)], "年末 1,500円", 342)
    body = f"""
<div class="cols">
  <div class="fig">{ad}<div class="cap"><b>Fig.8</b> アドバンテスト（6857）。上方修正と自社株買いでも、日経に対するベータは1.85。</div></div>
  <div class="fig">{kx}<div class="cap"><b>Fig.9</b> キオクシア（285A）。ベータ3.17と日本株で最も振れが大きい。</div></div>
  <div class="fig">{fj}<div class="cap"><b>Fig.10</b> フジクラ（5803）。データセンター向け光ファイバー。142週線まで。</div></div>
  <div class="fig">{fr}<div class="cap"><b>Fig.11</b> 古河電工（5801）。年初来+88%からの急落。142週線1,500円まで。</div></div>
</div>
<table class="t">
  <tr><th>銘柄</th><th class="r">現在値</th><th class="r">ベータ</th><th class="r">日経5万円時の理論値</th><th>テクニカルの節目</th><th class="r">年末ズバリ</th><th class="r">現在から</th></tr>
  <tr><td><b>アドバンテスト</b></td><td class="r">29,985</td><td class="r">1.85</td><td class="r">約20,100</td><td>52週線27,811を割ると節目が遠い</td><td class="r dn"><b>21,000</b></td><td class="r dn">-30%</td></tr>
  <tr><td><b>キオクシア</b></td><td class="r">9,300</td><td class="r">3.17</td><td class="r">約4,050</td><td>上場来の上げの起点が遠い</td><td class="r dn"><b>4,500</b></td><td class="r dn">-52%</td></tr>
  <tr><td><b>フジクラ</b></td><td class="r">3,002</td><td class="r">1.90</td><td class="r">約1,990</td><td>52週安値2,637・142週線2,306</td><td class="r dn"><b>2,300</b></td><td class="r dn">-23%</td></tr>
  <tr><td><b>古河電工</b></td><td class="r">2,285</td><td class="r">2.42</td><td class="r">約1,300</td><td>142週線1,500</td><td class="r dn"><b>1,500</b></td><td class="r dn">-34%</td></tr>
</table>
<p class="cap">ベータは直近1年の週次リターンで日経平均に対して自前計算。理論値＝現在値×（1－ベータ×17.8%）。日経の現在値60,819円（11/12）から50,000円までは-17.8%。株価は11/12終値。</p>
<div class="cols">
  <div class="box tint">
    <h3>日本の半導体・電線は「日経の2〜3倍」動く</h3>
    <p class="small">4銘柄のベータは1.85〜3.17。日経が-18%なら<b>-33〜57%</b>です。逆に、日経が48,000〜50,000円から戻る局面では<b>最も大きく戻る</b>グループでもあります。下げの最終局面で拾うなら、業績が裏付けるアドバンテストとフジクラが第一候補です。</p>
  </div>
  <div class="box tint2">
    <h3>演者の注意点</h3>
    <p class="small">キオクシアは6月高値36,172円から-76%と、すでに「暴落後」です。ベータどおりに4,000円台まで下げるかは分かりません。<b>ズバリの数字は「そこまで下げても困らない量にしておく」ための目安</b>で、当てにいくための数字ではありません。</p>
  </div>
</div>"""
    out.append(sheet(2, 4, "チャートで読む日本の半導体・電線：日経の2〜3倍動く4銘柄の下値", "アドバンテスト・キオクシア・フジクラ・古河電工の週足に、ベータから出した年末の下値を書き込む", body,
                     ["証券アプリ 各社 週足（2026/11/10、演者のスクリーンショット。現在値は11/12終値）", "yfinance：週次ベータ・移動平均・52週安値（自前計算）", "アドバンテスト 2026/10/28 適時開示"]))

    # ---------- 2-5 売られすぎマップ ----------
    names = ["キオクシア", "フジクラ", "SKハイニックス※", "SCREEN", "ソフトバンクG", "ディスコ", "LRCX", "AMAT", "東京エレクトロン", "Vertiv", "Micron", "レーザーテック", "Broadcom", "アドバンテスト", "NVIDIA", "TSMC", "MSFT", "Marvell"]
    dd = [74.3, 61.5, 61.2, 55.6, 56.7, 46.3, 46.2, 46.6, 40.5, 44.8, 36.1, 36.5, 24.4, 28.4, 31.7, 16.6, 5.5, 48.6]
    pairs = sorted(zip(names, dd), key=lambda p: -p[1])
    names, dd = [p[0] for p in pairs], [p[1] for p in pairs]
    jp = {"キオクシア", "フジクラ", "SCREEN", "ソフトバンクG", "ディスコ", "東京エレクトロン", "レーザーテック", "アドバンテスト"}
    fig4 = hbar_chart(names, dd, colors=[A if n in jp else C for n in names], fmt="-{:.0f}%", w=300, row=17.2, label_w=96, vmax=88, note="淡色=日本　濃色=米国ほか")
    rows = [
        ("NVIDIA", "NVDA", "$163.5", -12.4, -31.7, "11/17決算（暫定CEO）", "CEO不在・後任未定"),
        ("Broadcom", "AVGO", "$362.1", 6.3, -24.4, "専用ASIC・12/9決算", "顧客集中"),
        ("Marvell", "MRVL", "$162.6", 81.2, -48.6, "AWS向け専用ASIC", "買収の希薄化"),
        ("AMD", "AMD", "$562.9", 155, -13.3, "NVIDIAの代替", "高値圏"),
        ("TSMC", "TSM", "$405.2", 26.9, -16.6, "先端品を独占", "台湾・関税"),
        ("Micron", "MU", "$774.1", 148, -36.1, "HBMの品薄", "価格の天井論"),
        ("ASML", "ASML", "$1,505.6", 23.3, -24.1, "EUVを独占", "中国の内製化"),
        ("Vertiv", "VRT", "$207.7", 19.5, -44.8, "DC冷却・電源", "DC規制"),
        ("Microsoft", "MSFT", "$525.3", 11.8, -5.5, "AIの収益化", "投資削減報道"),
        ("東京エレクトロン", "8035", "¥9,304", 28.0, -40.5, "DRAM投資回復", "中国向け比率"),
        ("アドバンテスト", "6857", "¥29,985", 42.0, -28.4, "上方修正・自社株買い", "業績の集中"),
        ("キオクシア", "285A", "¥9,300", 146, -74.3, "NAND値上がり", "慎重な見通し"),
        ("フジクラ", "5803", "¥3,002", -1.1, -61.5, "DC向け光ファイバー", "DC投資減速"),
    ]
    tr = "".join(
        f"<tr><td><b>{n}</b></td><td>{c}</td><td class='r'>{p}</td><td class='r {'upc' if y>=0 else 'dn'}'>{y:+.1f}%</td><td class='r dn'>{'要確認' if d is None else f'{d:.1f}%'}</td><td>{b}</td><td>{r}</td></tr>"
        for n, c, p, y, d, b, r in rows)
    body = f"""
<div class="cols" style="grid-template-columns:1fr 1fr">
  <div class="span2">
    <h2><span class="n">1</span>注目12銘柄の比較</h2>
    <table class="t">
      <tr><th>銘柄</th><th>コード</th><th class="r">株価</th><th class="r">年初来</th><th class="r">高値比</th><th>買い材料</th><th>リスク</th></tr>
      {tr}
    </table>
    <p class="cap">米国株・日本株とも11/12終値（yfinance）。高値比は52週高値からの下落率。キオクシアは年初3,472円→6/22高値36,172円→9,300円と値動きが極端。マーベルは11/2のLumentum買収発表（株数+50%）で1週間に-28%。</p>
  </div>
  <div>
    <h2><span class="n">2</span>どこまで売られたか</h2>
    <div class="fig">{fig4}<div class="cap"><b>Fig.12</b> 52週高値からの下落率。※SKハイニックスは分割調整漏れの可能性あり。</div></div>
  </div>
  <div style="display:flex;flex-direction:column;gap:8px">
    <h2><span class="n">3</span>本命・対抗・大穴</h2>
    <div class="box tint"><h3>本命：装置・検査</h3><p class="small">東京エレクトロン（-47%）、アドバンテスト。AI投資の増額が見えれば遅れて業績に効きます。アドバンテストは上方修正と自社株買いで下値の支えがあります。</p></div>
    <div class="box tint"><h3>対抗：ファウンドリ・専用チップ</h3><p class="small">TSMC、ブロードコム。NVIDIAは後任CEOが決まるまで様子見。CEO辞任の日に+4.9%買われたブロードコムは、12/9の決算が材料です（Session 3-6）。</p></div>
    <div class="box tint2"><h3>大穴：メモリ・電力</h3><p class="small">Micron、フジクラ、Vertiv。戻る時の上昇率は最大ですが、選挙後の規制リスクと値動きの大きさから<b>小さく・分けて</b>持つ前提です。</p></div>
  </div>
  <div class="span2 small muted">
    参考（高値比、11/12）：AMAT -47%、LRCX -46%、ディスコ -46%、レーザーテック -36%、SCREEN -56%、ソフトバンクG -57%、さくらインターネット -26%、Alphabet -27%、Meta -20%、Palantir -19%、Constellation -27%。
  </div>
</div>"""
    out.append(sheet(2, 5, "売られすぎマップ：12銘柄の「下げ幅」と「戻る理由」", "高値からの下落率と材料・リスクを並べ、本命・対抗・大穴に分ける", body,
                     ["yfinance 株価・52週高値（2026/11/12終値、11/13取得）", "アドバンテスト 2026年10/28 適時開示（業績予想修正・自己株式取得）", "AMD 2026年Q3決算", "FourWeekMBA: AI memory stocks fell up to 26%"]))

    # ---------- 2-6 戦い方 ----------
    ev = [(0, "12/1頃|Marvell決算", False), (8, "12/9 FOMC", True), (9, "12/9-11|SEMICON Japan", False), (8.6, "12/9|Broadcom決算", True),
          (16, "12/16頃|Micron決算", True), (45, "1月中旬|TSMC決算", True), (57, "1/27 FOMC", False), (63, "1月末〜2月|大手4社決算", True),
          (72, "2月上旬|東エレク・アドテスト", False), (87, "2月下旬|NVIDIA決算", True), (106, "3/17 FOMC", False), (107, "3月中旬|NVIDIA GTC", True)]
    tl = timeline(ev, w=700, color=C, accent="#C1121F")
    alloc = hbar_chart(["GPU・ファウンドリ", "製造装置・検査", "メモリ", "電力・DC", "現金（押し目用）"], [30, 30, 10, 10, 20], colors=[C, C, A, A, "#9AA5B1"], fmt="{:.0f}%", w=330, row=21, label_w=104, vmax=40)
    body = f"""
<div class="fig">{tl}<div class="cap"><b>Fig.13</b> 12月〜3月の半導体関連イベント（日付は予定・例年ベースを含む※）。赤は相場を動かしやすいもの。11/17のNVIDIA決算は期間前の最重要イベント。</div></div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>3段階の押し目買いプラン</h2>
    <table class="t">
      <tr><th>段階</th><th>条件（SOX）</th><th>行動</th></tr>
      <tr><td style="white-space:nowrap"><b>Step 1</b></td><td>11/17決算後も9,011を割らない</td><td>予定額の1/3で打診買い（GPU・装置）</td></tr>
      <tr><td style="white-space:nowrap"><b>Step 2</b></td><td>200日線10,874を終値で回復</td><td>次の1/3。トレンド転換を確認</td></tr>
      <tr><td style="white-space:nowrap"><b>Step 3</b></td><td>1〜2月決算で2027年投資が増額</td><td>残り1/3。メモリ・電力も追加</td></tr>
      <tr><td><b class="dn">撤退</b></td><td>9,011を終値で割る</td><td>買い増し停止。Session 1の下値シナリオへ</td></tr>
    </table>
    <p class="small" style="margin-top:5px">Session 1で見た「日経48,000〜50,000円まで下げる」シナリオでは、半導体株はさらに下げる可能性が高いと考えます。<b>一度に全額を入れず、時間と価格を分けること</b>が退場しないための最低条件です。</p>
  </div>
  <div>
    <h2><span class="n">2</span>配分のたたき台（半導体・AI枠を100とした場合）</h2>
    <div class="fig">{alloc}<div class="cap"><b>Fig.14</b> 演者のたたき台。半導体・AI枠の内訳。現金20%は下値シナリオ時の買い増し用（資金全体の現金30%＝1-4とは別枠）。</div></div>
    <h2 style="margin-top:7px"><span class="n">3</span>主なリスク</h2>
    <ul class="b small">
      <li>2027年に大手4社がAI投資を鈍化させる（最大のリスク）</li>
      <li>NVIDIAの後任CEOが決まらず、経営の混乱が長引く</li>
      <li>民主党主導の議会でデータセンター優遇が縮小</li>
      <li>メモリ価格の天井、中国の追い上げと輸出規制</li>
      <li>金利上昇。日本株は円高と信用買い残の重さ</li>
    </ul>
  </div>
  <div class="span2">
    <h2><span class="n">4</span>段階ごとの買い候補</h2>
    <table class="t">
      <tr><th>段階</th><th>米国</th><th>日本</th><th>選ぶ理由</th></tr>
      <tr><td style="white-space:nowrap"><b>Step 1</b></td><td>TSMC、ブロードコム</td><td>東京エレクトロン</td><td>下げが浅く、見通しが確か。NVIDIAは後任CEOと11/17決算を見てから</td></tr>
      <tr><td style="white-space:nowrap"><b>Step 2</b></td><td>ASML、NVIDIA（新CEO決定後）</td><td>アドバンテスト、ディスコ</td><td>装置・検査は投資増額が見えた後に効く。自社株買いで下値も堅い</td></tr>
      <tr><td style="white-space:nowrap"><b>Step 3</b></td><td>Micron、Vertiv</td><td>キオクシア、フジクラ</td><td>戻る時の上昇率は最大。規制と値動きのリスクから最後に小さく</td></tr>
    </table>
  </div>
  <div class="span2 box tint">
    <h3>飲み会での論点</h3>
    <p class="small">① 今回の下げは2000年型か2022年型か　② NVIDIA決算の「合格ライン」はいくらか（売上108B$超え？　次期ガイダンス120B$？）　③ 日本株で一番戻りが大きいのは装置・検査・メモリ・電線のどれか</p>
  </div>
</div>"""
    out.append(sheet(2, 6, "12月〜3月の戦い方：3段階で分けて買い、撤退ラインを先に決める", "イベント日程・押し目買いの条件・配分のたたき台", body,
                     ["Federal Reserve: 2026-27 FOMC 日程", "SEMI: SEMICON Japan 2026（12/9-11）", "各社IR（決算発表予定日。例年ベースは要確認）", "Session 1 本資料（下値シナリオ）"]))
    return out
