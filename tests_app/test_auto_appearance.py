from types import SimpleNamespace
from app import viewer_render


def test_unset_appearance_defaults_to_auto(monkeypatch):
    fake = SimpleNamespace(session_state={}, query_params={})
    monkeypatch.setattr(viewer_render, 'st', fake)
    assert viewer_render.init_appearance() == 'Auto'


def test_explicit_theme_survives_navigation(monkeypatch):
    fake = SimpleNamespace(session_state={}, query_params={'appearance': 'Light'})
    monkeypatch.setattr(viewer_render, 'st', fake)
    assert viewer_render.init_appearance() == 'Light'


def test_auto_uses_system_media_query_and_structure_changes_locally():
    from app.viewer_structure import structure_panel_html
    css = viewer_render.palette_css('Auto', {'Light': '--mode:light;', 'Dark': '--mode:dark;'})
    assert '@media(prefers-color-scheme:dark)' in css
    assert '--mode:light' in css and '--mode:dark' in css
    html = structure_panel_html(appearance='Auto')
    assert 'matchMedia' in html and "addEventListener('change'" in html
