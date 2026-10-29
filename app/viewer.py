"""Local saved-run workbench. Viewing and input checks never dispatch scientific work.

Run: .venv/Scripts/python.exe -m streamlit run app/viewer.py -- --artifact <path.json>
"""
import argparse
from html import escape
from pathlib import Path
import sys
import time

import streamlit as st
import streamlit.components.v1 as components

from app.review_checks import check_review_input
from app.viewer_data import (CLAIM_BANNER, PROVENANCE_CHAIN_SCOPE as CHAIN_SCOPE,
                             candidate_csv, format_candidate_rows,
                             load_run_view, select_candidate_rows)
from app.upload_checks import (MAX_SEQUENCE_BYTES, MAX_STRUCTURE_BYTES,
                               check_sequence, check_structure)
from app.viewer_render import (appearance_control, handoff_ladder, init_appearance,
                               render_brand, workspace_navigation, palette_css)
from app.brand import BRAND_ICON
from app.viewer_structure import residue_selection, structure_panel_html, verify_reference, sequence_neighborhood
from app.guided_tour import (STEPS, advance_tour, set_tour_playing, start_tour,
                             stop_tour, tick_tour)
from app.core.atlas_snapshot import load_registered_atlas_snapshot
from app.tour_spotlight import spotlight_document
from app.prediction_view import load_predictions


# --line is the quiet divider; --edge is the border of anything clickable and must
# clear 3:1 against its own surface, or buttons read as flat text. --scheme drives
    # the browser's native widgets: a fixed value renders dark inputs on a light page.
PALETTES = {
    'Dark': '--scheme:dark;--bg:#0b0f14;--panel:#121820;--raised:#19222c;--text:#eef2f6;--muted:#a4b0be;--line:#2b3643;--edge:#64748b;--accent:#6ce4cb;--accent-soft:#12362f;--input:#17202a;--danger:#ffb3b3;--danger-soft:#351d24;',
    'Light': '--scheme:light;--bg:#eef2f7;--panel:#ffffff;--raised:#ffffff;--text:#0f172a;--muted:#475569;--line:#cbd5df;--edge:#64748b;--accent:#00695c;--accent-soft:#d4efe9;--input:#ffffff;--danger:#9f1239;--danger-soft:#fff1f2;',
    }


def _artifact_argument():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True, help='Saved run report JSON')
    parser.add_argument('--session-url', default='http://127.0.0.1:8521',
                        help='Where the separate live session program is served')
    parser.add_argument('--workspace-url', default='http://127.0.0.1:8520',
                        help='This saved-review surface URL, for shared navigation')
    known, _ = parser.parse_known_args(sys.argv[1:])
    return known


def _style(appearance):
    css = Path(__file__).with_suffix('.css').read_text(encoding='utf-8')
    st.html('<style>' + palette_css(appearance, PALETTES) + css + '</style>')


def _try_example(variant):
    st.session_state['local_variant'] = variant
    st.session_state['local_frame'] = 'full_reference_1based'
    st.session_state['local_objective'] = 'sequence_plausibility_review'
    st.session_state['local_check_result'] = check_review_input(
        variant, 'full_reference_1based', 'sequence_plausibility_review')


def _set_comparison(candidate_ids):
    st.session_state['compare_candidates'] = list(candidate_ids)


def _sync_candidate(rows):
    candidate = next(r for r in rows if r['candidate_id'] == st.session_state['focused_candidate'])
    st.session_state['structure_focus'] = f"{candidate['candidate_id']} · full {candidate['full_position']}"


def _sync_structure(choices):
    row = next(c[2] for c in choices if c[0] == st.session_state['structure_focus'])
    if row is not None:
        st.session_state['focused_candidate'] = row['candidate_id']


def _open_candidate_structure(rows):
    _sync_candidate(rows)
    _navigate_view('Structure')


def _candidate_focus(rows):
    ids = [row['candidate_id'] for row in rows]
    if not ids:
        return
    if st.session_state.get('focused_candidate') not in ids:
        st.session_state['focused_candidate'] = ids[0]
    st.selectbox('Candidate to inspect', ids, key='focused_candidate',
                 on_change=_sync_candidate, args=(rows,),
                 help='Shared with Structure. Inspection never changes ranks or calls a model.')


def _move_trace(delta, count):
    st.session_state['trace_step'] = max(0, min(
        count - 1, st.session_state.get('trace_step', 0) + delta))


