"""Contrast is asserted on the surfaces people actually click, in both themes.

An earlier pass measured text contrast only and reported a passing number while the
button surface sat at 1.06:1 against the page, so buttons read as flat text in Light.
These tests measure the control boundaries as well, so that cannot recur silently.

WCAG 2.1: 4.5:1 for body text, 3:1 for the boundary of a user-interface component.
"""
import pytest

from app.viewer import PALETTES

BODY_MIN = 4.5
CONTROL_MIN = 3.0


def _tokens(palette):
    pairs = [chunk.split(':', 1) for chunk in palette.split(';') if ':' in chunk]
    return {name.strip().lstrip('-'): value.strip() for name, value in pairs}


def _relative_luminance(hex_colour):
    raw = hex_colour.lstrip('#')
    channels = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    lighter, darker = sorted((_relative_luminance(a), _relative_luminance(b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize('theme', sorted(PALETTES))
def test_native_widgets_follow_the_selected_theme(theme):
    """A fixed color-scheme renders dark inputs and scrollbars on a light page."""
    tokens = _tokens(PALETTES[theme])
    assert tokens['scheme'] == theme.lower()


@pytest.mark.parametrize('theme', sorted(PALETTES))
def test_clickable_boundaries_are_visible_in_both_themes(theme):
    tokens = _tokens(PALETTES[theme])
    for surface in ('raised', 'input', 'panel'):
        ratio = contrast(tokens['edge'], tokens[surface])
        assert ratio >= CONTROL_MIN, f'{theme}: edge vs {surface} is {ratio:.2f}:1'
    ratio = contrast(tokens['edge'], tokens['bg'])
    assert ratio >= CONTROL_MIN, f'{theme}: edge vs page is {ratio:.2f}:1'


@pytest.mark.parametrize('theme', sorted(PALETTES))
def test_text_is_readable_on_every_surface_it_lands_on(theme):
    tokens = _tokens(PALETTES[theme])
    for surface in ('bg', 'panel', 'raised', 'input'):
        ratio = contrast(tokens['text'], tokens[surface])
        assert ratio >= BODY_MIN, f'{theme}: text vs {surface} is {ratio:.2f}:1'
    for surface in ('bg', 'panel'):
        ratio = contrast(tokens['muted'], tokens[surface])
        assert ratio >= BODY_MIN, f'{theme}: muted vs {surface} is {ratio:.2f}:1'


@pytest.mark.parametrize('theme', sorted(PALETTES))
def test_accent_and_danger_stay_readable_on_their_own_tints(theme):
    tokens = _tokens(PALETTES[theme])
    assert contrast(tokens['accent'], tokens['accent-soft']) >= BODY_MIN
    assert contrast(tokens['accent'], tokens['bg']) >= BODY_MIN
    assert contrast(tokens['danger'], tokens['danger-soft']) >= BODY_MIN
