"""Presentation shared by the replay viewer and the live session surface.

Pure rendering over an already-built read model. No provider, inference, network or
subprocess access, so importing this module can never cause work to be dispatched.
Both surfaces read the same artifact shape, so a saved replay and a run that is still
growing are drawn by exactly the same code.
"""
from html import escape

import streamlit as st

from app.brand import brand_symbol_data_uri


def render_brand(*, subtitle='SCIENTIFIC REVIEW'):
    """One restrained identity for saved and controlled-review workspaces."""
    icon = brand_symbol_data_uri(init_appearance())
    st.html('<div class="brand"><img class="brand-symbol" src="' + icon +
            '" alt="" aria-hidden="true" width="36" height="36"/>' +
            '<div class="brand-wordmark"><strong>BioPilot Bench</strong><small>' +
            escape(subtitle) + '</small></div></div>')


def appearance_control():
    """Keep theme selection available as a secondary, initially closed setting."""
    with st.container(key='display_settings'), st.expander('Display settings', expanded=False):
        st.selectbox('Appearance', ['Auto', 'Light', 'Dark'], key='appearance')


def init_appearance():
    """Carry appearance between isolated workspace pages, never live authority."""
    if 'appearance' not in st.session_state:
        selected = st.query_params.get('appearance', 'Auto')
        st.session_state['appearance'] = selected if selected in ('Auto', 'Dark', 'Light') else 'Auto'
    return st.session_state['appearance']


def workspace_navigation(*, current, viewer_url, session_url):
    """One workspace navigation, two capability-isolated local programs."""
    appearance = init_appearance()
    links = []
    for label, url, badge, hint in (
            ('Saved review', viewer_url, 'REPLAY', 'Saved evidence · no new inference'),
            ('New Review', session_url, 'SESSION', 'New controlled review')):
        if current == 'Live session':
            current = 'New Review'
        active = ' active' if current == label else ''
        current_page = ' aria-current="page"' if current == label else ''
        # Links carry a visual preference only; they cannot arm a live session.
        target = url.split('?')[0].rstrip('/') + '/?appearance=' + appearance
        links.append(f'<a class="workspace-item{active}" href="{escape(target, quote=True)}" '
                     f'target="_self" title="{badge} · {hint}"{current_page}>'
                     f'<span class="workspace-label">{label}</span></a>')
    st.html('<nav class="workspace-nav workspace-switch" aria-label="Workspace">' + ''.join(links) + '</nav>')

LADDER_CAPTION = (
    'Saved order. The model selects permitted tools; registered code performs every '
    'computation, guard and ranking. Model turns show public accounting only — '
    'reply length, never reply text.')


def _model_detail(step):
    usage = step.get('usage') or {}
    parts = ['finish: ' + step['finish_reason']]
    if 'completion_tokens' in usage:
        parts.append(f"{usage['completion_tokens']} completion tokens")
    if step.get('elapsed_seconds') is not None:
        parts.append(f"{step['elapsed_seconds']}s")
    if step.get('content_chars') is not None:
        parts.append(f"{step['content_chars']}-char reply")
    return parts


def _code_detail(step):
    parts = ['result: ' + str(step['result'].get('status', 'unavailable'))]
    if step.get('reason_brief'):
        parts.append(step['reason_brief'])
    return parts


def handoff_ladder(steps, *, heading='Recorded handoffs', caption=LADDER_CAPTION):
    """Both actors in saved order: the model asks, registered code computes."""
    if not steps:
        return
    st.markdown(f'**{heading}**')
    if caption:
        st.caption(caption)
    rungs = ['<ol class="ladder">']
    for step in steps:
        model_turn = step['kind'] == 'meta_response'
        parts = _model_detail(step) if model_turn else _code_detail(step)
        rungs.append(
            '<li class="rung ' + ('rung-model' if model_turn else 'rung-code') + '">'
            '<span class="rung-step">' + str(step['step']).zfill(2) + '</span>'
            '<span class="rung-body">'
            '<span class="rung-actor">' + escape(step['actor']) + '</span>'
            '<span class="rung-label">' + escape(step['label']) + '</span>'
            '<span class="rung-detail">' + escape(' · '.join(parts)) + '</span>'
            '</span></li>')
    rungs.append('</ol>')
    st.html(''.join(rungs))


def palette_css(appearance, palettes):
    """Follow system appearance in CSS without inference or provider calls."""
    if appearance == 'Auto':
        return ':root{' + palettes['Light'] + '}@media(prefers-color-scheme:dark){:root{' + palettes['Dark'] + '}}'
    return ':root{' + palettes[appearance] + '}'