def _sidebar(view, session_url, workspace_url):
    task = view['task_context']
    with st.sidebar:
        render_brand()
        workspace_navigation(current='Saved review', viewer_url=workspace_url,
                             session_url=session_url)
        st.markdown('**Reference workspace**')
        st.text('Public Lipase A' if task['reference_id'] == 'ESTA_BACSU_Nutschel_2020'
                else 'Saved reference')
        st.caption('Full positions: ' + (', '.join(str(position) for position in task['positions'])
                                       or 'Unavailable'))
        with st.expander('Saved input details'):
            st.text(task['reference_id'] or 'Reference ID not recorded')
            st.caption('Original goal profile')
            st.text(task['objective_id'] or 'Unavailable in this saved report')
            st.caption('Additional user constraints / approvals')
            st.text('Unavailable in this saved report' if task['additional_constraints'] is None
                    else str(task['additional_constraints']))
        st.markdown('**Registered guardrails**')
        st.caption('Full-reference 1-based · full_212 context')
        st.html('<div class="guard-chips"><span>S108</span><span>D164</span><span>H187</span></div>')
        st.caption('Protection does not establish retained function.')
        appearance_control()
        st.caption('Saved review · offline playback')


def _input(view):
    st.subheader('Input & local diagnostics')
    st.caption('Check a variant against the registered reference. This local check does not change the saved result.')
    entry, context = st.columns([3, 2], gap='large')
    with entry, st.container(key='tour_input'):
        examples = st.columns(3)
        for column, variant in zip(examples, ('A32V', 'S108A', 'G32V')):
            column.button(variant, key='example_' + variant, width='stretch',
                          on_click=_try_example, args=(variant,))
        with st.form('offline_check'):
            variant = st.text_input('Variant', 'A32V', key='local_variant', max_chars=32)
            frame = st.selectbox('Declared numbering',
                ['full_reference_1based', 'mature_1based'], key='local_frame',
                format_func=lambda value: {'full_reference_1based': 'Full reference · 1-based',
                    'mature_1based': 'Mature sequence · 1-based'}[value])
            objective = st.selectbox('Goal for local check',
                ['sequence_plausibility_review', 'lipase_T50_hypothesis_review',
                 'activity_optimization'], key='local_objective',
                format_func=lambda value: {'sequence_plausibility_review': 'Sequence preferences',
                    'lipase_T50_hypothesis_review': 'T50 hypothesis · unvalidated',
                    'activity_optimization': 'Activity optimization · unsupported'}[value])
            submitted = st.form_submit_button('Check input locally', width='stretch', type='primary')
        if submitted:
            st.session_state['local_check_result'] = check_review_input(variant, frame, objective)
        result = st.session_state.get('local_check_result')
        if result:
            (st.success if result['status'] == 'accepted' else st.error)(result['message'])
            checked = result['variant']
            checked = checked.get('candidate_id') if isinstance(checked, dict) else checked
            st.caption(f'Last checked: {checked} · local guard · no model call or inference')
            with st.expander('Local check output'):
                st.json(result, expanded=False)
    with context:
        st.html('<div class="input-summary"><span class="section-kicker">REGISTERED TARGET</span>'
                '<h3>Public Lipase A</h3><p>212 residues · full-reference numbering</p>'
                '<p>Sequence plausibility review</p><hr><p>Protected sites</p>'
                '<div class="guard-chips"><span>S108</span><span>D164</span><span>H187</span></div>'
                '<p>Try A32V to pass, S108A to see site protection, or G32V to catch a reference mismatch.</p></div>')
    with st.expander('Advanced diagnostics · FASTA and mmCIF'):
        _uploads(view)


def _candidate_table(rows, *, key):
    # A semantic table follows the selected palette. Streamlit's native canvas
    # retains its startup theme even when the application palette changes.
    with st.container(key=key):
        st.table([{label: row[field] for field, label in (
            ('rank', 'Rank'), ('candidate_id', 'Variant'), ('score', 'ESM preference'),
            ('full_position', 'Full position'), ('wild_type', 'WT'), ('mutant', 'Substitution'))}
            for row in rows])


