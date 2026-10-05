from pathlib import Path

def test_editable_catalogs_have_visible_dropdown_button():
    root=Path(__file__).resolve().parents[1]
    dialogs=(root/'views/components/dialogs.py').read_text(encoding='utf-8')
    theme=(root/'views/components/theme.py').read_text(encoding='utf-8')
    assert "_editable_catalog_field(self.category" in dialogs
    assert "_editable_catalog_field(self.unit" in dialogs
    assert "comboDropButton" in theme
    assert "lista editable" in dialogs
