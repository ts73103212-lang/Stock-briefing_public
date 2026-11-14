"""3テーマ×4ページの抄録集HTMLを書き出す。python3 build/build.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kit, theme1, theme2, theme3  # noqa: E402

out = Path(__file__).parent.parent / "kabukura_2026-11-13.html"
sheets = theme1.pages() + theme2.pages() + theme3.pages()
out.write_text(kit.document("株クラ秋季研究会 抄録集", sheets), encoding="utf-8")
print(out, len(sheets))
