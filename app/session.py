"""Live review session. This surface CAN spend, and says so on screen.

Deliberately a separate entry point from app/viewer.py. The replay viewer is asserted
to contain no network or subprocess capability, so opening a saved run provably cannot
dispatch work. Rather than weaken that guarantee to add a button, the capability lives
here, behind an explicit arming step and a hard run budget.

One chat turn is one bounded run. That keeps the conversation honest: every answer on
screen is backed by its own immutable run and its own artifact, rather than by a
growing context the operator cannot audit.

Run: .venv/Scripts/python.exe -m streamlit run app/session.py -- --esm-env <file>
"""
import argparse
from pathlib import Path
import sys
import re
import subprocess
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from app.session_exec import (PROTECTED_FULL_POSITIONS, SessionBudget, extract_positions,
                              run_session, validate_session_request)
from app.viewer_data import CLAIM_BANNER, format_candidate_rows, load_run_view
from app.viewer_render import (appearance_control, handoff_ladder, init_appearance,
                               render_brand, workspace_navigation, palette_css)
from app.brand import BRAND_ICON
from app.viewer_structure import residue_selection, structure_panel_html
from app.review_checks import check_review_input

ROOT = Path(__file__).resolve().parents[1]


def _arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--esm-env', default='.cache/local_esm150_verified.env')
    parser.add_argument('--max-runs', type=int, default=3)
    parser.add_argument('--max-requests', type=int, default=4)
    parser.add_argument('--viewer-url', default='http://127.0.0.1:8520',
                        help='Where the separate read-only replay program is served')
    parser.add_argument('--session-url', default='http://127.0.0.1:8521',
                        help='This live-session surface URL, for shared navigation')
    known, _ = parser.parse_known_args(sys.argv[1:])
    return known


def _style(appearance):
    css = (ROOT / 'app' / 'viewer.css').read_text(encoding='utf-8')
    from app.viewer import PALETTES
    st.html('<style>' + palette_css(appearance, PALETTES) + css + '</style>')


def _budget(options):
    if 'session_budget' not in st.session_state:
        st.session_state['session_budget'] = SessionBudget(
            max_runs=options.max_runs, max_requests_per_run=options.max_requests)
    return st.session_state['session_budget']


def _render_result(report_path):
    view = load_run_view(report_path)
    st.caption(f"{view['status']} · model {view['actual_model'] or 'unavailable'} · "
               f"{view['meta_request_attempts']} model requests")
    handoff_ladder(view['decision_steps'], heading='What just happened')
    rows = format_candidate_rows(view['candidates'])
    if rows:
        left, right = st.columns([3, 2])
        with left:
            st.table([{key: row[key] for key in ('rank', 'candidate_id', 'score', 'full_position')}
                      for row in rows])
            st.caption('Ranked by the registered common policy, computed by code.')
        with right:
            selection = residue_selection(rows[0]['full_position'])
            if selection['status'] != 'observed':
                st.warning(selection['note'])
            components.html(structure_panel_html(highlight=selection, height=280,
                appearance=st.session_state.get('appearance', 'Dark')), height=365)
    if view['model_narrative']:
        with st.expander('Recorded model explanation'):
            st.text(view['model_narrative'])
    with st.expander('Scientific limits'):
        st.text(CLAIM_BANNER)


def _say(role, text, **extra):
    st.session_state.setdefault('turns', []).append({'role': role, 'text': text, **extra})


def _replay_turns():
    for turn in st.session_state.get('turns', []):
        with st.chat_message(turn['role']):
            st.markdown(turn['text'])
            if turn.get('report'):
                _render_result(turn['report'])


