from pathlib import Path


def test_arrow_combobox_does_not_open_popup_manually_on_mouse_press():
    src = (Path(__file__).parents[1] / "views" / "components" / "widgets.py").read_text(encoding="utf-8")
    start = src.index("class ArrowComboBox")
    end = src.index("class KPIButton")
    block = src[start:end]
    assert "self.showPopup()" not in block
    assert "super().mousePressEvent(event)" in block