def _overview(view):
    """Explain the recorded result before offering detailed inspection controls."""
    rows = format_candidate_rows(view['candidates'])
    provenance = view['provenance']
    task = view['task_context']
    positions = ', '.join(str(p) for p in task['positions']) or 'unrecorded'
    context = str(provenance.get('sequence_context') or 'unrecorded')
    requests = view['meta_request_attempts']
    with st.container(key='tour_overview'):
        st.subheader('Review the saved evidence')
        st.html('<section class="overview-purpose"><span class="section-kicker">'
                'Research purpose · current review scope</span>'
                '<h2>Which variants merit a closer look?</h2>'
                '<p>Review sequence plausibility using recorded ESM preferences, '
                'guarded Meta tool calls and inspectable evidence. '
                'Choose hypotheses for follow-up; biological effects remain unvalidated.</p></section>')
        metrics = (
            ('Saved candidates', str(view['candidate_count'])),
            ('Full-reference position', positions),
            ('Scoring context', context),
            ('Meta requests recorded', str(requests) if requests is not None else 'Unrecorded'),
        )
        st.html('<div class="overview-metrics">' + ''.join(
            '<div class="overview-metric"><span>' + escape(label) + '</span><strong>'
            + escape(value) + '</strong></div>' for label, value in metrics) + '</div>')
        results, workflow = st.columns([1, 1], gap='large')
        with results:
            st.markdown('**Saved ESM results**')
            checkpoint = provenance.get('checkpoint') or provenance.get('model_key') or 'unrecorded'
            st.caption(f"{checkpoint} · {context} · "
                       f"{provenance.get('device') or 'device unrecorded'} / "
                       f"{provenance.get('precision') or 'precision unrecorded'}")
            st.table([{'Rank': row['rank'], 'Variant': row['candidate_id'],
                       'ESM preference': row['score']} for row in rows[:3]])
            st.caption('Top three of the saved cohort · dimensionless sequence preference. '
                       'Full table and CSV are in Candidates.')
            st.caption('Common rank policy: ' + str(view['ranking_scope'] or 'unrecorded'))
        with workflow:
            st.markdown('**Recorded Meta workflow**')
            st.caption(f"{view['actual_model'] or 'Model unrecorded'} · "
                       f"{len(view['tool_events'])} MCP calls · saved order")
            steps = []
            for step in view['decision_steps']:
                actor = 'Meta' if step['kind'] == 'meta_response' else 'MCP code'
                steps.append('<li><strong>' + actor + '</strong><span>'
                             + escape(step['label']) + '</span></li>')
            if steps:
                st.html('<ol class="overview-path">' + ''.join(steps) + '</ol>')
            else:
                st.info('No agent steps recorded in this artifact.')
            st.caption('Meta selects permitted tools and explains evidence. '
                       'Registered code enforces guards, computes scores and ranks candidates.')
        st.html('<aside class="overview-limit"><strong>Not established</strong>'
                '<p>T50, activity, solubility, Tm, retained function and atom geometry '
                'remain unvalidated. Provider cost: ' + escape(view['cost_display']) + '.</p></aside>')
        st.caption('Current view: REPLAY · original ESM execution: '
                   + view['original_esm_badge'] + ' · viewing never starts a new model call.')


def _candidates(view):
    rows = format_candidate_rows(view['candidates'])
    heading, control = st.columns([3, 2], vertical_alignment='center')
    heading.subheader('Candidate shortlist')
    show_all = control.toggle('Show entire cohort', key='show_all_candidates')
    shown = select_candidate_rows(rows, limit=None if show_all else 5)
    st.caption(f"Showing {len(shown)} of {len(rows)} · saved order · dimensionless sequence preference")
    _candidate_table(shown, key='candidate_table')
    st.download_button('Download displayed CSV', candidate_csv(shown),
        file_name='biopilot-candidates.csv', mime='text/csv', key='candidate_csv',
        icon=':material/download:')
    st.caption('Common rank policy: ' + str(view['ranking_scope'] or 'unavailable') +
               ' · optional evidence does not change these ranks.')
    st.markdown('**Inspect candidates**')
    _candidate_focus(rows)
    st.button('Inspect in Structure', key='open_candidate_structure',
              on_click=_open_candidate_structure, args=(rows,), icon=':material/view_in_ar:')
    compare, clear, _ = st.columns([1.5, 1, 2.5])
    compare.button('Compare top three', key='compare_top_three',
        on_click=_set_comparison, args=([row['candidate_id'] for row in rows[:3]],),
        disabled=not rows, icon=':material/compare_arrows:')
    clear.button('Clear selection', key='clear_comparison',
        on_click=_set_comparison, args=([],),
        disabled=not st.session_state.get('compare_candidates'))
    selected = st.multiselect('Compare up to three saved candidates',
        [row['candidate_id'] for row in rows], key='compare_candidates', max_selections=3,
        placeholder='Choose variants to inspect together',
        help='Comparison preserves original ranks and recorded scores.')
    if selected:
        compared = select_candidate_rows(rows, selected)
        _candidate_table(compared, key='comparison_table')
        st.download_button('Download comparison CSV', candidate_csv(compared),
            file_name='biopilot-comparison.csv', mime='text/csv', key='comparison_csv')
    if view['model_narrative']:
        with st.expander('Recorded model explanation'):
            st.caption('Saved public prose; numerical evidence is rendered from artifact rows above.')
            st.text(view['model_narrative'])
    with st.expander('Scientific limits'):
        st.text(CLAIM_BANNER)


