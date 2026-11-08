import pytest

from note_pipeline import lint


@pytest.mark.parametrize("text", ["今が買い場です", "目標株価は3000円", "ここで損切りします", "今がチャンス", "この銘柄を推奨します"])
def test_detects_recommendation(text):
    assert lint.check_text(text)


@pytest.mark.parametrize("text", ["特定の銘柄の売買を推奨するものではありません", "その後買い戻しが入った",
                                  "ニューヨークは買われた", "🐾投資判断はご自身で🐾"])
def test_allows_neutral(text):
    assert lint.check_text(text) == []


def test_xpost_length_and_tags():
    problems = lint.check_xpost("あ" * 141 + " #a #b #c")
    assert len(problems) == 2


def test_xpost_ok():
    assert lint.check_xpost("日経平均は−893円。約半分はたった2銘柄でした🐾\n#日本株 #米中間選挙") == []
