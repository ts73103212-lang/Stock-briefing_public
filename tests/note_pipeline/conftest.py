import pytest
from note_pipeline import fonts

@pytest.fixture(scope="session", autouse=True)
def _fonts():
    return fonts.ensure_fonts()