VIEWS = ('Overview', 'Candidates', 'Structure', 'Agent Trace', 'Evidence')
VIEW_LABELS = {name: name for name in VIEWS}
EVIDENCE_SECTIONS = ('Run provenance', 'Structure provenance', 'Advanced diagnostics')


def _tour_action(action, candidates):
    now = time.monotonic()
    if action == 'start':
        start_tour(st.session_state, candidates, now=now, autoplay=False)
    elif action == 'stop':
        stop_tour(st.session_state)
    elif action in ('next', 'back'):
        advance_tour(st.session_state, candidates, now=now, delta=1 if action == 'next' else -1)
    else:
        set_tour_playing(st.session_state, action == 'play', now=now)


def _guided_tour(view):
    """An acting offline walkthrough, with real checks and inspectable controls."""
    if not st.session_state.get('tour_active'):
        return
    active = st.session_state['tour_step']
    step = STEPS[active]
    playing = st.session_state.get('tour_playing', False)
    with st.container(border=True, key='tour_card'):
        st.html(f'<div class="tour-compact"><span class="tour-count">{active + 1:02d} / {len(STEPS):02d}</span>'
                f'<div><strong>{escape(step.title)}</strong><p>{escape(step.body)}</p></div></div>')
        back, toggle, forward, restart, dismiss = st.columns([1, 1, 1, 1, 1])
        back.button('Back', key='tour_back', disabled=active == 0,
                    on_click=_tour_action, args=('back', view['candidates']), width='stretch')
        toggle.button('Pause' if playing else 'Play', key='tour_play',
                      disabled=st.session_state.get('tour_complete', False),
                      on_click=_tour_action, args=('pause' if playing else 'play', view['candidates']),
                      width='stretch')
        forward.button('Next', key='tour_next', disabled=active == len(STEPS) - 1,
                       on_click=_tour_action, args=('next', view['candidates']), width='stretch')
        restart.button('Restart', key='restart_demo', on_click=_tour_action,
                       args=('start', view['candidates']), width='stretch')
        dismiss.button('Exit', key='exit_demo', on_click=_tour_action,
                       args=('stop', view['candidates']), width='stretch')
        st.caption(('Walkthrough complete. Exit restores your previous controls.'
                    if st.session_state.get('tour_complete') else
                    'Guided demo · REPLAY + real local checks · '
                    + ('Autoplay · 7 seconds per step' if playing else 'Use Next to continue')
                    + ' · no new inference'))


@st.fragment(run_every=1)
def _tour_clock():
    # A fragment may run after widget construction. Only request a full rerun here;
    # main applies the transition before constructing any widget with changed keys.
    deadline = st.session_state.get('tour_next_at')
    if (st.session_state.get('tour_active') and st.session_state.get('tour_playing')
            and deadline is not None and time.monotonic() >= deadline):
        st.rerun(scope='app')


def _navigate_view(name):
    st.session_state['active_view'] = name
    set_tour_playing(st.session_state, False, now=time.monotonic())


def _pause_for_navigation():
    set_tour_playing(st.session_state, False, now=time.monotonic())


def _trace(view):
    st.subheader('Recorded tool decisions')
    handoff_ladder(view['decision_steps'])
    st.divider()
    st.caption('Ordered saved MCP calls. Selecting a step only inspects the record.')
    events = view['tool_events']
    if not events:
        st.info('No MCP tool calls recorded.')
        return
    st.session_state['trace_step'] = min(len(events) - 1,
        max(0, st.session_state.get('trace_step', 0)))
    index = st.selectbox('Recorded step', list(range(len(events))), key='trace_step',
        format_func=lambda i: f"{i+1:02d} · {events[i]['tool']}")
    previous, following, note = st.columns([1, 1, 3])
    previous.button('Previous step', key='previous_trace', disabled=index == 0,
        on_click=_move_trace, args=(-1, len(events)))
    following.button('Next recorded step', key='next_trace', disabled=index == len(events)-1,
        on_click=_move_trace, args=(1, len(events)))
    note.caption('Inspect saved events. Nothing is executed.')
    for event in events:
        with st.container(border=True, key=f"trace_card_{event['step']}"):
            st.html('<div class="trace-heading"><span class="step-number">'
                + str(event['step']).zfill(2) + '</span><span class="trace-label">'
                + escape(event['tool']) + '</span><span class="state-pill">'
                + escape(str(event['result'].get('status', 'unavailable'))) + '</span></div>')
            st.text(f"{event['step']:02d}  {event['tool']}  ·  " +
                    str(event['result'].get('status', 'outcome unavailable')))
            st.text(event['reason_brief'] or 'No reason_brief recorded.')
            if event['step'] == index + 1:
                left, right = st.columns(2)
                left.caption('RECORDED ARGUMENTS')
                left.json(event['arguments'], expanded=True)
                right.caption('RECORDED PUBLIC OUTPUT')
                right.json(event['result'], expanded=True)
    st.caption('reason_brief is a short public justification, not private chain of thought. '
               'Original tool output modes describe the historical execution.')