def _handle(message, options, budget, model_key, armed):
    """One chat turn is one bounded run. Refusals happen locally and cost nothing."""
    _say('user', message)
    if re.search(r'\bmature\b|성숙체|성숙\s*(?:서열|번호)', message, re.IGNORECASE):
        _say('assistant', 'Please declare full-reference 1-based numbering. An explicit mature '
             'frame is refused locally; nothing was sent and this check cost nothing.')
        return
    for token in re.findall(r'(?<![A-Za-z0-9])[ACDEFGHIKLMNPQRSTVWY]\d{1,3}[ACDEFGHIKLMNPQRSTVWY](?![A-Za-z0-9])', message):
        checked = check_review_input(token, 'full_reference_1based', 'sequence_plausibility_review')
        if checked['status'] != 'accepted':
            _say('assistant', f'**refused** `{token}`: {checked["message"]}. Nothing was sent; this check cost nothing.')
            return
    found = extract_positions(message)
    if not found:
        _say('assistant', 'I could not read a full-reference position from that. Name one, '
                          'for example `A32V` or `position 45`. Nothing was sent.')
        return
    protected = ', '.join(str(p) for p in PROTECTED_FULL_POSITIONS)
    try:
        positions = validate_session_request(found, model_key)
    except ValueError as error:
        _say('assistant',
             f'I read positions `{found}` from your message and **refused** before anything '
             f'was sent: {error}.' + '\n\n' +
             'This refusal cost nothing. The guard is local code, not the model choosing to '
             f'behave. Protected catalytic sites are {protected}.')
        return
    if not armed:
        _say('assistant',
             f'I read positions `{positions}` with checkpoint `{model_key}`. The session is '
             '**unarmed**, so the review command is built without live flags and nothing is '
             'sent. Arm it in the sidebar to run this turn.')
        return
    try:
        budget.check()
    except ValueError as error:
        _say('assistant', f'**{error}**')
        return
    workspace = ROOT / '.runtime' / ('chat_' + uuid4().hex)
    try:
        with st.spinner('Running one bounded review…'):
            result = run_session(ROOT, workspace, positions=positions, model_key=model_key,
                                 esm_env=options.esm_env, budget=budget, armed=True,
                                 goal_text=message)
    except (ValueError, OSError, TimeoutError, subprocess.TimeoutExpired) as error:
        _say('assistant', 'The review stopped before a result was available: ' + str(error)[:500] +
             '. Existing evidence is preserved. Check the run record before retrying.')
        return
    if result['returncode'] != 0:
        detail = (result['stderr'] or 'no error text')[-800:]
        _say('assistant', f"The {result['stage']} step failed:" + '\n\n```\n' + detail + '\n```')
        return
    report = workspace / 'live_report.json'
    report.write_text(result['stdout'], encoding='utf-8')
    _say('assistant',
         f'Reviewed positions `{positions}` with `{model_key}`. Your sentence was passed '
         'through as untrusted context; the approved cohort came from the frozen run, not '
         'from the text.', report=str(report))


def _draft(text):
    """Examples prepare an editable request; they never submit or arm a run."""
    st.session_state['chat_draft'] = text


def main():
    options = _arguments()
    st.set_page_config(page_title='BioPilot Bench · Live session', page_icon=BRAND_ICON,
                       layout='wide', initial_sidebar_state='auto')
    init_appearance()
    _style(st.session_state['appearance'])
    budget = _budget(options)

    with st.sidebar:
        render_brand(subtitle='CONTROLLED SESSION')
        workspace_navigation(current='Live session', viewer_url=options.viewer_url,
                             session_url=options.session_url)
        st.markdown('**Run controls**')
        st.metric('Runs left', f'{budget.remaining_runs} of {options.max_runs}')
        st.caption(f'Each run is capped at {options.max_requests} model requests. The cap is '
                   'enforced in code, not by the model, and this screen cannot raise it.')
        model_key = st.selectbox('Checkpoint', ['esm150', 'esm650'], key='model_key',
                                 help='One checkpoint per run; a run never mixes rank policies.')
        armed = st.checkbox('Arm paid runs', key='armed', value=False)
        st.caption('Armed. The next accepted request will spend one run.' if armed else
                   'Unarmed — the review command is built without live flags.')
        st.html('<div class="guard-chips"><span>S108</span><span>D164</span><span>H187</span></div>')
        st.caption('Protected sites are refused locally, before any request is built.')
        appearance_control()

    st.html('<div class="workspace-kicker">PUBLIC LIPASE A '
            '<span class="workspace-mode">LIVE SESSION · ' + ('ARMED' if armed else 'UNARMED') + '</span></div>')
    st.title('Ask for a review')
    st.caption('Meta selects permitted tools. ESM computes sequence preferences. Registered code guards and ranks.')
    if armed:
        st.warning('Armed · the next accepted request can spend real credit within the displayed run cap.')
    else:
        st.info('Unarmed · prepare and check a request here. Enable paid runs in the sidebar to execute.')
    if not st.session_state.get('turns'):
        st.subheader('What would you like to inspect?')
        with st.container(key='session_examples'):
            valid, protected, another = st.columns(3)
            for column, label, key, text, detail in (
                (valid, 'Review a variant', 'draft_valid', 'Review A32V for sequence plausibility.',
                 'Start with the registered Lipase A reference.'),
                (protected, 'Try a protected site', 'draft_guard', 'Review S108A for sequence plausibility.',
                 'See the local guard refuse a protected mutation.'),
                (another, 'Review another position', 'draft_position', 'Review position 45 for sequence plausibility.',
                 'Keep full-reference 1-based numbering.')):
                with column:
                    with st.container(border=True):
                        st.button(label, key=key, on_click=_draft, args=(text,), width='stretch')
                        st.caption(detail)
        st.caption('Examples fill the message box. Read or edit the request before sending.')
    _replay_turns()
    with st.expander('Execution boundaries and scientific scope'):
        st.warning('This program can call the Meta Model API and spend real credit. The '
                   'saved-run viewer is a separate program that provably cannot.')
        st.caption('Each message starts a separate bounded run. ESM scores are not T50, activity, '
                   'solubility, Tm or experimental validation. The registered target stays fixed.')
    message = st.chat_input('Describe a variant or full-reference position…', key='chat_draft')
    if message:
        _handle(message, options, budget, model_key, armed)
        st.rerun()


if __name__ == '__main__':
    main()
