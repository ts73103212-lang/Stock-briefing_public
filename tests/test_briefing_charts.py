"""briefing_charts.fetch の「日足の最新足が欠けたときの補完」のテスト（ネットワークなし）。"""
import pandas as pd

import briefing_charts as bc

COLS = ["Open", "High", "Low", "Close", "Volume"]


def _daily(dates):
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="Date")
    return pd.DataFrame([[100, 110, 90, 105, 1000]] * len(dates), index=idx, columns=COLS)


def _hourly(day, rows):
    idx = pd.DatetimeIndex([pd.Timestamp(f"{day} {h:02d}:00", tz="Asia/Tokyo") for h, *_ in rows],
                           name="Datetime")
    return pd.DataFrame([r[1:] for r in rows], index=idx, columns=COLS)


def _patch(monkeypatch, daily, hourly):
    def fake_download(ticker, period, interval, **kw):
        return (daily if interval == "1d" else hourly).copy()
    monkeypatch.setattr(bc.yf, "download", fake_download)


HOURS = [(9, 1148, 1189, 1133, 1160, 100), (14, 1160, 1224, 1146, 1221, 200),
         (15, 1224, 1300, 1224, 1295, 300)]


def test_missing_latest_daily_bar_is_filled_from_intraday(monkeypatch):
    _patch(monkeypatch, _daily(["2026-11-16", "2026-11-17"]), _hourly("2026-11-18", HOURS))
    df, patched = bc.fetch("4418")
    assert df.index[-1] == pd.Timestamp("2026-11-18")
    assert patched == ["2026-11-18"]
    last = df.iloc[-1]
    assert (last["Open"], last["High"], last["Low"], last["Close"], last["Volume"]) == \
        (1148, 1300, 1133, 1295, 600)


def test_close_and_volume_override_from_screening(monkeypatch):
    # 60分足には引けの板寄せが入らないため、終値・出来高はスクリーニング値（TradingView）を優先
    _patch(monkeypatch, _daily(["2026-11-17"]), _hourly("2026-11-18", HOURS))
    df, _ = bc.fetch("4418", latest={"close": 1281.0, "volume": 1281700})
    last = df.iloc[-1]
    assert (last["Close"], last["Volume"]) == (1281.0, 1281700)
    assert last["Low"] <= 1281.0 <= last["High"]


def test_no_patch_when_daily_is_up_to_date(monkeypatch):
    _patch(monkeypatch, _daily(["2026-11-17", "2026-11-18"]), _hourly("2026-11-18", HOURS))
    df, patched = bc.fetch("4418", latest={"close": 1.0, "volume": 1})
    assert patched == []
    assert df.iloc[-1]["Close"] == 105  # 日足が揃っていればスクリーニング値で上書きしない


def test_intraday_failure_keeps_daily(monkeypatch):
    daily = _daily(["2026-11-17"])

    def fake_download(ticker, period, interval, **kw):
        if interval == "1d":
            return daily.copy()
        raise RuntimeError("intraday down")
    monkeypatch.setattr(bc.yf, "download", fake_download)
    df, patched = bc.fetch("4418")
    assert df.index[-1] == pd.Timestamp("2026-11-17") and patched == []
