"""mailmag_charts の判定・米日対応づけ・添付組み立てのテスト（ネットワークなし）。"""
import numpy as np
import pandas as pd

import mailmag_charts as mc

COLS = ["Open", "High", "Low", "Close", "Volume"]


def _daily(closes, vols=None, start="2026-01-05"):
    idx = pd.bdate_range(start, periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    v = pd.Series(vols if vols is not None else [1000] * len(closes), index=idx, dtype=float)
    return pd.DataFrame({"Open": c.shift(1).fillna(c.iloc[0]), "High": c * 1.01, "Low": c * 0.99,
                         "Close": c, "Volume": v})[COLS]


def test_uptrend_with_volume_is_shobu():
    closes = list(np.linspace(1000, 1500, 200))
    vols = [1000] * 199 + [3000]
    s = mc.jp_signals(_daily(closes, vols))
    assert s["verdict"] == "勝負"
    assert s["weekly_up"] and s["daily_aligned"]
    assert s["vol_ratio"] == 3.0
    assert s["close"] == 1500.0


def test_downtrend_is_miokuri():
    s = mc.jp_signals(_daily(list(np.linspace(1500, 1000, 200))))
    assert s["verdict"] == "見送り"
    assert "25日線の下で下向き" in s["tags"]


def test_rebound_in_downtrend_is_yousumi():
    closes = list(np.linspace(3000, 1000, 199)) + [1040]
    s = mc.jp_signals(_daily(closes, [1000] * 199 + [1500]))
    assert s["verdict"] == "様子見"
    assert any(t.startswith("反発初動") for t in s["tags"])


def test_align_next_day_uses_previous_us_session():
    us = pd.Series([100, 110, 121], index=pd.to_datetime(["2026-03-02", "2026-03-03", "2026-03-04"]))
    jp = pd.Series([1000, 1010, 1020], index=pd.to_datetime(["2026-03-03", "2026-03-04", "2026-03-05"]))
    a = mc.align_next_day(us, jp)
    # 日本の 3/3 には米国の 3/2（前日）の終値が当たる。同じ日付は当てない
    assert list(a["us"]) == [100, 110, 121]
    assert list(a.index.strftime("%m-%d")) == ["03-03", "03-04", "03-05"]


def test_pair_stats_beta():
    rng = np.random.default_rng(0)
    r_us = rng.normal(0, 0.02, 80)
    us = pd.Series(100 * np.cumprod(1 + r_us))
    jp = pd.Series(1000 * np.cumprod(1 + 0.5 * r_us))
    a = pd.DataFrame({"us": us.values, "jp": jp.values})
    st = mc.pair_stats(a, us_last_change_pct=2.0)
    assert abs(st["beta"] - 0.5) < 0.01 and st["corr"] > 0.99
    assert abs(st["implied_jp_pct"] - 1.0) < 0.02


def test_finalize_orders_attachments_and_handles_missing():
    manifest = {"jp_8035": {"file": "jp_8035.png", "path": "/r/jp_8035.png", "sha256": "a" * 64},
                "us_NVDA": {"file": "us_NVDA.png", "path": "/r/us_NVDA.png", "sha256": "b" * 64}}
    html = "x{{chart:us_NVDA}}y{{chart:jp_8035}}z{{chart:jp_9999}}w{{chart:us_NVDA}}"
    final, atts, noimg = mc.finalize(html, manifest)
    assert [a["filename"] for a in atts] == ["us_NVDA.png", "jp_8035.png"]
    assert atts[0]["content"] == f"sha256:{'b' * 64}:/r/us_NVDA.png" and atts[0]["inline"] is True
    assert final.count('cid:att0') == 2 and 'cid:att1' in final
    assert "チャート取得不可" in final
    assert noimg == "xyzw"