def _structure(view):
    """Reference structure beside the saved evidence for the chosen position."""
    st.subheader('Reference structure')
    st.caption('Experimental reference 1ISP · chain A · local correspondence check · atom geometry unvalidated')
    rows = format_candidate_rows(view['candidates'])
    candidate_control, position_control = st.columns(2)
    with candidate_control:
        _candidate_focus(rows)
    focused = next((r for r in rows if r['candidate_id'] == st.session_state.get('focused_candidate')), None)
    choices = [(f"{row['candidate_id']} · full {row['full_position']}",
                row['full_position'], row) for row in rows]
    choices += [(f'{residue}{position} · protected', position, None)
                for position, residue in ((108, 'S'), (164, 'D'), (187, 'H'))]
    labels = [choice[0] for choice in choices]
    if st.session_state.get('structure_focus') not in labels:
        st.session_state['structure_focus'] = (f"{focused['candidate_id']} · full {focused['full_position']}" if focused else labels[0])
    with position_control:
        chosen = st.selectbox('Position to inspect', labels, key='structure_focus',
            on_change=_sync_structure, args=(choices,),
            help='Saved candidates first, then the registered protected residues.')
    _, position, row = choices[labels.index(chosen)]
    selection = residue_selection(position)
    if focused:
        st.caption(f"Selected candidate: {focused['candidate_id']} · reference visualization only; no mutant structure is inferred.")
    report = verify_reference()
    try:
        neighborhood = sequence_neighborhood(position)
        st.caption('Full-reference sequence neighborhood · brackets mark the inspected position')
        st.code(' '.join(f"[{r['residue']}{r['full_position']}]" if r['full_position'] == position else f"{r['residue']}{r['full_position']}" for r in neighborhood), language=None, wrap_lines=True)
    except ValueError:
        st.error('Registered sequence could not be verified; sequence context unavailable.')
        return
    if report['status'] != 'verified_index_join':
        st.error('Reference correspondence is unverified. 3D is disabled: ' + report.get('reason', 'unknown'))
        st.caption('Sequence-level context only; no atom positions or mutation effects are inferred.')
        return
    evidence, panel = st.columns([2, 3])
    with evidence:
        if row is not None:
            st.metric('Recorded ESM preference', row['score'])
            st.caption('Dimensionless masked-marginal log likelihood ratio from the saved '
                       'run. Not T50, activity, solubility, Tm or experimental validation.')
        else:
            st.metric('Protected residue', f"{selection['residue']}{position}")
            st.caption('Interactive review blocks substitutions here. Protection does not '
                       'establish retained function.')
        if selection['status'] == 'observed':
            st.success(f"Modelled · chain {selection['chain']} · author residue "
                       f"{selection['pdb_auth_seq_id']}")
        else:
            st.warning(selection['note'])
        st.text(f"Full position {position}  →  author numbering "
                f"{selection['pdb_auth_seq_id'] or 'unavailable'}")
        st.caption('Structure labels use full-reference positions; author numbering comes from the registered join.')
        with st.expander('Scientific limits'):
            st.text(CLAIM_BANNER)
    with panel, st.container(key='tour_structure'):
        st.caption('Orange: inspected residue · S108 teal · D164 blue · H187 purple. Missing atoms are never highlighted.')
        components.html(structure_panel_html(highlight=selection,
            appearance=st.session_state.get('appearance', 'Dark')),
            height=620, scrolling=False)
    with st.expander('Additional evidence · Atlas and structure models'):
        _additional_evidence()


def _structure_provenance():
    report = verify_reference()
    st.subheader('Structure provenance')
    st.caption('Public experimental reference; independent from any saved model prediction.')
    st.json({key: value for key, value in report.items() if key != 'mapping'}, expanded=True)
    if report['status'] == 'verified_index_join':
        st.markdown('[Public mmCIF source](' + report['source_url'] + ')')
        st.caption('Exact full-reference/deposited-sequence match; polymer scheme joined to observed atoms; author numbering and residue identities rechecked locally. This verifies index correspondence, not atom geometry, stability, activity or binding changes.')
        st.table([{'Full residue': f"{r['residue']}{r['full_position']}", 'Chain': r['chain'],
                           'Author residue': r['pdb_auth_seq_id'], 'Correspondence': r['status']}
                          for r in [residue_selection(p) for p in (32, 108, 164, 187, 212)]])


