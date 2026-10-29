"""Workspace identity and visual settings never grant execution authority."""
from contextlib import nullcontext

from app import viewer_render


class RenderProbe:
    def __init__(self):
        self.session_state = {'appearance': 'Light'}
        self.query_params = {}
        self.html_blocks = []
        self.expanders = []
        self.selectboxes = []

    def html(self, value):
        self.html_blocks.append(value)

    def container(self, **kwargs):
        return nullcontext()

    def expander(self, label, **kwargs):
        self.expanders.append((label, kwargs))
        return nullcontext()

    def selectbox(self, label, choices, **kwargs):
        self.selectboxes.append((label, choices, kwargs))


def test_workspace_links_explain_replay_and_session_without_arming_authority(monkeypatch):
    probe = RenderProbe()
    monkeypatch.setattr(viewer_render, 'st', probe)
    viewer_render.workspace_navigation(current='Saved review',
        viewer_url='http://127.0.0.1:8522', session_url='http://127.0.0.1:8523')
    html = probe.html_blocks[0]
    assert 'aria-current="page"' in html
    assert 'workspace-switch' in html
    assert 'Saved review' in html and 'Live session' in html
    assert 'REPLAY' in html and 'New controlled review' in html
    assert '8522/?appearance=Light' in html and '8523/?appearance=Light' in html
    assert 'armed' not in html and 'run_id' not in html
    assert probe.session_state == {'appearance': 'Light'}


def test_display_settings_are_collapsed_and_keep_the_existing_theme_state(monkeypatch):
    probe = RenderProbe()
    monkeypatch.setattr(viewer_render, 'st', probe)
    render = getattr(viewer_render, 'appearance_control', None)
    assert callable(render), 'Appearance needs a compact secondary settings control'
    render()
    assert probe.expanders == [('Display settings', {'expanded': False})]
    assert probe.selectboxes == [('Appearance', ['Auto', 'Light', 'Dark'], {'key': 'appearance'})]
    assert probe.session_state == {'appearance': 'Light'}


def test_identity_uses_an_unboxed_vector_and_escapes_the_subtitle(monkeypatch):
    probe = RenderProbe()
    monkeypatch.setattr(viewer_render, 'st', probe)
    render = getattr(viewer_render, 'render_brand', None)
    assert callable(render), 'The shared identity must replace the boxed letter'
    render(subtitle='<script>untrusted</script>')
    html = probe.html_blocks[0]
    assert 'brand-symbol' in html and 'data:image/svg+xml;base64,' in html
    assert '>B<' not in html and 'brand-mark' not in html
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert 'BioPilot Bench' in html


def test_installed_streamlit_encodes_the_local_vector_favicon_without_network():
    import base64
    from xml.etree import ElementTree

    from streamlit.commands.page_config import _get_favicon_string
    from app.brand import BRAND_ICON, BRAND_SYMBOL

    encoded = _get_favicon_string(BRAND_ICON)
    assert encoded.startswith('data:image/svg+xml;base64,')
    favicon = ElementTree.fromstring(base64.b64decode(encoded.split(',', 1)[1]))
    mark = ElementTree.fromstring(BRAND_SYMBOL)
    ns = '{http://www.w3.org/2000/svg}'
    assert [p.attrib['d'] for p in favicon.iter(ns+'path')] == [
        p.attrib['d'] for p in mark.iter(ns+'path')]
    assert all('href' not in element.attrib for element in favicon.iter())
    assert not list(favicon.iter(ns+'script'))


def test_sidebar_mark_survives_html_sanitization_as_a_self_contained_image(monkeypatch):
    import base64
    from html.parser import HTMLParser
    from xml.etree import ElementTree

    class Images(HTMLParser):
        def __init__(self):
            super().__init__()
            self.images = []

        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                self.images.append(dict(attrs))

    probe = RenderProbe()
    monkeypatch.setattr(viewer_render, 'st', probe)
    viewer_render.render_brand()
    html = probe.html_blocks[0]
    parser = Images()
    parser.feed(html)
    assert len(parser.images) == 1, 'st.html removes inline SVG; use a local SVG image URI'
    image = parser.images[0]
    assert image['class'] == 'brand-symbol'
    assert image['src'].startswith('data:image/svg+xml;base64,')
    svg = base64.b64decode(image['src'].split(',', 1)[1]).decode('utf-8')
    assert ElementTree.fromstring(svg).tag == '{http://www.w3.org/2000/svg}svg'
    assert 'currentColor' not in svg, 'SVG images cannot inherit the page text color'
    assert '<svg' not in html
