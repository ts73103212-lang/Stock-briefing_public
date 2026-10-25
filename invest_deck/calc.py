import json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.json")
INFL, CASH = 0.02, 0.001
RATES = [0.03, 0.05, 0.07]
AMTS = [1000, 10000, 30000]
YEARS = [10, 20, 30, 40]
TAX = 0.20315

def fv(m, rate, years):
    r = (1 + rate) ** (1 / 12) - 1  # 実効年率→月利
    v = 0.0
    for _ in range(years * 12):
        v = v * (1 + r) + m  # 積立は月末
    return v

def path(m, rate, years):
    r = (1 + rate) ** (1 / 12) - 1
    v, out = 0.0, [0]
    for i in range(1, years * 12 + 1):
        v = v * (1 + r) + m
        if i % 12 == 0: out.append(round(v))
    return out

def real(x, years): return x / (1 + INFL) ** years
R = lambda x: int(round(x))

table = []
for m in AMTS:
    for y in YEARS:
        p = m * 12 * y
        cash = fv(m, CASH, y)
        row = {"monthly": m, "years": y, "principal": p,
               "cash_nominal": R(cash), "cash_real": R(real(cash, y))}
        for r in RATES:
            v = fv(m, r, y)
            row[f"invest_{int(r*100)}pct"] = R(v)
            row[f"invest_{int(r*100)}pct_real"] = R(real(v, y))
            row[f"gain_{int(r*100)}pct"] = R(v - p)
        table.append(row)

# 購買力: 100万円
power = [{"years": y, "real_value": R(1_000_000 / (1 + INFL) ** y),
          "price_needed_for_same_goods": R(1_000_000 * (1 + INFL) ** y)} for y in (10, 20, 30, 40)]
# 預金100万円を置いたまま(金利0.1%)
deposit = [{"years": y, "nominal": R(1_000_000 * (1 + CASH) ** y),
            "real": R(1_000_000 * (1 + CASH) ** y / (1 + INFL) ** y)} for y in (10, 20, 30)]

# 年齢差 (65歳まで、月1万円)
age = []
for start in (25, 35):
    y = 65 - start
    d = {"start_age": start, "years": y, "principal": 10000 * 12 * y}
    for r in RATES: d[f"invest_{int(r*100)}pct"] = R(fv(10000, r, y))
    age.append(d)
# 35歳スタートで25歳スタート(月1万)に追いつく月額(5%)
target5 = fv(10000, 0.05, 40)
catch_up = {"target_5pct": R(target5), "monthly_needed_at_35": R(target5 / fv(1, 0.05, 30))}
catch_up["ratio"] = round(catch_up["monthly_needed_at_35"] / 10000, 2)
# 10年早く始めるコスト(元本差)
age_diff = {"principal_diff": age[0]["principal"] - age[1]["principal"]}

# 税: 月1万円20年 5%
v = fv(10000, 0.05, 20); p = 2_400_000; g = v - p
tax = {"monthly": 10000, "years": 20, "rate": 0.05, "principal": p, "value": R(v), "gain": R(g),
       "tax_normal": R(g * TAX), "after_tax_normal": R(v - g * TAX), "nisa": R(v), "tax_rate": TAX}
# 30年 月3万 5%
v3 = fv(30000, 0.05, 30); g3 = v3 - 10_800_000
tax2 = {"monthly": 30000, "years": 30, "rate": 0.05, "principal": 10_800_000, "value": R(v3),
        "gain": R(g3), "tax_normal": R(g3 * TAX)}

# NISA枠
nisa = {"tsumitate_year": 1_200_000, "growth_year": 2_400_000, "year_total": 3_600_000,
        "lifetime": 18_000_000, "growth_lifetime_sub_limit": 12_000_000,
        "years_to_fill_at_30000_monthly": 18_000_000 / 360_000,
        "years_to_fill_at_100000_monthly": 18_000_000 / 1_200_000,
        "tsumitate_monthly_max": 100_000}

# ストレス: 月1万20年5% の19年目末に-40%暴落
r = (1.05) ** (1 / 12) - 1
v = 0
for i in range(1, 19 * 12 + 1): v = v * (1 + r) + 10000
before = v; after = v * 0.6
for i in range(12): after = after * (1 + r) + 10000
stress = {"before_crash_19y": R(before), "after_-40pct_crash_end20y": R(after),
          "principal_20y": 2_400_000, "note": "20年目直前に40%下落しても元本を上回る例(5%シナリオ)"}