def _additional_evidence():
    st.caption('Workspace evidence acquired separately from this saved run. It is not part of the original Meta trace.')
    try:
        snapshot = load_registered_atlas_snapshot()
    except (ValueError, OSError):
        snapshot = None
    if snapshot:
        st.markdown('**Biohub ESM Atlas · verified local snapshot**')
        st.text(f"Exact registered WT · accession {snapshot['identity']['accession']} · source {snapshot['identity']['source']}")
        st.caption('Retrieved ' + snapshot['retrieved_at'] +
                   ' · no new folding requested · available through the bounded MCP snapshot tool')
        st.caption('Structure confidence was not returned. This match does not establish a stored structure or a variant effect.')
        st.caption('The snapshot checksum is verified locally; upstream authenticity is not cryptographically verified.')
    else:
        st.info('Atlas context is unavailable; no lookup or fallback is started by this screen.')
    try:
        predictions=load_predictions()
    except (ValueError,OSError,KeyError) as error:
        st.error('Stored prediction integrity check failed: '+str(error))
        predictions=[]
    actual={r['model']:r for r in predictions}
    st.table([
        {'Model': 'ESM3 open', 'Role': 'Optional full_212 structure prediction',
         'State': 'Actual L40S prediction · A32V · stored result' if 'esm3' in actual else 'GPU execution unverified'},
        {'Model': 'ESMFold2', 'Role': 'Optional full_212 structure prediction',
         'State': 'Actual L40S prediction · WT · stored result' if 'esmfold2' in actual else 'GPU execution unverified'},
    ])
    if predictions:
        chosen=st.selectbox('Stored predicted structure',range(len(predictions)),
            format_func=lambda i:('ESMFold2' if predictions[i]['model']=='esmfold2' else 'ESM3')+' · '+predictions[i]['variant'],key='predicted_structure')
        selected=predictions[chosen]
        st.caption(f"Actual recorded worker time {selected['elapsed_seconds']}s · local checksums and full_212 sequence verified")
        components.html(structure_panel_html(prediction=selected,
            appearance=st.session_state.get('appearance','Dark'),height=330),height=420)
        st.caption('Different models and inputs: these views do not measure a variant effect or compare model accuracy. Atom geometry and biological effects remain unvalidated.')
    st.caption('Optional predictions do not change saved ESM2 scores or ranks. This screen replays the stored GPU results.')


def _decoded(upload, limit):
    if upload is None:
        return None
    data = upload.getvalue()[:limit + 1]
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('utf-8', 'replace')


def _uploads(view):
    """Local diagnostics over your own files. Nothing is uploaded anywhere."""
    st.markdown('**Your files · local diagnostics**')
    st.caption('Analysed in memory on this machine. No file, sequence or structure is sent to '
               'a provider, a GPU or any network service. These checks diagnose numbering; '
               'they predict nothing.')
    sequence_tab, structure_tab = st.columns(2)
    with sequence_tab:
        st.markdown('**1 · Is this the registered protein?**')
        fasta = st.file_uploader('FASTA', type=['fasta', 'fa', 'faa', 'txt'],
                                 key='upload_fasta', max_upload_size=1,
                                 help='Local sequence diagnostics accept up to 64 KiB.')
        text = _decoded(fasta, MAX_SEQUENCE_BYTES)
        if text is not None:
            result = check_sequence(text)
            (st.success if result['reviewable'] else st.warning)(
                result['verdict'].replace('_', ' '))
            st.caption(result['detail'])
            st.text(f"length {result['length']} · sha256 "
                    f"{(result['sha256'] or '')[:16] or 'unavailable'}…")
    with structure_tab:
        st.markdown('**2 · Does your numbering join to your coordinates?**')
        st.caption('The same derivation the registered contract uses, run against your file.')
        cif = st.file_uploader('mmCIF', type=['cif', 'mmcif'], key='upload_cif',
                               max_upload_size=8, help='Maximum 8 MiB. Local diagnostics only.')
        chain = st.text_input('Author chain', 'A', max_chars=4, key='upload_chain')
        paired = st.file_uploader('Sequence for that chain (FASTA)',
                                  type=['fasta', 'fa', 'faa', 'txt'], key='upload_cif_fasta',
                                  max_upload_size=1,
                                  help='Up to 64 KiB. Use the deposited chain sequence, which may differ from the full reference.')
        cif_text = _decoded(cif, MAX_STRUCTURE_BYTES)
        seq_text = _decoded(paired, MAX_SEQUENCE_BYTES)
        if cif_text is not None and seq_text is not None:
            result = check_structure(cif_text, seq_text, chain=chain or 'A')
            ok = result['verdict'] == 'join_verified'
            (st.success if ok else st.error)(result['verdict'].replace('_', ' '))
            st.caption(result['detail'])
            if ok:
                st.json({key: result[key] for key in (
                    'chain', 'deposited_residue_count', 'modelled_residue_count',
                    'unmodelled_positions', 'auth_minus_label_offsets', 'insertion_codes')})
        elif cif_text is not None or seq_text is not None:
            st.caption('Both a structure and the matching sequence are needed to check a join.')


