"""Original local identity assets; no remote fonts, images or executable content."""
import base64
from pathlib import Path


_ASSETS = Path(__file__).resolve().parent / 'assets' / 'brand'
BRAND_SYMBOL = (_ASSETS / 'fold-mark.svg').read_text(encoding='utf-8')
BRAND_ICON = _ASSETS / 'favicon.svg'


def brand_symbol_data_uri(appearance):
    """An image URI survives HTML sanitizing and carries its own theme color."""
    color = '#28988a' if appearance == 'Auto' else ('#00695c' if appearance == 'Light' else '#6ce4cb')
    svg = BRAND_SYMBOL.replace('currentColor', color)
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii')