# 推移データ(グラフ用) 月1万円30年
series = {"monthly": 10000, "years": 30,
          "principal": [10000 * 12 * i for i in range(31)],
          "cash_nominal": path(10000, CASH, 30),
          "cash_real": [R(real(c, i)) for i, c in enumerate(path(10000, CASH, 30))],
          "invest_3pct": path(10000, .03, 30), "invest_5pct": path(10000, .05, 30),
          "invest_7pct": path(10000, .07, 30)}

def T(m, y): return next(t for t in table if t["monthly"] == m and t["years"] == y)
t1_20, t1_30, t10_10, t10_20, t10_30 = T(1000,20), T(1000,30), T(10000,10), T(10000,20), T(10000,30)
yen = lambda x: f"{x:,}円"
man = lambda x: f"約{x/10000:,.0f}万円"

pages = [
 {"no":1,"title":"20代のうちに知りたい、NISA積立のはじめ方","catch":"時間は、お金より先に減っていく。",
  "bullets":["月1,000円からでも始められる","必要なのは、才能ではなく「早さ」","8ページで、数字で確かめよう"],
  "chart":{"type":"none","note":"表紙。ビジュアル中心(右肩上がりの階段などイメージ図)"}},
 {"no":2,"title":"貯金だけだと、実はじわじわ減っている","catch":"100万円は、20年後「約67万円分」の価値に。",
  "bullets":[f"インフレ年2%だと、今の100万円の購買力は10年後約{power[0]['real_value']//10000}万円分、20年後約{power[1]['real_value']//10000}万円分、30年後約{power[2]['real_value']//10000}万円分",
             f"預金金利0.1%想定では、100万円は20年で{deposit[1]['nominal']:,}円。額面は増えても実質は約{deposit[1]['real']//10000}万円分",
             "「減らさない」ためにも、お金を働かせる選択肢が要る(インフレ2%は想定であり保証ではない)"],
  "chart":{"type":"line","title":"100万円の購買力の推移(インフレ年2%)","x":"年(0〜30)","series":["預金100万円の実質価値(金利0.1%)","インフレ2%で同じものを買うのに必要な額"],
           "data_ref":"extra.power_and_deposit"}},
 {"no":3,"title":"投資すると、お金が「お金を生む」","catch":"複利は、時間が味方になるしくみ。",
  "bullets":["利益にも利益がつく=複利。長いほど伸びが加速する",
             f"月1万円を30年積立:元本{man(t10_30['principal'])}→預金だと実質約{t10_30['cash_real']//10000}万円、年5%運用なら{man(t10_30['invest_5pct'])}",
             "年率3%/5%/7%は保守的な仮定。過去のS&P500や全世界株式の長期年率は概ね7〜10%台とされるが、将来を保証するものではない"],
  "chart":{"type":"line","title":"月1万円×30年の資産推移","x":"年","series":["元本","預金(名目)","預金(実質)","年3%","年5%","年7%"],"data_ref":"extra.series_10000_30y"}},
 {"no":4,"title":"月1,000円と月1万円、10年・20年・30年の差","catch":"金額より、続けた年数が効いてくる。",
  "bullets":[f"月1,000円:20年で元本24万円→年5%で{man(t1_20['invest_5pct'])}、30年で{man(t1_30['invest_5pct'])}",
             f"月1万円(年5%):10年{man(t10_10['invest_5pct'])}/20年{man(t10_20['invest_5pct'])}/30年{man(t10_30['invest_5pct'])}",
             f"月1万円30年の元本{man(t10_30['principal'])}に対し、増えた分は年5%で約{t10_30['gain_5pct']//10000}万円"],
  "chart":{"type":"grouped_bar","title":"積立額×期間の最終評価額(年5%)","x":"10年/20年/30年","series":["月1,000円","月10,000円","月30,000円(任意)"],"overlay":"元本を濃淡で併記","data_ref":"tables"}},
 {"no":5,"title":"始める年齢で、結果は変わる","catch":"25歳と35歳、たった10年で約1.8倍の差。",
  "bullets":[f"月1万円を65歳まで(年5%):25歳スタート{man(age[0]['invest_5pct'])}、35歳スタート{man(age[1]['invest_5pct'])}",
             f"元本の差は{man(age_diff['principal_diff'])}だけなのに、結果の差は約{(age[0]['invest_5pct']-age[1]['invest_5pct'])//10000}万円",
             f"35歳から追いつくには月約{catch_up['monthly_needed_at_35']:,}円(約{catch_up['ratio']}倍)が必要"],
  "chart":{"type":"bar","title":"25歳開始 vs 35歳開始(月1万円・65歳時点)","series":["元本","年3%","年5%","年7%"],"data_ref":"age"}},
 {"no":6,"title":"リスクと向き合う:下がる時もある","catch":"暴落は来る。それでも「長期・分散・積立」で乗り越えてきた。",
  "bullets":["S&P500の過去の大きな下落(高値から安値、約):ITバブル後約-49%、リーマン期約-57%、コロナ期(2020年)約-34%。コロナ下落は数か月で戻った一方、リーマン後は高値回復まで数年かかった",
             "歴史的には長期・分散保有で回復してきたが、将来の回復は保証されない。短期で使うお金は投資に回さない",
             f"年3〜7%の幅:月1万円20年で{man(t10_20['invest_3pct'])}〜{man(t10_20['invest_7pct'])}。元本240万円を下回らない保証はないことも理解を"],
  "chart":{"type":"range_band","title":"月1万円×20年:3つのシナリオ幅","series":["元本","年3%","年5%","年7%"],"data_ref":"series_10000_30y(20年目まで)","extra":"過去の暴落率は注釈付き横棒で併記"}},
 {"no":7,"title":"新NISAなら、利益が非課税","catch":"本来20.315%かかる税金が、ゼロに。",
  "bullets":["つみたて投資枠 年120万円+成長投資枠 年240万円(併用可・年360万円)、生涯1,800万円(成長投資枠は1,200万円まで)、非課税期間は無期限",
             f"月1万円20年・年5%の利益約{tax['gain']//10000}万円:通常口座なら税約{tax['tax_normal']//10000}万円、NISAなら0円",
             f"月3万円30年・年5%の利益約{tax2['gain']//10000}万円:通常口座なら税約{tax2['tax_normal']//10000}万円"],
  "chart":{"type":"stacked_bar","title":"通常口座とNISAの手取り比較(月1万円・20年・年5%)","series":["元本","税引後の利益","税金"],"data_ref":"tax"}},
 {"no":8,"title":"今日からできる3ステップ","catch":"完璧なタイミングより、今日の1,000円。",
  "bullets":["①証券口座を開設しNISA口座を申し込む  ②つみたて投資枠で全世界株式またはS&P500のインデックスファンドを選ぶ  ③月1,000円〜で自動積立を設定",
             "余裕資金で、生活防衛資金(目安:生活費3〜6か月分)を確保してから。無理のない金額で長く続ける",
             "※本資料は情報提供で、特定商品の推奨・将来の運用成果の保証ではありません。投資は元本割れの可能性があり、最終判断はご自身で。数値は年率3/5/7%・インフレ2%等の仮定に基づく試算で、税・手数料・信託報酬は考慮していません"],
  "chart":{"type":"steps","title":"3ステップ","note":"アイコン付きステップ図。免責は小さく下部に"}},
]