def _provenance_chain(chain):
    st.markdown('**Recorded provenance chain**')
    broken = [link for link in chain if link['mismatch']]
    absent = [link for link in chain if link['absent']]
    unverified = [link for link in chain if not link['link_verified']]
    if broken:
        st.error('Commitment mismatch at: ' + ', '.join(link['stage'] for link in broken) +
                 ' — the stored upstream digest disagrees with the record.')
    elif absent:
        st.warning('Stages absent from this record: ' +
                   ', '.join(link['stage'] for link in absent) + '.')
    elif unverified:
        st.info('Local checks are shown below. Other stages are recorded commitments or file '
                'identities; external source authenticity remains unverified.', icon=':material/link:')
    else:
        st.info('Recorded local consistency checks passed. These are not signed or externally anchored.')
    rows = []
    for index, link in enumerate(chain, start=1):
        digest = link['digest']
        carried = link['carries_upstream_digest']
        rows.append({
            'step': index,
            'stage': link['label'],
            'digest': (digest[:12] + '…' + digest[-4:]) if digest else '— absent —',
            'carries upstream': (carried[:12] + '…' + carried[-4:]) if carried else '—',
            'link': link.get('status', 'unverified'),
        })
    st.table(rows)
    st.caption(CHAIN_SCOPE)
    with st.expander('Full digests for every chain stage'):
        st.json({link['stage']: {'digest': link['digest'],
                                 'carries_upstream_digest': link['carries_upstream_digest'],
                                 'detail': link['detail'], 'link_verified': link['link_verified']}
                 for link in chain})


def _run_provenance(view):
    st.subheader('Evidence and provenance')
    st.caption('Current view: REPLAY · saved evidence is not recomputed.')
    with st.container(key='tour_provenance'):
        _provenance_chain(view['provenance_chain'])
    st.divider()
    st.text(f"Recorded ESM source mode: {view['esm_badge']}  ·  "
            f"original score execution: {view['original_esm_badge']}")
    with st.expander('Run identity and source hashes'):
        st.json({'run_id':view['run_id'], 'status':view['status'],
                 'score_artifact_sha256':view['score_artifact_sha256'],
                 'opened_file_sha256':view['file_sha256'], 'replay_lineage':view['lineage']})
        st.caption('The opened-file hash identifies the bytes being viewed; it is not an upstream authenticity check.')
    with st.expander('Recorded computation provenance'):
        st.json(view['provenance'], expanded=True)
    with st.expander('Provider, protocol and cost details'):
        st.json({key:view[key] for key in ('provider','actual_model','requested_model',
            'mcp_protocol_version','meta_request_attempts','actual_cost_micros','cost_status')})
        st.caption('A local reservation is not a provider bill. Unverified cost remains unknown.')
    with st.expander('Public saved evidence JSON'):
        st.json({'task_context':view['task_context'], 'ranking_scope':view['ranking_scope'],
                 'scientific_scope':view['scientific_scope'],
                 'biological_efficacy_established':view['biological_efficacy_established'],
                 'candidates':format_candidate_rows(view['candidates']),
                 'tool_events':view['tool_events']}, expanded=False)


def _evidence(view):
    st.session_state.setdefault('evidence_section', EVIDENCE_SECTIONS[0])
    if st.session_state['evidence_section'] not in EVIDENCE_SECTIONS:
        st.session_state['evidence_section'] = EVIDENCE_SECTIONS[0]
    st.segmented_control('Evidence section', EVIDENCE_SECTIONS, key='evidence_section',
                         selection_mode='single', required=True, width='stretch')
    if st.session_state['evidence_section'] == EVIDENCE_SECTIONS[1]:
        _structure_provenance()
    elif st.session_state['evidence_section'] == 'Advanced diagnostics':
        _input(view)
    else:
        _run_provenance(view)


