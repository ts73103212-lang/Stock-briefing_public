from kit import sheet, bar_chart, hbar_chart, timeline

C, A = "#0B4F5C", "#0E9C9C"


def pages():
    out = []
    # ---------- 2-1 ----------
    fig1 = bar_chart(["2000-02|ITバブル".split("|")[0], "2008|金融危機".split("|")[0], "2022|利上げ".split("|")[0], "2026|今回"], [-80, -60, -45, -38],
                     colors=["#9AA5B1", "#9AA5B1", "#9AA5B1", "#C1121F"], fmt="{:.0f}%", w=330, h=150, ymin=-90, ymax=0)
    body = f"""
<div class="kpis">
  <div class="kpi"><div class="v">10,003</div><div class="l">SOX指数（11/9取引中）<br>11/5に1日で-12.3%</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-38<small>%</small></div><div class="l">6/22高値14,634→11/5安値<br>9,011。弱気相場入り</div></div>
  <div class="kpi"><div class="v">+8<small>%</small></div><div class="l">200日線10,841までの距離<br>回復＝トレンド転換の目安</div></div>
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
    </ul>
    <h2 style="margin-top:6px"><span class="n">2</span>それでも業績は過去最高</h2>
    <ul class="b">
      <li>NVIDIAの今期売上ガイダンスは<b>108B$</b>（市場予想は約104B$）。前四半期のデータセンター売上は前年比+117%。</li>
      <li>AMDのQ3売上は+45%。アドバンテストは通期営業利益見通しを<b>9,670億円</b>に上方修正し、2,800億円の自社株買いも決めました。</li>
      <li>Metaは2026年のAI投資を125〜145B$に引き上げ。アマゾン・アルファベットは「2027年はさらに大幅増」と発言しています。</li>
    </ul>
  </div>
  <div>
    <div class="fig">{fig1}<div class="cap"><b>Fig.1</b> SOX指数の高値からの最大下落率（過去の大相場との比較）。2008年は概算［要確認］。今回は11/5安値まで。</div></div>
    <div class="box tint" style="margin-top:8px">
      <h3>本セッションの問い</h3>
      <p class="small">今回の下げは2000年型（需要そのものが消える）か、2022年型（金利とバリュエーションの調整）か。演者は<b>「株価は売られたが、事業は売られていない」2022年型に近い</b>と考えます。ただし政治（データセンター規制）という新しいリスクが加わった点は2022年と違います。</p>
    </div>
    <div class="box" style="margin-top:8px">
      <h3>巻き返しの3条件</h3>
      <ul class="b small">
        <li><span class="em">①</span> 11/17 NVIDIA決算で「108B$超え＋強気の次期ガイダンス」</li>
        <li><span class="em">②</span> SOXが200日線（10,841）を終値で回復</li>
        <li><span class="em">③</span> 1〜2月の大手決算で2027年AI投資の増額が見える</li>
      </ul>
    </div>
  </div>
  <div class="span2">
    <h2><span class="n">3</span>SOX指数の節目</h2>
    <table class="t">
      <tr><th>節目</th><th class="r">水準</th><th class="r">現在値10,003から</th><th>意味</th></tr>
      <tr><td>6/22 年初来高値</td><td class="r">14,634</td><td class="r upc">+46.3%</td><td>ここまで戻れば「完全回復」。2027年のAI投資増額が前提</td></tr>
      <tr><td>75日線</td><td class="r">11,709</td><td class="r upc">+17.1%</td><td>中期の上値メド。戻り売りが出やすい</td></tr>
      <tr><td><b>200日線</b></td><td class="r"><b>10,841</b></td><td class="r upc"><b>+8.4%</b></td><td><b>回復＝トレンド転換の合図（巻き返しの条件②）</b></td></tr>
      <tr><td>11/5 安値</td><td class="r">9,011</td><td class="r dn">-9.9%</td><td>割れたら2番底を探る展開。撤退ライン</td></tr>
    </table>
  </div>
</div>"""
    out.append(sheet(2, 1, "半導体は「弱気相場」入り、それでも業績は過去最高", "高値から-38%の調整は2000年型か2022年型か。巻き返しの3条件を考える", body,
                     ["newsbytesapp: SOX in bear territory (2026/11)", "Fortune: chip stocks volatility (2026/8/2)", "Al Jazeera: midterms and data centres (2026/11/7)", "NVIDIA IR: Q3 FY27 conference call (11/17)", "インテル決算報道（2026/10/30）", "yfinance 株価・移動平均（11/9取得）"],
                     abstract="SOX指数は6月の高値14,634から11/5の9,011まで約38%下落し、弱気相場に入った。理由はAI投資の回収への疑問、インテル決算、中間選挙後のデータセンター規制懸念である。一方で主要企業の業績とAI投資計画は上方修正が続く。株価と業績の差が、巻き返しの余地になる。",
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
      <tr><td><b>GPU / ASIC</b></td><td>AIの計算</td><td>NVIDIA, Broadcom, AMD</td><td>ソシオネクスト</td><td>11/17決算が最大の材料。ASICは2027年に60〜90B$の市場</td></tr>
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
    <div class="fig">{capex}<div class="cap"><b>Fig.2</b> 米大手4社の2026年AI投資計画（B$=10億ドル、レンジは中央値）。※マイクロソフトは暦年換算の二次情報［要確認］。</div></div>
  </div>
  <div>
    <h2><span class="n">3</span>市場規模は2年で倍以上</h2>
    <p>WSTS（世界半導体市場統計）の2026年春季予測では、2026年は<b>1.51兆$（+89.9%）</b>、2027年は約1.9兆$（+26.6%）。メモリだけで2027年に1.06兆$です。</p>
    <div class="fig">{wsts}<div class="cap"><b>Fig.3</b> 世界半導体市場の予測（WSTS 2026年6月）。2025年は2026年の伸び率から逆算。秋季予測は12月公表予定。</div></div>
  </div>
  <div class="span2 box tint2">
    <h3>演者の見方：今は「受け取る側」の株価だけが先に崩れた</h3>
    <p class="small">払う側（大手4社）は投資計画を下げていません。にもかかわらず、受け取る側の半導体株は高値から2〜6割下げています。<b>1〜2月の大手決算で2027年の投資額が示された時</b>が、この差が埋まるかどうかの分かれ目です。逆に投資額の伸びが鈍れば、装置・メモリ・電力の順に下げが深くなる点に注意します。</p>
  </div>
</div>"""
    out.append(sheet(2, 2, "AIのお金の流れ：払う側は減らさず、受け取る側の株価だけが下げた", "バリューチェーン8層と、需要を決める米大手4社のAI投資", body,
                     ["WSTS 2026年春季予測（JEITA, 2026/6/2）", "DatacenterDynamics: Moody's hyperscaler capex forecasts", "各社決算資料（Meta, Amazon, Alphabet 2026年Q3）", "Broadcom 決算説明（ASIC市場機会）"]))

    # ---------- 2-3 ----------
    names = ["キオクシア※", "フジクラ", "SKハイニックス※", "SCREEN", "ソフトバンクG", "ディスコ", "LRCX", "AMAT", "東京エレクトロン", "Vertiv", "Micron", "レーザーテック", "Broadcom", "アドバンテスト", "NVIDIA", "TSMC", "MSFT"]
    dd = [76.5, 62.1, 61.2, 59.9, 58.8, 53.7, 49.7, 49.3, 47.2, 46.3, 39.1, 44.0, 33.5, 33.1, 26.2, 19.3, 2.7]
    pairs = sorted(zip(names, dd), key=lambda p: -p[1])
    names, dd = [p[0] for p in pairs], [p[1] for p in pairs]
    jp = {"キオクシア※", "フジクラ", "SCREEN", "ソフトバンクG", "ディスコ", "東京エレクトロン", "レーザーテック", "アドバンテスト"}
    fig4 = hbar_chart(names, dd, colors=[A if n in jp else C for n in names], fmt="-{:.0f}%", w=300, row=17.2, label_w=96, vmax=88, note="■日本 ■米国ほか")
    rows = [
        ("NVIDIA", "NVDA", "$176.5", -5.1, -26.2, "11/17決算・Rubin量産", "大手の自社チップ化"),
        ("Broadcom", "AVGO", "$319.2", -7.3, -33.5, "カスタムASIC", "AI見通しへの失望"),
        ("AMD", "AMD", "$501.2", 134, -22.8, "Q3売上+45%", "上昇後の利益確定"),
        ("TSMC", "TSM", "$392.2", 30.1, -19.3, "先端品を独占", "台湾・関税"),
        ("Micron", "MU", "$738.8", 159, -39.1, "HBMの品薄", "メモリ価格の天井論"),
        ("ASML", "ASML", "$1,511.6", 42.2, -23.8, "EUV装置を独占", "中国の内製化"),
        ("Vertiv", "VRT", "$201.8", 24.7, -46.3, "DCの冷却・電源", "選挙後のDC規制"),
        ("Microsoft", "MSFT", "$540.8", 12.5, -2.7, "AIの収益化", "投資削減の報道"),
        ("東京エレクトロン", "8035", "¥8,263", 22.4, -47.2, "DRAM投資の回復", "中国向け比率"),
        ("アドバンテスト", "6857", "¥28,015", 43.1, -33.1, "上方修正・自社株買い", "業績の集中"),
        ("キオクシア", "285A", "¥8,511", 145, None, "NAND値上がり", "慎重な見通し"),
        ("フジクラ", "5803", "¥2,962", 2.8, -62.1, "DC向け光ファイバー", "DC投資の減速"),
    ]
    tr = "".join(
        f"<tr><td><b>{n}</b></td><td>{c}</td><td class='r'>{p}</td><td class='r {'upc' if y>=0 else 'dn'}'>{y:+.1f}%</td><td class='r dn'>{'要確認' if d is None else f'{d:.1f}%'}</td><td>{b}</td><td>{r}</td></tr>"
        for n, c, p, y, d, b, r in rows)
    body = f"""
<div class="cols" style="grid-template-columns:1.25fr 1fr">
  <div>
    <h2><span class="n">1</span>注目12銘柄の比較</h2>
    <table class="t">
      <tr><th>銘柄</th><th>コード</th><th class="r">株価</th><th class="r">年初来</th><th class="r">高値比</th><th>買い材料</th><th>リスク</th></tr>
      {tr}
    </table>
    <p class="cap">米国株は11/9取引時間中、日本株は11/6終値（yfinance）。キオクシアの高値比は株式分割の調整漏れの可能性があり要確認。</p>
  </div>
  <div>
    <h2><span class="n">2</span>どこまで売られたか</h2>
    <div class="fig">{fig4}<div class="cap"><b>Fig.4</b> 年初来高値からの下落率。※キオクシア・SKハイニックスは分割調整漏れの可能性［要確認］。</div></div>
  </div>
  <div class="span2">
    <div class="cols3">
      <div class="box tint"><h3>本命：装置・検査</h3><p class="small">東京エレクトロン（-47%）、アドバンテスト。AI投資の増額が見えれば遅れて業績に効きます。アドバンテストは上方修正と自社株買いで下値の支えがあります。</p></div>
      <div class="box tint"><h3>対抗：GPU・ファウンドリ</h3><p class="small">NVIDIA、TSMC。下げは比較的浅く、11/17決算という分かりやすい材料があります。決算で反発しなければ、全体の底入れはまだ先と判断します。</p></div>
      <div class="box tint2"><h3>大穴：メモリ・電力</h3><p class="small">Micron、フジクラ、Vertiv。戻る時の上昇率は最大ですが、選挙後の規制リスクと値動きの大きさから<b>小さく・分けて</b>持つ前提です。</p></div>
    </div>
  </div>
  <div class="span2 small muted">
    参考（高値比）：AMAT -49%、Lam -50%、ディスコ -54%、レーザーテック -44%、SCREEN -60%、ソフトバンクG -59%、さくらインターネット -37%、Alphabet -27%、Meta -18%、Palantir -19%、Constellation -26%。
  </div>
</div>"""
    out.append(sheet(2, 3, "売られすぎマップ：12銘柄の「下げ幅」と「戻る理由」", "高値からの下落率と材料・リスクを並べ、本命・対抗・大穴に分ける", body,
                     ["yfinance 株価・52週高値（2026/11/6・11/9取得）", "アドバンテスト 2026年10/28 適時開示（業績予想修正・自己株式取得）", "AMD 2026年Q3決算", "FourWeekMBA: AI memory stocks fell up to 26%"]))

    # ---------- 2-4 ----------
    ev = [(0, "12/1|師走入り", False), (8, "12/9 FOMC", True), (9, "12/9-11|SEMICON Japan", False), (10, "12/10頃|Broadcom決算", False),
          (16, "12/16頃|Micron決算", True), (45, "1月中旬|TSMC決算", True), (57, "1/27 FOMC", False), (63, "1月末〜2月|大手4社決算", True),
          (72, "2月上旬|東エレク・アドテスト", False), (87, "2月下旬|NVIDIA決算", True), (106, "3/17 FOMC", False), (107, "3月中旬|NVIDIA GTC", True)]
    tl = timeline(ev, w=700, h=104, color=C, accent="#C1121F")
    alloc = hbar_chart(["GPU・ファウンドリ", "製造装置・検査", "メモリ", "電力・DC", "現金（押し目用）"], [30, 30, 10, 10, 20], colors=[C, C, A, A, "#9AA5B1"], fmt="{:.0f}%", w=330, row=21, label_w=104, vmax=40)
    body = f"""
<div class="fig">{tl}<div class="cap"><b>Fig.5</b> 12月〜3月の半導体関連イベント（日付は予定・例年ベースを含む［要確認］）。赤は相場を動かしやすいもの。11/17のNVIDIA決算は期間前の最重要イベント。</div></div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>3段階の押し目買いプラン</h2>
    <table class="t">
      <tr><th>段階</th><th>条件（SOX）</th><th>行動</th></tr>
      <tr><td><b>Step 1</b></td><td>11/17決算後も<br>9,011を割らない</td><td>予定額の1/3で打診買い（GPU・装置）</td></tr>
      <tr><td><b>Step 2</b></td><td>200日線10,841を<br>終値で回復</td><td>次の1/3。トレンド転換を確認</td></tr>
      <tr><td><b>Step 3</b></td><td>1〜2月決算で<br>2027年投資が増額</td><td>残り1/3。メモリ・電力も追加</td></tr>
      <tr><td><b class="dn">撤退</b></td><td>9,011を終値で割る</td><td>買い増し停止。Session 1の下値シナリオへ</td></tr>
    </table>
    <p class="small" style="margin-top:5px">Session 1で見た「日経48,000円まで下げる」シナリオでは、半導体株はさらに下げる可能性が高いと考えます。<b>一度に全額を入れず、時間と価格を分けること</b>が退場しないための最低条件です。</p>
  </div>
  <div>
    <h2><span class="n">2</span>配分のたたき台（半導体・AI枠を100とした場合）</h2>
    <div class="fig">{alloc}<div class="cap"><b>Fig.6</b> 演者のたたき台。現金20%は下値シナリオ時の買い増し用に残す。</div></div>
    <h2 style="margin-top:7px"><span class="n">3</span>主なリスク</h2>
    <ul class="b small">
      <li>2027年に大手4社がAI投資を鈍化させる（最大のリスク）</li>
      <li>民主党主導の議会でデータセンター優遇が縮小</li>
      <li>メモリ価格の天井、中国の追い上げと輸出規制</li>
      <li>金利上昇。日本株は円高と信用買い残の重さ</li>
    </ul>
  </div>
  <div class="span2">
    <h2><span class="n">4</span>段階ごとの買い候補</h2>
    <table class="t">
      <tr><th>段階</th><th>米国</th><th>日本</th><th>選ぶ理由</th></tr>
      <tr><td><b>Step 1</b></td><td>NVIDIA、TSMC</td><td>東京エレクトロン</td><td>下げが比較的浅く、業績の見通しが最も確か。決算で方向が早く出る</td></tr>
      <tr><td><b>Step 2</b></td><td>ASML、Broadcom</td><td>アドバンテスト、ディスコ</td><td>装置・検査は投資増額が見えた後に効く。自社株買いで下値も堅い</td></tr>
      <tr><td><b>Step 3</b></td><td>Micron、Vertiv</td><td>キオクシア、フジクラ</td><td>戻る時の上昇率は最大。規制と値動きのリスクから最後に小さく</td></tr>
    </table>
  </div>
  <div class="span2 box tint">
    <h3>飲み会での論点</h3>
    <p class="small">① 今回の下げは2000年型か2022年型か　② NVIDIA決算の「合格ライン」はいくらか（売上108B$超え？　次期ガイダンス120B$？）　③ 日本株で一番戻りが大きいのは装置・検査・メモリ・電線のどれか</p>
  </div>
</div>"""
    out.append(sheet(2, 4, "12月〜3月の戦い方：3段階で分けて買い、撤退ラインを先に決める", "イベント日程・押し目買いの条件・配分のたたき台", body,
                     ["Federal Reserve: 2026-27 FOMC 日程", "SEMI: SEMICON Japan 2026（12/9-11）", "各社IR（決算発表予定日。例年ベースは要確認）", "Session 1 本資料（下値シナリオ）"]))
    return out
