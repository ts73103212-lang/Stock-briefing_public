"""Noto Sans JP の静的フォント（Regular 400 / Bold 700）を用意して matplotlib に登録する。

matplotlib は可変フォントを細字（Thin）で描画してしまうため、fontTools で
wght 軸を固定した静的フォントを作ってから使う。
"""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path

VF_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"
FAMILY = "Noto Sans JP"
WEIGHTS = {"regular": 400, "bold": 700}
_registered: dict[str, Path] | None = None


def default_cache_dir() -> Path:
    return Path(os.environ.get("NOTE_PIPELINE_CACHE", Path.home() / ".cache" / "note_pipeline")) / "fonts"


def _instantiate(vf_path: Path, weight: int, out: Path) -> None:
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    font = TTFont(vf_path)
    static = instantiateVariableFont(font, {"wght": weight}, updateFontNames=False)
    static["OS/2"].usWeightClass = weight
    if weight >= 700:
        static["OS/2"].fsSelection = (static["OS/2"].fsSelection | 0x20) & ~0x40  # BOLD, not REGULAR
        static["head"].macStyle |= 0x1
    static.save(out)


def ensure_fonts(cache_dir: Path | None = None) -> dict[str, Path]:
    """静的フォントを（なければ作って）返し、matplotlib に登録する。"""
    global _registered
    cache = Path(cache_dir) if cache_dir else default_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    paths = {k: cache / f"NotoSansJP-{w}.ttf" for k, w in WEIGHTS.items()}
    if not all(p.exists() for p in paths.values()):
        vf = cache / "NotoSansJP-VF.ttf"
        if not vf.exists():
            tmp = vf.with_suffix(".part")
            urllib.request.urlretrieve(VF_URL, tmp)
            tmp.rename(vf)
        for k, w in WEIGHTS.items():
            if not paths[k].exists():
                _instantiate(vf, w, paths[k])
    if _registered != paths:
        import matplotlib
        from matplotlib import font_manager

        for p in paths.values():
            font_manager.fontManager.addfont(str(p))
        matplotlib.rcParams["font.family"] = FAMILY
        matplotlib.rcParams["axes.unicode_minus"] = False
        _registered = paths
    return paths