data = {
 "assumptions": {"compounding":"月次複利(年率は実効年率→月利=(1+r)^(1/12)-1)","contribution_timing":"月末積立",
   "scenarios":{"3%":"保守的","5%":"中位","7%":"過去実績(7〜10%台)の下限寄り"},
   "scenario_basis":"S&P500・オルカンの過去の長期年率は概ね7〜10%台だが将来保証はないため、3/5/7%で保守的に試算",
   "cash_rate":CASH,"inflation":INFL,"real_value":"名目額÷(1.02)^年数","fees_tax":"手数料・信託報酬・税は未考慮(NISA前提)","tax_rate_normal":TAX},
 "pages": pages,
 "tables": table,
 "power_of_money": power, "deposit_1m": deposit,
 "age": age, "age_catch_up": catch_up, "age_diff": age_diff,
 "tax": tax, "tax2": tax2, "nisa": nisa, "stress": stress,
 "extra": {"series_10000_30y": series, "power_and_deposit":{"power":power,"deposit":deposit}},
 "history_notes": {"S&P500_dotcom":"約-49%(2000-2002)","S&P500_lehman":"約-57%(2007-2009)","S&P500_covid":"約-34%(2020年2〜3月、数か月で回復)",
   "note":"高値から安値までの約値。将来の保証なし"},
}
json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
print(json.dumps({"t":[ (t["monthly"],t["years"],t["principal"],t["cash_real"],t["invest_3pct"],t["invest_5pct"],t["invest_7pct"]) for t in table],
 "power":power,"deposit":deposit,"age":age,"catch":catch_up,"tax":tax,"tax2":tax2,"stress":stress}, ensure_ascii=False))
