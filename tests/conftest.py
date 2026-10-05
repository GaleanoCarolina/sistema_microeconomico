import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from database.migrate import migrate

@pytest.fixture
def db(tmp_path):
    path=tmp_path/'test.db'; migrate(path); return path
