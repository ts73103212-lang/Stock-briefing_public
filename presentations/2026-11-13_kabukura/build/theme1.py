import json
from pathlib import Path

from kit import sheet, bar_chart, line_chart, scenario_bar, timeline

C, A = "#1D3557", "#C1121F"
HERE = Path(__file__).parent


def pages():
    out = []
    # ---------- 1-1 ----------
    sox = bar_chart(["11/4", "11/5", "11/6", "11/9"], [-3.13, -12.3, 4.21, 6.5], w=330, h=150, ymin=-14, ymax=8, fmt="{:+.1f}%")
    body = f"""
<div class="kpis">
  <div class="kpi"><div class="v">54<small>対</small>44</div><div class="l">上院（民主対共和）<br>選挙前は共和53対民主47</div></div>
  <div class="kpi"><div class="v">228<small>対</small>139</div><div class="l">下院（民主対共和）<br>民主が19議席増・一部未確定</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-4.36<small>%</small></div><div class="l">11/5 S&amp;P500<br>NASDAQ -5.52%、VIX 28.8</div></div>
  <div class="kpi"><div class="v" style="color:#C1121F">-3,643<small>円</small></div><div class="l">11/6 日経平均（57,435円）<br>下げ幅は歴代3位級</div></div>
</div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>選挙後5日間に起きたこと</h2>
    <table class="t">
      <tr><th>日付</th><th>出来事と値動き</th></tr>
      <tr><td><b>11/3</b></td><td>中間選挙。投票数1.24億票超で中間選挙として過去最多。民主党が上下両院を制する</td></tr>
      <tr><td><b>11/4</b></td><td><span class="upc">安心ラリー</span>。「ねじれ議会なら政策のサプライズが減る」とダウ+1,569ドル（+3.03%）。ただしSOXは-3.1%</td></tr>
      <tr><td><b>11/5</b></td><td><span class="dn">急落</span>。テキサス州知事選で「データセンター建設の即時停止」を掲げた民主党候補が勝利。SOX -12.3%、NVIDIAは1日で時価総額4,000億ドル超を失う</td></tr>
      <tr><td><b>11/6</b></td><td><span class="dn">東京に波及</span>。日経は一時4,300円超安の56,745円。プライム市場の98%が値下がり、売買代金12.5兆円</td></tr>
      <tr><td><b>11/9</b></td><td>6営業日ぶりに反発（58,776円、+2.33%）。後場は追証売りへの警戒で上げ幅を縮める</td></tr>
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
      <tr><td>日経平均（11/9）</td><td class="r">58,776</td><td class="r dn">-5.1%</td><td class="r dn">-18.8%</td></tr>
      <tr><td>S&amp;P500（11/6）</td><td class="r">7,377</td><td class="r upc">+0.7%</td><td class="r dn">-5.6%</td></tr>
      <tr><td>NASDAQ100（11/6）</td><td class="r">26,990</td><td class="r dn">-3.6%</td><td class="r dn">-13.6%</td></tr>
      <tr><td>SOX（11/6）</td><td class="r">9,390</td><td class="r dn">-13.4%</td><td class="r dn">-35.8%</td></tr>
    </table>
    <p class="cap">終値。200日線・高値はyfinance（11/9取得）。S&amp;P500だけがまだ200日線の上にいる。</p>
  </div>
  <div>
    <div class="fig">{sox}<div class="cap"><b>Fig.1</b> 選挙後のSOX指数（米半導体株）の日次騰落率。11/5の-12.3%は2020年3月以来の最悪級。11/9は米国の取引時間中の値。</div></div>
    <div class="box tint" style="margin-top:8px">
      <h3>本セッションの結論</h3>
      <p class="small">歴史的には「中間選挙の後の1年は株高」（1950年以降19戦19勝）です。演者もメインシナリオは<b>春に向けた回復</b>と考えます。<br>ただしそれは<b>途中の下げを生き残った人だけ</b>が受け取れるリターンです。新天地さんの見立てどおり、ここから一旦は<b class="dn">日経48,000円</b>まで下げる展開を想定し、資金とレバレッジを管理することが本日の主題です。</p>
    </div>
    <div class="box" style="margin-top:8px">
      <h3>マクロの現在地（11/9）</h3>
      <p class="small">米10年債4.89%／FF金利3.75〜4.00%（12月利上げ確率 約88%）／ドル円158円台（介入警戒）／WTI 90ドル台（イラン情勢・ホルムズ海峡）／米Q3 GDP +3.4%</p>
    </div>
  </div>
</div>"""
    out.append(sheet(1, 1, "民主党が上下両院を奪還：選挙後5日間で何が起きたか", "安心ラリーから一転、AIデータセンター規制への懸念で世界的な株安へ", body,
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
    <p>新天地さんのメルマガ（11/9）も、ヘッジファンドの12月末解約の通知期限（11/15前後、いわゆる45日ルール）を挙げ、<b>「2018年だけはクリスマスに向けて大きく下げた」</b>と注意を促しています。</p>
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
                     ["Pepperstone: Do stocks rally after midterms?（1950年以降の集計）", "Motley Fool: Midterm election year stock market history", "CFA Institute: Election cycle theory, year three", "Carson Group / Ryan Detrick（選挙後6か月・安値から1年）", "Chase: Presidential cycle（1945〜2025年）", "新天地メルマガ「45日ルール」（2026/11/9配信）"]))

    # ---------- 1-3 ----------
    wk = json.loads((HERE / "n225_weekly.json").read_text())
    lab = [d[0][2:7].replace("-", "/") for d in wk]
    closes = [d[1] for d in wk]
    ma = [d[2] for d in wk]
    ticks = [i for i, d in enumerate(wk) if d[0][8:10] <= "07"]
    fig = line_chart(lab, [(ma, "#8DA2BF", 1.6, "4 2", "200日線 61,964"), (closes, C, 2.2, "", "現在 57,435")], w=700, h=215, lo=40000, hi=76000, step=6000,
                     hlines=[(50558, "3月安値 50,558", "#B45309"), (48000, "下値目安 48,000", A)], xticks=ticks, bands=[(46000, 50558, A, "")])
    body = f"""
<div class="fig">{fig}<div class="cap"><b>Fig.3</b> 日経平均の週足（2025年11月〜2026年11月6日）と200日移動平均。赤い帯は「3月安値割れ〜48,000円」の想定下値ゾーン。データ：yfinance。</div></div>
<div class="cols" style="grid-template-columns:1fr 1.1fr">
  <div>
    <h2><span class="n">1</span>48,000円はどんな水準か</h2>
    <table class="t">
      <tr><th>比べる相手</th><th class="r">水準</th><th class="r">48,000円まで</th></tr>
      <tr><td>6/25 年初来高値</td><td class="r">72,366</td><td class="r dn">-33.7%</td></tr>
      <tr><td>200日線（上値の壁に転換）</td><td class="r">61,964</td><td class="r dn">-22.5%</td></tr>
      <tr><td><b>現在値（11/9終値）</b></td><td class="r"><b>58,776</b></td><td class="r dn"><b>-18.3%</b></td></tr>
      <tr><td>フィボナッチ78.6%戻し</td><td class="r">55,225</td><td class="r dn">-13.1%</td></tr>
      <tr><td>3/31 年初来安値（ザラ場）</td><td class="r">50,558</td><td class="r dn">-5.1%</td></tr>
      <tr><td>100週線（参考）</td><td class="r">50,576</td><td class="r dn">-5.1%</td></tr>
    </table>
    <p class="small" style="margin-top:4px">48,000円は<b>今年の上昇分をすべて失う水準</b>です。予想PERは約13.7倍（5月時点の予想EPS 3,495円で試算※）。東証の要請以降のPERレンジ16〜18倍を大きく下回ります。米国はS&amp;P500が200日線7,328に接近（11/6終値7,377から-0.7%）、NASDAQ100はすでに200日線割れです。</p>
  </div>
  <div>
    <div class="alert">
      <div class="hd">⚠ 新天地さんの警告：この下げを想定していないと退場する</div>
      <p class="small">新天地さんの見立ては「ここから一旦は大きく下げる。最大下げとして<b>200日線割れの定着と日経48,000円</b>くらいは想定しておくべき」というものです。現在値（11/9終値58,776円）からは<b>約-18%</b>。日経に連動する個別株は、その1.5〜2倍下げることも珍しくありません。</p>
      <table class="t nw" style="margin-top:4px">
        <tr><th>持ち方</th><th class="r">日経-18%時の損失目安</th><th>結果</th></tr>
        <tr><td>現物・指数並み</td><td class="r">-18%</td><td>耐えられる</td></tr>
        <tr><td>現物・高ベータ株</td><td class="r">-30〜40%</td><td>心が折れやすい</td></tr>
        <tr><td>信用2倍</td><td class="r dn">-36%（資産比）</td><td class="dn">追証・強制決済</td></tr>
        <tr><td>信用3倍</td><td class="r dn">-54%以上</td><td class="dn">退場</td></tr>
      </table>
    </div>
    <h2 style="margin-top:7px"><span class="n">2</span>下げを大きくする需給要因</h2>
    <ul class="b small">
      <li><b>45日ルール</b>：ヘッジファンドの年末解約の通知期限は11/15前後。2018年はQ4に約225億ドルが流出（HFR）。</li>
      <li><b>高値-10%ルール</b>：機関投資家の機械的な損切りが11/5の下げを拡大（新天地メルマガ11/6）。</li>
      <li><b>追証売り</b>：11/9の後場も追証への警戒で上げ幅を縮めた。信用買い残の整理は終わっていない。</li>
    </ul>
  </div>
</div>"""
    out.append(sheet(1, 3, "最大下げ「日経48,000円」を想定しない人は退場する", "新天地さんの見立てを数字で検証：どこまで下げうるか、そのとき何が起きるか", body,
                     ["新天地メルマガ（2026/11/6〜11/9配信）：45日ルール・高値-10%ルール・追証警戒", "yfinance：日経平均・S&P500 日足/週足、移動平均（11/9取得）", "SBI証券：日経平均の予想EPS（2026/5/19）", "野村證券：日本株PERレンジ", "HFR：2018年Q4ヘッジファンド資金流出"]))

    # ---------- 1-4 ----------
    sb = scenario_bar([("強気：年末ラリーで高値奪回へ", 25, "#13803B"), ("メイン：2番底→春に回復", 50, C), ("弱気：48,000円まで", 25, A)], w=700, h=46)
    ev = [(3, "12/4|米雇用統計", False), (8, "12/9|FOMC利上げ?", True), (9, "12/10頃|米CPI", False), (10, "12/11|メジャーSQ", True),
          (17, "12/18|日銀会合", True), (26, "12/26頃|損出し売り一巡", False), (33, "1/3|新議会招集", False), (34, "1/4|大発会", False), (38, "1/8 SQ", False),
          (57, "1月下旬|FOMC・日銀", True), (64, "2/3 節分|国内決算", False), (84, "2/23頃|NVIDIA決算", True), (101, "3/12|メジャーSQ", True)]
    tl = timeline(ev, w=700, color=C, accent=A)
    body = f"""
<div class="fig">{sb}<div class="cap"><b>Fig.4</b> 12月〜3月のシナリオ確率（演者の主観）。</div></div>
<table class="t">
  <tr><th style="width:11%">シナリオ</th><th style="width:30%">日経平均</th><th style="width:20%">S&amp;P500</th><th>こうなるきっかけ</th></tr>
  <tr><td><span class="tag u">強気 25%</span></td><td>65,000円台を回復<br>（25日・75日線）</td><td>7,818の高値更新</td><td>11/17 NVIDIA決算が好調、データセンター規制のトーンダウン、12月FOMCで利上げ見送り、イラン停戦</td></tr>
  <tr><td><span class="tag c">メイン 50%</span></td><td>54,000〜56,000円で2番底<br>→ 200日線（約62,000円）まで戻す</td><td>7,100〜7,800</td><td>2018年型の短縮版。12月の需給悪化（解約・損出し）を経て、1月以降に回復</td></tr>
  <tr><td><span class="tag r">弱気 25%</span></td><td><b class="dn">48,000円</b>（-18%）</td><td>200日線割れが定着<br>2018年並みなら約6,250</td><td>FOMC利上げで米10年債5%超、データセンター停止の法制化、大手の投資削減、原油100ドル超、急な円高</td></tr>
</table>
<div class="fig">{tl}<div class="cap"><b>Fig.5</b> 12月〜3月の主なイベント（日付は予定、一部要確認）。赤は相場を動かしやすいもの。期間前の11/15前後（45日ルール）と11/17（NVIDIA決算）も要注意。</div></div>
<div class="cols">
  <div>
    <h2><span class="n">1</span>退場しないための5つのルール</h2>
    <ul class="b">
      <li><b>信用・レバレッジは12月まで最小限</b>。日経-18%で追証が出ない建玉に落とす。</li>
      <li><b>資金全体の現金を30%残す</b>。下げは「買い場」に変わるが、現金がなければ買えない。</li>
      <li><b>買いは3回に分ける</b>：56,000円／52,000円／48,000円（Session 2・3の銘柄もここで仕込む）。</li>
      <li><b>逆指値を先に置く</b>。売る理由は買う前に決める。</li>
      <li><b>反発は戻り売りを疑う</b>。200日線（約62,000円）回復までは強気にならない。</li>
    </ul>
  </div>
  <div>
    <h2><span class="n">2</span>他のセッションとのつながり</h2>
    <div class="box tint small">
      <p><b>Session 2（半導体）</b>：AI投資の行方が今回の下げの震源です。半導体が底を打つかどうかが、日経の底を決めます。</p>
      <p><b>Session 3（お年玉銘柄）</b>：12月の損出し売りと下値シナリオが重なれば、暴騰候補を安く仕込める好機になります。下げを怖がるのではなく、<b>下げを待てる資金配分</b>にしておくことが結論です。</p>
    </div>
    <h2 style="margin-top:7px"><span class="n">3</span>飲み会での論点</h2>
    <p class="small">① 2番底はどこか（56,000円？52,000円？48,000円？）　② 12/9 FOMCで本当に利上げはあるか　③ 今の自分の持ち高で、日経-18%に耐えられるか</p>
  </div>
</div>"""
    out.append(sheet(1, 4, "3つのシナリオと、退場しないための5つのルール", "確率・水準・きっかけを整理し、12月〜3月の行動を先に決める", body,
                     ["Federal Reserve: FOMC 2026-27 日程", "日本銀行: 金融政策決定会合 日程", "日本取引所グループ: SQ日程", "大和総研: 日銀の利上げ見通し（2026/9）", "本資料 Session 2・3"]))
    return out