def main():
    st.set_page_config(page_title='BioPilot Bench · Review workbench', page_icon=BRAND_ICON,
                       layout='wide', initial_sidebar_state='auto')
    arguments = _artifact_argument()
    session_url = arguments.session_url
    try:
        view = load_run_view(arguments.artifact)
    except (ValueError, OSError) as error:
        st.error(f'Nothing rendered: {error}')
        return
    # Style first: the palette variables must exist before any block paints, or the
    # sidebar renders a rerun at fallback contrast.
    tick_tour(st.session_state, view['candidates'], now=time.monotonic())
    # Preserve presentation state while another view temporarily removes its widgets.
    # Streamlit otherwise deletes unrendered widget keys at the end of a run.
    for key in ('local_variant', 'local_frame', 'local_objective', 'compare_candidates',
                'show_all_candidates', 'focused_candidate', 'structure_focus', 'trace_step', 'evidence_section'):
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    previous_view = st.session_state.get('active_view')
    if previous_view in ('Input', 'Check a file', 'Input & Diagnostics'):
        st.session_state['evidence_section'] = 'Advanced diagnostics'
    if st.session_state.get('evidence_section') == 'Reference mapping & saved structures':
        st.session_state['evidence_section'] = 'Structure provenance'
    aliases = {'Input': 'Evidence', 'Check a file': 'Evidence', 'Input & Diagnostics': 'Evidence',
               'Decision trace': 'Agent Trace'}
    st.session_state['active_view'] = aliases.get(previous_view, previous_view)
    if st.session_state['active_view'] not in VIEWS:
        st.session_state['active_view'] = 'Overview'
    init_appearance()
    _style(st.session_state['appearance'])
    _sidebar(view, session_url, arguments.workspace_url)
    with st.container(key='workspace_header'):
        heading, demo = st.columns([3, 1], vertical_alignment='bottom')
        with heading:
            st.html('<div class="workspace-kicker">PUBLIC LIPASE A <span class="workspace-mode">SAVED RUN / REPLAY</span></div>')
            st.title('Sequence review')
        with demo:
            st.button('Start guided demo', key='start_demo', type='primary', width='stretch',
                      on_click=_tour_action, args=('start', view['candidates']))
    st.html('<div class="run-summary">'
            f'<span><b>{view["candidate_count"]}</b> candidates</span>'
            f'<span>{escape(str(view["provenance"].get("model_key") or view["provenance"].get("checkpoint") or "checkpoint unavailable"))} · '
            f'{escape(str(view["provenance"].get("sequence_context") or "context unavailable"))}</span>'
            f'<span>Meta <b>{escape(view["actual_model"] or "unavailable")}</b></span>'
            f'<span>Cost <b>{escape(view["cost_display"])}</b></span></div>')
    st.caption('REPLAY · saved results, no new inference. Sequence preferences only; T50, activity, solubility, '
               'Tm, retained function and atom geometry remain unvalidated.')
    if not view['is_complete']:
        st.error(f"Run status: {view['status']} — stop_reason: {view['stop_reason']}. "
                 'This is not a completed review.')
    if not view['is_scientific_evidence']:
        st.warning('Recorded score evidence: ' + view['esm_badge'] +
                   ' · incomplete, inconsistent or synthetic evidence is not verified scientific output.')
    if view.get('integrity_status') == 'mismatch':
        st.error('Saved evidence does not pass local integrity checks. Inspect Evidence before using these rows.')
    _guided_tour(view)
    # A state-driven selector rather than st.tabs: tabs cannot be switched
    # programmatically, so the guided tour could only ever name a tab instead of
    # opening it. This lets Next actually move the screen.
    st.session_state.setdefault('active_view', 'Overview')
    st.segmented_control('View', VIEWS, key='active_view',
                         format_func=lambda name: VIEW_LABELS[name],
                         on_change=_pause_for_navigation, label_visibility='collapsed',
                         selection_mode='single', required=True, width='stretch')
    shown = st.session_state.get('active_view') or 'Overview'
    with st.container(key='view_content'):
        {'Overview': _overview, 'Candidates': _candidates, 'Structure': _structure, 'Agent Trace': _trace,
         'Input & Diagnostics': _input, 'Evidence': _evidence}[shown](view)
    st.caption('Saved run status: ' + str(view['status']))
    if st.session_state.get('tour_playing'):
        _tour_clock()
    components.html(spotlight_document(
        st.session_state['tour_step'] if st.session_state.get('tour_active') else None,
        appearance=st.session_state.get('appearance', 'Dark'),
        playing=st.session_state.get('tour_playing', False)), height=0, scrolling=False)


if __name__ == '__main__':
    main()
