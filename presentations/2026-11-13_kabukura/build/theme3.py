from kit import sheet, bar_chart, hbar_chart, line_chart, timeline

C, A, R = "#7E1A2C", "#B8860B", "#C1121F"


def stars(n):
    return f'<span class="stars">{"★" * n}<span style="color:#D5D9E1">{"★" * (5 - n)}</span></span>'


def pages():
    out = []
    # ---------- 3-1 ----------
    # 模式図：12月の平均-5.7%、年明けの反発（直近3年の期間中最大上昇+8.6〜12.0%）を目安にした形
    lab = ["11月末", "12/10", "12/20", "12/26", "1/10", "1/31", "2/15", "2/28", "3/15", "3/31"]
    path = [100, 97.5, 94.3, 95.8, 99.5, 103.5, 104.5, 102.0, 101.0, 99.0]
    fig = line_chart(lab, [(path, C, 2.4, "", "")], w=340, h=165, lo=92, hi=106, step=2, xticks=[0, 2, 4, 6, 9], pr=46,
                     hlines=[(94.3, "仕込み", R), (104.5, "利確", "#13803B")])
    tbl = [
        ("本命", "データセクション（3905）", "受注と業績が数字で見え始めた。高値から-74%、12月に米国案件が全面稼働", "ロケットラボ（RKLB）", "Neutron初号機（Q4目標）が成功すれば宇宙テーマの主役。業績も伸びている"),
        ("対抗", "メタプラネット（3350）", "時価総額が保有BTCの価値を下回る（mNAV 1倍割れ）。BTCが戻れば上げ幅は最大級", "スペースX（SPCX）", "12/9のロックアップ解除の売りを押し目買い。目標株価の平均は約$232"),
        ("大穴", "アクセルスペース（402A）", "公開価格375円の半値以下。損出し売りの反動を狙う", "オクロ（OKLO）", "年初来-67%。原子力・電力テーマの再燃と規制審査の進展で数倍も"),
    ]
    rows = "".join(f"<tr><td><span class='tag {'r' if k=='本命' else ('c' if k=='対抗' else 'g')}'>{k}</span></td><td><b>{j}</b><br><span class='small'>{jr}</span></td><td><b>{u}</b><br><span class='small'>{ur}</span></td></tr>" for k, j, jr, u, ur in tbl)
    body = f"""
<div class="cols">
  <div>
    <h2><span class="n">1</span>お年玉アノマリーの実態</h2>
    <ul class="b">
      <li><b>12月は損出し売りで弱い</b>：東証グロース250 ETFの12月は2018〜2025年で<b class="dn">7敗1勝</b>、平均<b class="dn">-5.7%</b>。最悪は2018年の-19.8%。</li>
      <li><b>年明けは戻しやすい</b>：同ETFの1月は8年中6年プラス。2018年12月に-19.8%下げた後、2019年1月は+8.9%。</li>
      <li><b>12/1〜3/31を通して持つと勝ちにくい</b>：期間でプラスは8年中3年だけ。ただし期間中の最大上昇は直近3年で<b class="upc">+8.6〜12.0%</b>。</li>
      <li><b>米国は「1月効果」が12月中旬に前倒し</b>：ラッセル2000の12/15〜31は平均+2.5%（1987〜2025年）。</li>
    </ul>
    <p class="small muted">集計：ETF（2516.T）・^RUT の終値から調査担当が算出。指数そのものの値ではありません。</p>
  </div>
  <div>
    <div class="fig">{fig}<div class="cap"><b>Fig.1</b> 小型グロース株の12〜3月の値動きの模式図（11月末=100）。12月の平均下落と年明けの最大上昇を目安に描いたイメージで、実データではありません。</div></div>
    <div class="box tint" style="margin-top:8px">
      <h3>今年の狙い方</h3>
      <p class="small">人気テーマ株は年初来で大きく下げています（メタプラネット-49%、OKLO-67%、ASTS-55%）。<b>損出し売りが大きいほど年明けの反発余地も大きい</b>と考えます。Session 1の下値シナリオ（日経48,000円）と重なれば、そこが絶好の仕込み場です。</p>
    </div>
  </div>
  <div class="span2">
    <h2><span class="n">2</span>応援3銘柄の早見表（詳細は3-2）</h2>
    <table class="t">
      <tr><th>銘柄</th><th class="r">株価</th><th class="r">高値からの下落</th><th>株価を動かすもの</th><th>買い場の目安</th></tr>
      <tr><td><b>メタプラネット（3350）</b></td><td class="r">237円</td><td class="r dn">-61%（613円比）</td><td>ビットコイン価格、mNAV</td><td>BTCの底打ち確認後</td></tr>
      <tr><td><b>データセクション（3905）</b></td><td class="r">1,583円</td><td class="r dn">-74%（6,140円比）</td><td>受注・中間決算・米国案件の稼働</td><td>決算を通過した12月の損出し局面</td></tr>
      <tr><td><b>スペースX（SPCX）</b></td><td class="r">$141.99</td><td class="r dn">-33%（$211比）</td><td>ロックアップ解除の需給、Starship</td><td>12/9のロックアップ解除後</td></tr>
    </table>
  </div>
  <div class="span2">
    <h2><span class="n">3</span>結論：本命・対抗・大穴</h2>
    <table class="t">
      <tr><th style="width:52px">区分</th><th>日本株</th><th>米国株</th></tr>
      {rows}
    </table>
  </div>
</div>"""
    out.append(sheet(3, 1, "お年玉は「12月中旬に仕込み、1〜2月に受け取る」", "損出し売りの反動を狙うアノマリーと、日米の本命・対抗・大穴", body,
                     ["楽天証券トウシル：東証グロース指数の12月・損出し売り", "Stock Trader's Almanac：Russell 2000 の12月後半", "yfinance：2516.T・1563.T・^RUT 終値から調査担当が集計", "各社IR・報道（銘柄ページ参照）"],
                     abstract="お年玉銘柄は年明けに上がる銘柄ではなく、12月の損出し売りで安くなった銘柄である。グロース株は12月に平均-5.7%下げ、1〜2月に戻しやすい。今年は人気テーマ株の下げが大きく、反発余地も大きい。応援銘柄のメタプラネット・データセクション・スペースXを含め、日米20銘柄を選んだ。",
                     kw="お年玉銘柄、損出し売り、1月効果、小型グロース、12/1〜3/31"))

    # ---------- 3-2 ----------
    def card(name, code, theme, price, kpis, bull, bear, cat, rate):
        k = "".join(f'<div class="kpi" style="padding:5px 6px"><div class="v" style="font-size:15px">{v}</div><div class="l">{l}</div></div>' for v, l in kpis)
        return f"""
<div style="display:flex;flex-direction:column;gap:6px;min-width:0">
  <div class="box tint" style="padding:8px 9px">
    <div class="small muted">{theme}</div>
    <div style="font-size:15px;font-weight:700;color:{C};line-height:1.3">{name}</div>
    <div class="small"><b>{code}</b>　{price}</div>
    <div class="small">暴騰度 {stars(rate)}</div>
  </div>
  <div class="kpis" style="grid-template-columns:1fr 1fr;gap:5px">{k}</div>
  <div><h3 class="upc">強気の材料</h3><ul class="b small">{''.join(f'<li>{b}</li>' for b in bull)}</ul></div>
  <div><h3 class="dn">リスク</h3><ul class="b small">{''.join(f'<li>{b}</li>' for b in bear)}</ul></div>
  <div class="box" style="padding:6px 8px"><h3>12〜3月のカタリスト</h3><ul class="b small">{''.join(f'<li>{b}</li>' for b in cat)}</ul></div>
</div>"""
    mp = card("メタプラネット", "3350", "ビットコイン保有企業", "237円（11/6）",
              [("2,954<small>億円</small>", "時価総額"), ("-49<small>%</small>", "年初来"), ("約4.4<small>万BTC</small>", "保有（Q3末）"), ("0.6<small>倍?</small>", "mNAV［推計］")],
              ["時価総額が保有BTCの価値を下回る。BTCが戻れば株価は大きく動きやすい", "目標は2026年末10万BTC、2027年末21万BTC", "信用格付けの取得、優先株での資金調達を進める"],
              ["mNAV 1倍未満では普通株で資金を集めにくく、買い増しが鈍る", "BTC下落で評価損（Q1は7.25億ドルの純損失）"],
              ["BTC価格（11/9時点 $75,129）", "年末目標への進捗（10万BTCは難しいと推計）", "2月の通期決算［日程要確認］"], 5)
    ds = card("データセクション", "3905", "AIデータセンター（GPUクラウド）", "1,583円（11/6）",
              [("701<small>億円</small>", "時価総額"), ("-74<small>%</small>", "5/29高値6,140円比"), ("1,622<small>億円</small>", "今期売上予想（前期336）"), ("125<small>億円</small>", "今期経常予想（前期36）")],
              ["9/18に米AIインフラ企業から5年で約1,399億円の大口契約", "10月に豪州でGPU1万個規模の利用枠を受注（最大5年・2,000億円規模と報道）", "Q1経常50億円で通期予想に対する進捗40%"],
              ["Q1の利益は一括収入が中心。通期予想を支える正式受注はまだ不足との指摘", "GPU購入の資金調達による希薄化、顧客の集中"],
              ["11月中旬の中間決算［日程要確認］", "12月に米国案件が全面稼働", "追加受注（GPU10万〜30万個規模への拡張が目標）"], 5)
    sx = card("スペースX", "SPCX（NASDAQ）", "宇宙・衛星通信・AI", "$141.99（11/9）",
              [("1.93<small>兆$</small>", "時価総額"), ("+5<small>%</small>", "公開価格$135比（上場初日比は-12%）"), ("$232", "目標株価の平均※"), ("$108", "52週安値")],
              ["6/12上場、史上最大のIPO（調達約750億ドル）。7/7にNASDAQ100採用", "Q2売上78億ドル（前年比+92%）。Starlinkが収益の柱", "Starship初の有償ミッション（Starlink V3を26基）"],
              ["12/9に180日ロックアップの一部解除予定※。需給悪化に注意", "AI関連の設備投資が利益を圧迫。Q3は黒字/赤字の報道が分かれる"],
              ["12/9 ロックアップ解除後の押し目", "Starshipの打ち上げ", "Q4決算（1〜2月）。S&amp;P500採用は早くても2027年6月以降"], 3)
    body = f"""
<div class="box tint2 small">発表者が応援する3銘柄です。いずれも高値から大きく下げており、<b>12月の損出し売りとSession 1の下値シナリオが重なる局面が仕込み候補</b>になります。数値は11/6（日本株）・11/9（米国株）時点、yfinance と各社IR・報道から。</div>
<div class="cols3" style="gap:12px">{mp}{ds}{sx}</div>
<div class="box">
  <h3>3銘柄の共通点と違い</h3>
  <p class="small">共通点は<b>「テーマの主役」かつ「高値から大きく下げた」</b>こと。違いは値動きの源です。メタプラネットはBTC価格、データセクションは受注と決算、スペースXは需給（ロックアップ）とStarshipの成否で動きます。<b>動く理由が違うので、3つに分けて持つと分散になります</b>。</p>
</div>"""
    out.append(sheet(3, 2, "応援銘柄3選：メタプラネット・データセクション・スペースX", "それぞれの現状・強気材料・リスク・12〜3月のカタリスト", body,
                     ["The Block: Metaplanet sold 10,000 BTC in Q3（2026/10/5）", "JIO Invest Leaders / かぶ予報：データセクション", "NPR: SpaceX IPO（2026/6/11）", "Fortune: SpaceX lockup expiration（2026/8/5）", "RTTNews: SpaceX Q3", "yfinance 株価・時価総額"]))

    # ---------- 3-3 ----------
    jp = [
        ("3350", "メタプラネット", "ビットコイン", 237, "2,954億", -49, "BTC反発、年末保有目標", "BTC下落、mNAV<1", 5, True),
        ("3905", "データセクション", "AIデータセンター", 1583, "701億", -25, "中間決算、追加受注", "受注の確度、希薄化", 5, True),
        ("285A", "キオクシア", "AI・NAND", 8511, "13.3兆", 145, "AI需要、決算", "高値から-76%", 3, False),
        ("3778", "さくらインターネット", "GPUクラウド", 2715, "1,124億", -2, "政府クラウド、GPU案件", "先行投資の負担", 3, False),
        ("9348", "ispace", "宇宙（月）", 335, "508億", -28, "補助金・受注", "次の大きな材料まで遠い", 4, False),
        ("186A", "アストロスケール", "宇宙（デブリ除去）", 959, "1,404億", 39, "ミッションの進捗", "赤字が続く", 3, False),
        ("402A", "アクセルスペース", "宇宙（IPO後）", 179, "123億", -65, "衛星打ち上げ・受注", "公開価格375円を大きく下回る", 4, False),
        ("6208", "石川製作所", "防衛（小型）", 1402, "89億", -8, "防衛予算、地政学", "テーマ頼みの値動き", 4, False),
        ("7711", "助川電気", "核融合", 3620, "210億", -42, "核融合の国家戦略", "小型で値動きが荒い", 4, False),
        ("3687", "フィックスターズ", "量子・AI", 1555, "531億", 1, "量子関連のニュース", "テーマ一巡で下落", 3, False),
    ]
    tr = "".join(
        f"<tr{' style=\"background:#FBF3E4\"' if fav else ''}><td class='c'>{i+1}</td><td><b>{n}</b><br><span class='muted small'>{c}</span>{' <span class=\"tag\">推し</span>' if fav else ''}</td><td>{t}</td><td class='r'>{p:,}</td><td class='r'>{m}</td><td class='r {'upc' if y>=0 else 'dn'}'>{y:+d}%</td><td>{k}</td><td>{r}</td><td>{stars(s)}</td></tr>"
        for i, (c, n, t, p, m, y, k, r, s, fav) in enumerate(jp))
    yt = hbar_chart([j[1] for j in jp], [abs(j[5]) for j in jp], colors=[R if j[5] < 0 else "#13803B" for j in jp], fmt="{:.0f}%", w=330, row=16.5, label_w=104, vmax=140, note="■下落 ■上昇（年初来）")
    body = f"""
<table class="t">
  <tr><th class="c">#</th><th>銘柄</th><th>テーマ</th><th class="r">株価</th><th class="r">時価総額</th><th class="r">年初来</th><th>カタリスト</th><th>リスク</th><th>暴騰度</th></tr>
  {tr}
</table>
<p class="cap">株価は11/6終値（円）、時価総額は yfinance。テーマが偏らないよう、ビットコイン・AI・宇宙・防衛・核融合・量子に分散。補欠：古河電工（5801、AI向け電力・光）、三菱重工（7011、防衛の大型株）。</p>
<div class="cols">
  <div class="fig">{yt}<div class="cap"><b>Fig.2</b> 10銘柄の年初来騰落率（絶対値で表示、赤=下落）。下げた銘柄ほど損出し売りの対象になりやすい。</div></div>
  <div>
    <h2><span class="n">1</span>選び方の3つの基準</h2>
    <ul class="b">
      <li><b>テーマの主役であること</b>：相場が戻る時に最初に買われるのは、その年の人気テーマの中心銘柄です。</li>
      <li><b>高値から大きく下げていること</b>：10銘柄中6銘柄が52週安値の近くにあります（ispace、アクセルスペース、石川製作所、助川電気など）。</li>
      <li><b>12〜3月に材料があること</b>：決算、受注、打ち上げ、政策（防衛予算・核融合戦略）。</li>
    </ul>
    <div class="box tint2" style="margin-top:6px"><p class="small">時価総額100億円前後の小型株は、1日で±20%動くこともあります。<b>1銘柄あたりの金額を小さく、10銘柄に分けて</b>持つのが「暴騰候補」との付き合い方です。</p></div>
  </div>
</div>"""
    out.append(sheet(3, 3, "日本株10選：12/1〜3/31の最大暴騰候補", "応援銘柄2つを含め、テーマを分散して選んだ10銘柄", body,
                     ["yfinance：株価・時価総額・52週高安（2026/11/6終値）", "各社IR・適時開示", "報道（ispace・アストロスケール・アクセルスペース・助川電気ほか）"]))

    # ---------- 3-4 ----------
    us = [
        ("SPCX", "スペースX", "宇宙・AI", 141.99, "1.93兆", -12, "12/9後の押し目、Starship", "需給悪化", 3, True),
        ("RKLB", "ロケットラボ", "宇宙", 59.21, "379億", -22, "Neutron初号機（Q4目標）", "再延期", 4, False),
        ("ASTS", "ASTスペースモバイル", "衛星通信", 37.93, "114億", -55, "BlueBird衛星の展開", "打上げ失敗", 5, False),
        ("IONQ", "アイオンキュー", "量子", 35.35, "164億", -24, "技術発表", "割高感", 4, False),
        ("QBTS", "Dウェーブ", "量子（小型）", 11.40, "43億", -60, "量子相場の再燃", "増資", 5, False),
        ("OKLO", "オクロ", "原子力", 26.04, "51億", -67, "規制審査、試験炉", "売上ゼロ", 5, False),
        ("MSTR", "ストラテジー", "ビットコイン", 128.20, "543億", -18, "BTC反発", "BTC下落", 4, False),
        ("IREN", "アイレン", "AI・BTCマイニング", 22.06, "94億", -48, "AIクラウド契約", "BTC・投資負担", 4, False),
        ("NBIS", "ネビウス", "AIクラウド", 140.27, "381億", 56, "大型契約", "高値の半値", 3, False),
        ("LUNR", "インテュイティブ・マシーンズ", "月・宇宙（小型）", 11.90, "19億", -33, "NASA契約※", "ミッション失敗", 5, False),
    ]
    tr = "".join(
        f"<tr{' style=\"background:#FBF3E4\"' if fav else ''}><td class='c'>{i+1}</td><td><b>{n}</b><br><span class='muted small'>{c}</span>{' <span class=\"tag\">推し</span>' if fav else ''}</td><td>{t}</td><td class='r'>${p:,.2f}</td><td class='r'>${m}</td><td class='r {'upc' if y>=0 else 'dn'}'>{y:+d}%</td><td>{k}</td><td>{r}</td><td>{stars(s)}</td></tr>"
        for i, (c, n, t, p, m, y, k, r, s, fav) in enumerate(us))
    ev = [(0, "12/1|師走入り", False), (8, "12/9|SPCXロック解除・FOMC", True), (14, "12月中旬|損出し売りピーク", True),
          (26, "12/26頃|年内受渡最終日", True), (34, "1/4|大発会", False), (60, "1月末|大手決算", False), (84, "2月下旬|NVIDIA決算", False), (118, "3/31|期間終了", True)]
    tl = timeline(ev, w=700, color=C, accent=R)
    vote = "".join(f"<div>{h}</div>" for h in ["名前", "日本株1位", "米国株1位", "3/31日経"]) + "".join("<div></div>" for _ in range(16))
    body = f"""
<table class="t">
  <tr><th class="c">#</th><th>銘柄</th><th>テーマ</th><th class="r">株価</th><th class="r">時価総額</th><th class="r">年初来</th><th>カタリスト</th><th>リスク</th><th>暴騰度</th></tr>
  {tr}
</table>
<p class="cap">株価は11/9取引時間中、時価総額はドル（yfinance）。SPCXの年初来は上場初日終値比（公開価格$135比では+5%）。参考：BTC $75,129。</p>
<div class="fig">{tl}<div class="cap"><b>Fig.3</b> 暴騰候補の「仕込み〜利確」カレンダー（12/1〜3/31）。赤は需給が大きく動く日。12月中旬〜年内受渡最終日に仕込み、1〜2月の戻りで利確するのが基本形。</div></div>
<div class="cols" style="grid-template-columns:1fr 1.15fr">
  <div>
    <h2><span class="n">1</span>米国株の選び方</h2>
    <ul class="b small">
      <li><b>宇宙</b>：SPCX・RKLB・ASTS・LUNR。SPCXが相場の旗振り役で、12/9の需給を通過すれば周辺も動きやすい。</li>
      <li><b>量子・原子力</b>：IONQ・QBTS・OKLO。年初来-24〜-67%と下げが深く、反発の上げ幅も大きい。</li>
      <li><b>BTC・AIクラウド</b>：MSTR・IREN・NBIS。メタプラネットと同じくBTCとAI投資の向きで動く。</li>
    </ul>
  </div>
  <div>
    <h2><span class="n">2</span>飲み会の当てっこシート（3/31に答え合わせ）</h2>
    <div class="vote">{vote}</div>
    <p class="cap">20銘柄から12/1終値→3/31終値の上昇率1位を予想。賞品は次回の飲み会で。</p>
  </div>
</div>"""
    out.append(sheet(3, 4, "米国株10選と「仕込み〜利確」カレンダー", "応援銘柄スペースXを含む10銘柄と、12/1〜3/31の売買タイミング", body,
                     ["yfinance：株価・時価総額（2026/11/9取引時間中）", "Finviz: Rocket Lab Q3 / Neutron", "Webull: Oklo", "Fortune: SpaceX lockup（2026/8/5）"]))
    return out
