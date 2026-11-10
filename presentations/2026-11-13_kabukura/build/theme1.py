import json
from pathlib import Path

from kit import sheet, bar_chart, line_chart, scenario_bar, timeline
from annot import Chart, YEL, PINK, CYAN, WHITE, GREEN

C, A = "#1D3557", "#C1121F"
HERE = Path(__file__).parent


def pages():
    out = []
    # ---------- 1-1 ----------
    sox = bar_chart(["11/4", "11/5", "11/6", "11/9"], [-3.13, -12.3, 4.21, 6.86], w=330, h=150, ymin=-14, ymax=8, fmt="{:+.1f}%")
    body = f"""
<div class="kpis">
  <div class="kpi"><div class="v">54<small>対</small>44</div><div class="l">上院（民主対共和）<br>選挙前は共和53対民主47</div></div>
  <div class="kpi"><div class="v">228<small>対</small>139</div><div class="l">下院（民主対共和）<br>民主が19議席増・一部未確定</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-4.36<small>%</small></div><div class="l">11/5 S&amp;P500<br>NASDAQ -5.52%、VIX 28.8</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-3,643<small>円</small></div><div class="l">11/6 日経平均（57,435円）<br>下げ幅は歴代3位級</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>選挙後1週間に起きたこと</h2>
    <table class="t">
      <tr><th>日付</th><th>出来事と値動き</th></tr>
      <tr><td><b>11/3</b></td><td>中間選挙。投票数1.24億票超で中間選挙として過去最多。民主党が上下両院を制する</td></tr>
      <tr><td><b>11/4</b></td><td><span class="upc">安心ラリー</span>。「ねじれ議会なら政策のサプライズが減る」とダウ+1,569ドル（+3.03%）。ただしSOXは-3.1%</td></tr>
      <tr><td><b>11/5</b></td><td><span class="dn">急落</span>。テキサス州知事選で「データセンター建設の即時停止」を掲げた民主党候補が勝利。SOX -12.3%、NVIDIAは1日で時価総額4,000億ドル超を失う</td></tr>
      <tr><td><b>11/6</b></td><td><span class="dn">東京に波及</span>。日経は一時4,300円超安の56,745円。プライム市場の98%が値下がり、売買代金12.5兆円</td></tr>
      <tr><td><b>11/9〜10</b></td><td>2日続伸。11/10は<span class="upc">60,459円</span>で6万円台を回復。同日引け後、ソフトバンクGが中間赤字7,680億円を発表し、夜間取引で-8%</td></tr>
    </table>
    <h2 style="margin-top:7px"><span class="n">2</span>政策はどう変わるか</h2>
    <ul class="b">
      <li><b>関税は続く</b>：民主党は大統領の拒否権を覆せる3分の2に届かない。関税は大統領令で続く可能性が高い。</li>
      <li><b>減税の延長は難しくなる</b>：財政は「ねじれ」で動きにくい。</li>
      <li><b>AI・データセンターに逆風</b>：住民投票は41件中40件が否決。電力料金の高騰が争点になった。</li>
    </ul>
    <h2 style="margin-top:7px"><span class="n">3</span>主要指数の現在地</h2>
    <table class="t">
      <tr><th>指数</th><th class="r">現在値</th><th class="r">200日線比</th><th class="r">高値比</th></tr>
      <tr><td>日経平均（11/10）</td><td class="r">60,459</td><td class="r dn">-2.5%</td><td class="r dn">-16.5%</td></tr>
      <tr><td>S&amp;P500（11/9）</td><td class="r">7,550</td><td class="r upc">+3.0%</td><td class="r dn">-3.4%</td></tr>
      <tr><td>NASDAQ100（11/9）</td><td class="r">27,908</td><td class="r dn">-0.3%</td><td class="r dn">-10.6%</td></tr>
      <tr><td>SOX（11/9）</td><td class="r">10,034</td><td class="r dn">-7.5%</td><td class="r dn">-31.4%</td></tr>
    </table>
    <p class="cap">終値。200日線・高値はyfinance（11/9取得）。反発でS&amp;P500とNASDAQ100は200日線付近まで戻した。日経とSOXはまだ下。</p>
  </div>
  <div>
    <div class="fig">{sox}<div class="cap"><b>Fig.1</b> 選挙後のSOX指数（米半導体株）の日次騰落率。11/5の-12.3%は2020年3月以来の最悪級。11/9は終値（10,034）。</div></div>
    <div class="box tint" style="margin-top:8px">
      <h3>本セッションの結論</h3>
      <p class="small">歴史的には「中間選挙の後の1年は株高」（1950年以降19戦19勝）です。演者もメインシナリオは<b>春に向けた回復</b>と考えます。<br>ただしそれは<b>途中の下げを生き残った人だけ</b>が受け取れるリターンです。X上では「ここから一旦<b class="dn">48,000〜50,000円</b>まで下げる」という見方もあり、演者（櫻庭）もこれは<b>想定しておくべきライン</b>だと考えます。そのうえで資金とレバレッジをどう管理するかが本日の主題です。</p>
    </div>
    <div class="box" style="margin-top:8px">
      <h3>マクロの現在地（11/9）</h3>
      <p class="small">米10年債4.89%／FF金利3.75〜4.00%（12月利上げ確率 約88%）／ドル円158円台（介入警戒）／WTI 90ドル台（イラン情勢・ホルムズ海峡）／米Q3 GDP +3.4%</p>
    </div>
  </div>
</div>"""
    out.append(sheet(1, 1, "民主党が上下両院を奪還：選挙後1週間で何が起きたか", "安心ラリーから一転、AIデータセンター規制への懸念で世界的な株安へ", body,
                     ["OPB/NPR: 2026 midterms, Democrats win the Senate (11/4)", "LiveNOW from FOX: Democrats win control of Congress", "GV Wire: Markets cheer Democratic win (11/4)", "Al Jazeera: Tariffs to Iran war (11/4)", "みんかぶ: 日経平均 11/6 大引け", "Investinglive: Fed holds at 3.75-4%"],
                     abstract="11/3の米中間選挙で民主党が上下両院を制した。翌日は「ねじれ議会」を好感して上げたが、11/5にAIデータセンター規制への懸念から半導体株が急落し、11/6には日経平均が3,643円下げた。歴史的には選挙後は株高になりやすいが、今回は途中の大きな下げに耐えられるかが問われる。",
                     kw="中間選挙、ねじれ議会、関税、データセンター規制、SOX"))

    # ---------- 1-2 ----------
    years = [1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022]
    rets = [14, 33.2, 9, 26, 15, 11, 20, 8, 23, 1.1, 25.1, 27.1, 22, 16, 7, 4, 5, 11.7, 14.5]
    confirmed = {1954, 1986, 1990, 1994, 2018}
    cols = [C if y in confirmed else "#8DA2BF" for y in years]
    fig = bar_chart([f"'{str(y)[2:]}" for y in years], rets, colors=cols, w=700, h=170, ymin=0, ymax=36, fmt="{:.0f}", label_size=8.4, unit_note="単位：%")
    body = f"""
<div class="fig">{fig}<div class="cap"><b>Fig.2</b> 中間選挙の投票日から1年後のS&amp;P500騰落率（1950〜2022年）。濃い棒は出典で確認済み、薄い棒は終値からの概算※。平均・中央値（下の数値欄）はPepperstoneの集計値。</div></div>
<div class="kpis">
  <div class="kpi"><div class="v">19<small>戦</small>19<small>勝</small></div><div class="l">1950年以降、選挙後1年の<br>S&amp;P500は全てプラス</div></div>
  <div class="kpi"><div class="v">+15.1<small>%</small></div><div class="l">選挙後1年の平均<br>（中央値+14.5%）</div></div>
  <div class="kpi"><div class="v">+14<small>%</small></div><div class="l">選挙後6か月（11〜4月）の平均<br>4年サイクルで最強の期間</div></div>
  <div class="kpi"><div class="v">0<small>敗</small></div><div class="l">大統領サイクル3年目の<br>年間マイナス（1939年以降）</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>知っておきたいアノマリー</h2>
    <ul class="b">
      <li><b>大統領サイクル</b>：2年目（中間選挙の年）は平均+3.8%と弱く、他の3年は平均+10.9%。3年目は平均+13.5%、上昇確率78%。</li>
      <li><b>中間選挙の年の安値から1年後は平均+31.7%</b>。2022年は10月、2018年は12/24が安値でした。</li>
      <li><b>日本の年末ラリー</b>：日経など3指数の12月の勝率は過去10年で70〜80%（2015年時点の集計）。</li>
      <li><b>節分天井・彼岸底</b>：よく聞く格言ですが、大和総研は統計的な裏付けはないとしています。話のネタ程度に。</li>
    </ul>
  </div>
  <div>
    <h2><span class="n">2</span>反例：2018年は「勝ったが途中で-20%」</h2>
    <p>2018年は9/20の高値から12/24までS&amp;P500が<b class="dn">-19.8%</b>下げました。原因はFRBのタカ派姿勢、米中摩擦、原油安です。それでも投票日から1年後は<b class="upc">+11.7%</b>でした。</p>
    <p>今年も、ヘッジファンドの12月末解約の通知期限（11/15前後、いわゆる<b>45日ルール</b>）に向けた換金売りが意識されています。2018年はQ4に約225億ドルが流出し（HFR）、<b>クリスマスに向けて下げが加速</b>しました。</p>
  </div>
  <div class="span2">
    <h2><span class="n">3</span>2018年と2026年を並べる</h2>
    <table class="t">
      <tr><th>項目</th><th>2018年</th><th>2026年（現在）</th></tr>
      <tr><td>選挙結果</td><td>民主党が下院を奪還（ねじれ）</td><td>民主党が上下両院を奪還（ねじれ）</td></tr>
      <tr><td>FRB</td><td>利上げ継続（12月も利上げ）</td><td>12月利上げ確率 約88%</td></tr>
      <tr><td>主な売り材料</td><td>米中貿易摩擦、原油安</td><td>AIデータセンター規制、イラン情勢、原油高</td></tr>
      <tr><td>選挙前の上昇</td><td>年初来でほぼ横ばい</td><td>Q3までに約+13%（先に上げた）</td></tr>
      <tr><td>その後</td><td>12/24まで-19.8% → 1年後は+11.7%</td><td><b>？</b>（Session 1-4のシナリオへ）</td></tr>
    </table>
  </div>
  <div class="span2 box tint2">
    <h3>今年は違うかもしれない3つの理由</h3>
    <div class="cols3 small">
      <p><b class="dn">① 先に上げすぎた</b><br>S&amp;P500は第3四半期までに約+13%上昇済み。「選挙後の上げ」を先に織り込んだ可能性があります。</p>
      <p><b class="dn">② 利下げではなく利上げ</b><br>12/9のFOMCは利上げ確率が約88%。2018年と同じく、FRBが株価の重しになりえます。</p>
      <p><b class="dn">③ 新しい政治リスク</b><br>AIデータセンター規制は、今年の相場をけん引したAI投資そのものを直撃します。</p>
    </div>
  </div>
</div>"""
    out.append(sheet(1, 2, "歴史は「選挙後は株高」と言う。ただし2018年の-20%を忘れない", "中間選挙アノマリー・大統領サイクル・年末ラリーと、その反例", body,
                     ["Pepperstone: Do stocks rally after midterms?（1950年以降の集計）", "Motley Fool: Midterm election year stock market history", "CFA Institute: Election cycle theory, year three", "Carson Group / Ryan Detrick（選挙後6か月・安値から1年）", "Chase: Presidential cycle（1945〜2025年）", "HFR：2018年Q4ヘッジファンド資金流出"]))

    # ---------- 1-3 年末ラリーと1月の資金 ----------
    mon = bar_chart(["11月", "12月", "1月", "2月", "3月", "4月"], [1.79, 1.54, -0.45, 0.76, 0.28, 1.66],
                    colors=["#8DA2BF", C, A, "#8DA2BF", "#8DA2BF", "#8DA2BF"], w=330, h=150, ymin=-1, ymax=2.2, fmt="{:+.2f}%")
    flow = timeline([(0, "12月上旬|損出し売り開始", False), (14, "12/11|メジャーSQ", False), (27, "12/28|年内受渡最終日", True),
                     (29, "12/30|大納会", False), (34, "1/4|大発会・NISA新枠", True), (45, "1月中旬|年初一括の買い", True),
                     (60, "1月末|米大手決算", False), (64, "2/3|節分", False), (101, "3/12|メジャーSQ", False), (118, "3月末|年度末", False)],
                    w=700, color=C, accent=A)
    body = f"""
<div class="kpis">
  <div class="kpi"><div class="v">+1.3<small>%</small></div><div class="l">米サンタクロース・ラリー平均<br>勝率約79%（1950年以降）</div></div>
  <div class="kpi"><div class="v">65<small>%</small></div><div class="l">日経の12月の勝率<br>平均+1.54%（2000年以降）</div></div>
  <div class="kpi"><div class="v">360<small>万円</small></div><div class="l">新NISAの年間枠<br>毎年1月1日にリセット</div></div>
  <div class="kpi"><div class="v">2<small>兆円超</small></div><div class="l">投資信託の1月の純流入<br>（2025年・2026年とも）</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>なぜ年末に売られ、1月に買われるのか</h2>
    <ul class="b">
      <li><b>年末は「含み損の洗い出し」</b>：個人は12月に含み損の株を売り、その年の利益と相殺して税金を減らします（損出し）。今年下げた人気テーマ株ほど売られます。</li>
      <li><b>締め切りは12/28（月）</b>：この日の約定が年内受渡の最終日。損出し売りはここで一巡し、その後は売り手がいなくなります。</li>
      <li><b>1月は新しいお金が入る</b>：新NISAの年間枠（成長240万円＋つみたて120万円）が1/1にリセット。年初に一括で買う人が増え、投資信託の1月の純流入は2兆円を超えました。</li>
      <li><b>機関投資家も年初に配分を組み直す</b>：新しい運用年度のスタートで、売られすぎた銘柄に資金が戻りやすい（米国の「1月効果」）。</li>
    </ul>
  </div>
  <div>
    <div class="fig">{mon}<div class="cap"><b>Fig.3</b> 日経平均の月別平均騰落率（2000〜2026年、月末値から自前集計）。勝率は11月63%、12月65%、1月56%、2月63%、3月56%、4月59%。</div></div>
    <div class="box tint2" style="margin-top:8px">
      <h3>データで見ると意外な点</h3>
      <p class="small">日経の1月は平均<b class="dn">-0.45%</b>とむしろ弱い月です（2008年・2016年の急落が平均を下げた。中央値は+0.42%）。<b>強いのは12月</b>。つまり「1月に新しいお金が入る」効果は、<b>12月の損出しで十分に売られた銘柄</b>に出やすいと考えます。</p>
    </div>
  </div>
</div>
<div class="fig">{flow}<div class="cap"><b>Fig.4</b> 年末〜年度末の資金の流れ（2026〜27年の日程）。赤が需給の転換点。損出し売りは12/28の約定で一巡し、1/4の大発会からNISAの新枠の資金が入ります。</div></div>
<div class="box tint">
  <h3>演者の見立て：今年は「年末ラリー」より「年明けラリー」</h3>
  <p class="small">X上の「リバウンドを挟みながら年末まで下げる」シナリオが当たると、12月はラリーではなく<b>損出しと換金売りの月</b>になります。2018年もS&amp;P500は12/24に底を打ち、年明けから急回復しました。<b>12月後半に下値ゾーン（1-4）へ届いたら、1月の新しいお金の前に仕込む</b>。これがSession 3のお年玉銘柄の基本戦略につながります。</p>
</div>"""
    out.append(sheet(1, 3, "年末に売られ、1月にお金が戻る：年末ラリーと「1月の新しいお金」", "損出し・年内受渡最終日・新NISA枠のリセットから、12月〜1月の需給を読む", body,
                     ["Stock Trader's Almanac / LPL Research：Santa Claus Rally（1950年以降）", "yfinance ^GSPC・^N225 から自前集計（サンタラリー勝率76%、月別騰落）", "マネックス証券：2026年12月の権利・受渡日程", "モーニングスター：NISAと年初一括投資（2026年Q1）", "金融庁：NISA口座の利用状況（2026年1〜6月 買付13.8兆円）"]))

    # ---------- 1-4 下値ゾーン（日経の週足に書き込み） ----------
    n = Chart("n225", 700, view=(1100, 300, 1854, 590))
    n.band(48000, 50000, "想定下値ゾーン 48,000〜50,000円", PINK, x0=1110, x1=1700, lx=1120)
    n.hline(62000, "戻りの目標 62,000円（割れた節目＝200日線）", CYAN, x0=1110, x1=1700, lx=1120)
    n.hline(47200, "142週線 47,200", WHITE, x0=1110, x1=1700, lx=1400, above=False)
    n.note_xy(1120, n.y(48000) + 34, "1年前の安値 48,538／今年の安値 50,558", YEL, 10)
    n.path([("2026-11-10", 60459), ("2026-11-27", 62000), ("2026-12-14", 55500), ("2026-12-28", 49000)], YEL)
    n.path([("2026-12-28", 49000), ("2027-01-20", 54000)], GREEN, dash=True)
    n.sticker(1330, 318, ["ズバリ", "年末 49,000円"], YEL, size=13)
    body = f"""
<div class="fig">{n.svg()}<div class="cap"><b>Fig.5</b> 日経平均の週足（11/10時点、証券アプリの画面に演者が書き込み）。黄色＝「リバウンドを挟みながら年末まで下げる」想定ルート、緑の点線＝年明けの戻り。</div></div>
<div class="cols" style="grid-template-columns:1fr 1.1fr">
  <div>
    <h2><span class="n">1</span>48,000〜50,000円はどんな水準か</h2>
    <table class="t">
      <tr><th>比べる相手</th><th class="r">水準</th><th class="r">50,000円まで</th></tr>
      <tr><td><b>現在値（11/10）</b></td><td class="r"><b>60,459</b></td><td class="r dn"><b>-17.3%</b></td></tr>
      <tr><td>戻りの目標（200日線）</td><td class="r">62,000</td><td class="r dn">-19.4%</td></tr>
      <tr><td>6/25 年初来高値</td><td class="r">72,366</td><td class="r dn">-30.9%</td></tr>
      <tr><td>3/31 年初来安値</td><td class="r">50,558</td><td class="r dn">-1.1%</td></tr>
      <tr><td>1年前の安値（52週安値）</td><td class="r">48,538</td><td class="r upc">+3.0%</td></tr>
      <tr><td>142週線</td><td class="r">47,200</td><td class="r upc">+5.9%</td></tr>
    </table>
    <p class="small" style="margin-top:4px">48,000〜50,000円は<b>「今年の安値」「1年前の安値」「142週線」が集まる帯</b>です。ここまで下げると今年の上昇分がほぼ消えます。逆に言えば、長期の上昇トレンドが続くなら<b>最後に止まりやすい場所</b>でもあります。</p>
  </div>
  <div>
    <div class="alert">
      <div class="hd">⚠ この下げを想定していないと退場する</div>
      <p class="small">X上では、225先物の日足で<b>「割れた62,000円まで戻してから、もう一段下げる」</b>という作図も出ています。演者もこのシナリオを否定できず、<b>48,000〜50,000円は想定しておくべきライン</b>と考えます。現在値からは<b>-17〜21%</b>です。</p>
      <table class="t nw" style="margin-top:4px">
        <tr><th>持ち方</th><th class="r">日経-20%時の損失</th><th>結果</th></tr>
        <tr><td>現物・指数並み</td><td class="r">-20%</td><td>耐えうる</td></tr>
        <tr><td>現物・高ベータ株</td><td class="r">-35〜45%</td><td>心が折れやすい</td></tr>
        <tr><td>信用2倍</td><td class="r dn">-40%（資産比）</td><td class="dn">追証・強制決済</td></tr>
        <tr><td>信用3倍</td><td class="r dn">-60%</td><td class="dn">退場</td></tr>
      </table>
    </div>
    <h2 style="margin-top:7px"><span class="n">2</span>シナリオ（12月〜3月）</h2>
    <div class="fig" style="padding:4px 6px">{scenario_bar([("強気：高値奪回へ", 20, "#13803B"), ("メイン：戻して二番底→春に回復", 50, C), ("弱気：48,000円割れ", 30, A)], w=700, h=46)}</div>
    <p class="small">メイン：62,000円まで戻した後、12月に50,000円前後で二番底、1月から回復。弱気：48,000円を割り込み、2018年型の-20%超に。</p>
  </div>
</div>"""
    out.append(sheet(1, 4, "最大下げ「48,000〜50,000円」を想定しない人は退場する", "X上の見方と演者の見立て：62,000円まで戻してから、年末にかけてもう一段下げるルート", body,
                     ["証券アプリ 日経平均 週足（2026/11/10、演者のスクリーンショット）", "yfinance：日経平均の52週安値・142週線（11/10取得）", "X上の225先物チャートの作図（2026/11/10）", "HFR：2018年Q4ヘッジファンド資金流出"]))

    # ---------- 1-5 若手の保有株①：ソフトバンクG × ARM ----------
    sb = Chart("sbg", 343, view=(1200, 360, 1854, 640))
    sb.hline(4193, "戻り目標 4,193（61.8%押し）", CYAN, x0=1210, x1=1700, lx=1220)
    sb.hline(3532, "142週線 3,532", WHITE, x0=1210, x1=1700, lx=1220, above=False)
    sb.band(2900, 3000, None, PINK, x0=1210, x1=1700)
    sb.note_xy(1220, sb.y(2900) + 30, "200週線2,948＋78.6%押し2,989", PINK, 10)
    sb.hline(2490, "日経5万円なら 2,490", "#FF9F43", x0=1210, x1=1700, lx=1220, above=False)
    sb.path([("2026-11-10", 3560), ("2026-11-27", 4200), ("2026-12-28", 2950)], YEL)
    sb.sticker(1330, 372, ["ズバリ", "年末 2,950円"], YEL, size=12)
    ar = Chart("arm", 343, view=(1200, 330, 1854, 640))
    ar.hline(232.5, "戻り目標 232（61.8%押し＝200日線）", CYAN, x0=1210, x1=1700, lx=1220)
    ar.hline(164, "142週線 164", WHITE, x0=1210, x1=1700, lx=1220, above=False)
    ar.band(131, 155, "2025年夏のもみ合い 131〜155", PINK, x0=1210, x1=1700, lx=1220)
    ar.path([("2026-11-10", 186), ("2026-11-27", 230), ("2026-12-28", 150)], YEL)
    ar.sticker(1330, 372, ["ズバリ", "年末 150ドル"], YEL, size=12)
    body = f"""
<div class="box tint small">新入社員の若手投資家が保有している2銘柄を、Xの「リバウンドを挟みながら年末まで下げる」シナリオに当てはめます。<b>ソフトバンクGは11/10の終値3,872円（+13.9%）の後、引け後に中間赤字7,680億円を発表し、夜間取引で3,560円（-8%）</b>。ここが出発点です。</div>
<div class="cols">
  <div class="fig">{sb.svg()}<div class="cap"><b>Fig.6</b> ソフトバンクG（9984）週足。黄色が想定ルート：4,200円まで戻してから年末2,950円へ。</div></div>
  <div class="fig">{ar.svg()}<div class="cap"><b>Fig.7</b> ARM（米国）週足。230ドルまで戻してから150ドルへ。11/5の決算後に-13%。</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>SBGを持つならARMを見なければいけない3つの理由</h2>
    <ul class="b">
      <li><b>資産の約半分がARM</b>：SBGはARMを約90%保有。ARMが10%動くと純資産（NAV）が兆円単位で動きます。週次リターンの相関は0.70。</li>
      <li><b>ARM株が借金の担保</b>：ARM株約7.7億株（保有の約72%）を担保に最大250億ドルを借りています。ARMが下がると担保の余力が縮み、財務指標（LTV）が悪化します。</li>
      <li><b>AI投資の資金源</b>：OpenAIへの累計646億ドル（持分約13%）もARM担保の借入や社債が支えています。ARM安は「投資の余力が減る」連想を呼びます。</li>
    </ul>
    <p class="small muted">ARMの時間差：米国市場は日本の夜に動くので、<b>SBGは前夜のARMに反応</b>します（翌日ベースの相関0.49）。朝にARMを確認する習慣を。</p>
  </div>
  <div>
    <h2><span class="n">2</span>どこまで下げるか：3つの物差し</h2>
    <table class="t">
      <tr><th>物差し</th><th class="r">SBG</th><th class="r">ARM</th></tr>
      <tr><td>戻りの目標</td><td class="r">4,193</td><td class="r">232</td></tr>
      <tr><td>テクニカルの節目（200週線・78.6%押し）</td><td class="r">2,948〜2,989</td><td class="r">164〜176</td></tr>
      <tr><td>ベータ×日経の下落（日経50,000円）</td><td class="r">約2,490</td><td class="r">—</td></tr>
      <tr><td>ベータ×日経の下落（日経48,000円）</td><td class="r dn">約2,220</td><td class="r">—</td></tr>
      <tr><td><b>演者のズバリ（年末）</b></td><td class="r"><b class="dn">2,950</b></td><td class="r"><b class="dn">150</b></td></tr>
    </table>
    <p class="small" style="margin-top:4px">SBGの日経に対するベータは<b>2.07</b>（日経が1%動くと約2%動く）。<b>日経-17%なら-36%</b>です。ズバリは、テクニカルの節目が重なる2,950円としました。そこを割ると理論値の2,500円前後まで見ておく必要があります。</p>
  </div>
</div>
<div class="box tint2 small"><b>若手へのひと言</b>：SBGは「日経の2倍動くAI投資信託」と考えると扱いやすい。信用取引で持つなら、2,500円まで下げても追証が出ない量に。現物なら2,950円近辺は買い増し候補、ただし<b>ARMが150ドルを割るなら待つ</b>。</div>"""
    out.append(sheet(1, 5, "若手の保有株①ソフトバンクG：ARMを見ずに持ってはいけない", "週足に想定ルートを書き込み、年末の下値をズバリ予想する", body,
                     ["証券アプリ ソフトバンクG・ARM 週足（2026/11/10、演者のスクリーンショット）", "時事通信・Bloomberg：ソフトバンクG 2026年度上期決算（11/10）", "SBG IR：NAV・LTV（6/30時点）、Newsquawk：ARM担保ローン250億ドル", "Arm Newsroom：FY27 Q2決算（11/4）", "yfinance：ベータ・相関・移動平均（自前計算）"]))

    # ---------- 1-6 若手の保有株②：三菱重工と、退場しないルール ----------
    mh = Chart("mhi", 343, view=(1200, 320, 1854, 600))
    mh.hline(3604, "戻り目標 3,604（50%押し）", CYAN, x0=1210, x1=1700, lx=1220)
    mh.hline(3061, "142週線 3,061", WHITE, x0=1210, x1=1700, lx=1400, above=True)
    mh.band(2700, 2780, None, PINK, x0=1210, x1=1700)
    mh.note_xy(1220, mh.y(2700) + 30, "78.6%押し2,713＝ベータ理論値2,710〜2,780", PINK, 10)
    mh.path([("2026-11-10", 3151), ("2026-11-27", 3600), ("2026-12-28", 2730)], YEL)
    mh.path([("2026-12-28", 2730), ("2027-01-25", 3300)], GREEN, dash=True)
    mh.sticker(1330, 330, ["ズバリ", "年末 2,730円"], YEL, size=12)
    body = f"""
<div class="cols">
  <div>
    <div class="fig">{mh.svg()}<div class="cap"><b>Fig.8</b> 三菱重工（7011）週足。3,600円まで戻してから年末2,730円へ。緑の点線は年明けの戻り。</div></div>
    <div class="box tint" style="margin-top:8px"><p class="small"><b>ズバリ年末2,730円</b>：78.6%押し（2,713円）と、ベータから計算した日経5万円時の理論値（2,710〜2,780円）がぴったり重なります。日経に対するベータは<b>0.68</b>とSBGの3分の1。<b>業績の裏付けがあるので、ここは買い増しを考えてよい水準</b>です。</p></div>
  </div>
  <div>
    <h2><span class="n">1</span>業績は絶好調、株価は52週安値</h2>
    <ul class="b small">
      <li>上期（11/6発表）：受注3.6兆円（+9%）、事業利益2,493億円（+45%）、純利益+77%。受注残は<b>14.2兆円</b>。</li>
      <li>通期予想を上方修正（純利益3,800→4,400億円）し、<b>上限3,000億円の自社株買い</b>も発表。</li>
      <li>それでも当日は-4.6%で、11/6に52週安値2,912円。<b>好材料で売られるのは需給の悪化</b>（防衛・原発の人気テーマ株の利益確定）。</li>
      <li>追い風：防衛費の概算要求は過去最大の8.9兆円、AIデータセンター向けのガスタービン受注残は5兆円超。</li>
    </ul>
  </div>
</div>
<table class="t">
  <tr><th>若手の2銘柄</th><th>性格</th><th class="r">ベータ</th><th class="r">年末ズバリ</th><th class="r">現在値から</th><th>そこで何をするか</th></tr>
  <tr><td><b>ソフトバンクG</b></td><td>AI投資の高ベータ株。ARMとOpenAI次第</td><td class="r">2.07</td><td class="r dn">2,950円</td><td class="r dn">-17%（夜間3,560比）</td><td>ARMが150ドルを守れば打診買い。割れたら待つ</td></tr>
  <tr><td><b>三菱重工</b></td><td>業績好調の防衛・エネルギー株</td><td class="r">0.68</td><td class="r dn">2,730円</td><td class="r dn">-13%</td><td>2,700円台は分けて買い増し。3月までの戻りを狙う</td></tr>
</table>
<div class="cols">
  <div>
    <h2><span class="n">2</span>退場しないための5つのルール</h2>
    <ul class="b">
      <li><b>信用・レバレッジは12月まで最小限</b>。日経-20%で追証が出ない量に落とす。</li>
      <li><b>資金全体の現金を30%残す</b>。下げは買い場に変わるが、現金がなければ買えない。</li>
      <li><b>買いは3回に分ける</b>：日経56,000円／52,000円／49,000円。</li>
      <li><b>逆指値を先に置く</b>。売る理由は買う前に決める。</li>
      <li><b>戻りは売りを疑う</b>。62,000円（200日線）を週足で超えるまでは強気にならない。</li>
    </ul>
  </div>
  <div>
    <h2><span class="n">3</span>飲み会での論点</h2>
    <div class="box tint2 small">
      <p>① 日経は62,000円まで戻るか、その前に失速するか</p>
      <p>② 若手の2銘柄、今のうちに半分売る？　持ち続ける？　買い増す？</p>
      <p>③ SBGの夜間-8%は、年末2,950円への第一歩か、売られすぎか</p>
      <p>④ 自分の持ち高は、日経49,000円でも眠れるか</p>
    </div>
  </div>
</div>"""
    out.append(sheet(1, 6, "若手の保有株②三菱重工と、退場しないための5つのルール", "好業績で52週安値の三菱重工はどこまで下げるか。2銘柄の結論と行動ルール", body,
                     ["証券アプリ 三菱重工 週足（2026/11/10、演者のスクリーンショット）", "三菱重工 2026年度上期決算説明資料（11/6）", "時事：2027年度防衛費 概算要求（8兆8,908億円）", "yfinance：ベータ・移動平均・フィボナッチ（自前計算）"]))
    return out
