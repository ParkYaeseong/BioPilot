"""The structure panel may only select residues through the registered coordinate join.

The failure this guards against is concrete: 1ISP author numbering runs 1-181, so a
viewer that selects by full-reference position would highlight auth 32 (SER, full
position 63) when asked for full position 32 (ALA) - a silent 31-residue error shown
as evidence. Every selection here must come from the registered map, never arithmetic.
"""
import json
from pathlib import Path
import re

import pytest

from app.viewer_structure import (STRUCTURE_LABEL, protected_selections,
                                  residue_selection, structure_panel_html)

ROOT = Path(__file__).resolve().parents[1]
CIF = ROOT / 'reference/1ISP.cif'
BUNDLE = ROOT / 'app/vendor/3Dmol-min.js'


def test_reference_mapping_is_reverified_and_corruption_fails_closed():
    from app.viewer_structure import verify_reference
    verified = verify_reference()
    assert verified['status'] == 'verified_index_join'
    assert verified['observed_count'] == 179
    assert verified['missing_full_positions'] == [32, 212]
    assert verify_reference(cif_text='data_invalid')['status'] == 'unverified'
    rows = json.loads((ROOT / 'reference/residue_map.json').read_text())['mapping']
    rows[107]['pdb_auth_seq_id'] = '999'
    assert verify_reference(mapping=rows)['status'] == 'unverified'


def test_shared_candidate_focus_survives_switching_views():
    from streamlit.testing.v1 import AppTest
    import sys
    from unittest.mock import patch
    with patch.object(sys, 'argv', ['viewer.py', '--artifact', str(ROOT / 'demo/artifacts/sequence_review.replay.json')]):
        app = AppTest.from_file(str(ROOT / 'app/viewer.py')).run()
        app.session_state['active_view'] = 'Candidates'
        app.run()
        picker = next(x for x in app.selectbox if x.key == 'focused_candidate')
        picker.select('A32V').run()
        app.session_state['active_view'] = 'Structure'
        app.run()
        assert not app.exception
        assert app.session_state['focused_candidate'] == 'A32V'
        assert any('no atoms' in x.value for x in app.warning)
        assert any('A32V' in x.value for x in app.caption)
        app.selectbox(key='structure_focus').select('A32S · full 32').run()
        app.selectbox(key='structure_focus').select('S108 · protected').run()
        app.session_state['active_view'] = 'Candidates'
        app.run()
        assert app.selectbox(key='focused_candidate').value == 'A32S'
        app.button(key='open_candidate_structure').click().run()
        assert app.session_state['active_view'] == 'Structure'
        assert app.selectbox(key='structure_focus').value == 'A32S · full 32'


def test_forged_atom_selection_is_never_rendered():
    forged = {'full_position': 32, 'selection': {'chain': 'A', 'resi': 32}}
    html = structure_panel_html(highlight=forged)
    block = html.split('HIGHLIGHT_START')[1].split('HIGHLIGHT_END')[0]
    assert 'resi' not in block


def test_catalytic_sites_have_distinct_colors_and_sequence_context():
    from app.viewer_structure import sequence_neighborhood
    html = structure_panel_html()
    assert all(color in html for color in ('0x008577', '0x2563eb', '0x9333ea'))
    assert {'full_position': 32, 'residue': 'A'} in sequence_neighborhood(32)


def test_unverified_source_disables_3d_but_keeps_pinned_sequence(monkeypatch, tmp_path):
    import app.viewer_structure as structures
    damaged = tmp_path / 'damaged.cif'
    damaged.write_text('data_damaged')
    monkeypatch.setattr(structures, '_STRUCTURE', damaged)
    selection = structures.residue_selection(108)
    assert selection['selection'] is None
    html = structures.structure_panel_html(highlight=selection)
    assert 'disabled' in html and 'GLViewer' not in html
    assert {'full_position': 108, 'residue': 'S'} in structures.sequence_neighborhood(108)


def test_vendored_assets_are_present_so_nothing_is_fetched_at_render_time():
    assert CIF.is_file() and BUNDLE.is_file()
    pinned = json.loads((ROOT / 'reference/target_profile.json').read_text(
        encoding='utf-8'))['structure']['coordinate_file_sha256']
    import hashlib
    assert hashlib.sha256(CIF.read_bytes()).hexdigest() == pinned


def test_modelled_residue_resolves_to_registered_author_numbering():
    selection = residue_selection(108)
    assert selection['status'] == 'observed'
    assert selection['residue'] == 'S'
    assert selection['pdb_auth_seq_id'] == '77'
    assert selection['selection'] == {'chain': 'A', 'resi': 77}


def test_the_demo_position_is_unmodelled_and_yields_no_selection():
    """All 19 saved candidates are A32X. Full 32 has no atoms, so nothing is highlighted."""
    selection = residue_selection(32)
    assert selection['status'] == 'unmodelled'
    assert selection['residue'] == 'A'
    assert selection['selection'] is None
    assert 'model' in selection['note'].lower()


def test_position_outside_the_deposited_construct_yields_no_selection():
    selection = residue_selection(1)
    assert selection['status'] == 'outside_deposited_construct'
    assert selection['selection'] is None


@pytest.mark.parametrize('position', [0, 213, 500, -5])
def test_unknown_positions_are_refused_rather_than_guessed(position):
    selection = residue_selection(position)
    assert selection['status'] == 'unknown_position'
    assert selection['selection'] is None


def test_selection_follows_the_registered_map_and_never_an_offset():
    """Feed a map whose author numbering disagrees with full_position - 31."""
    doctored = [{'full_position': 108, 'residue': 'S', 'mature_position': 77,
                 'deposited_sequence_position': 77, 'pdb_label_seq_id': 77,
                 'pdb_auth_seq_id': '999', 'pdb_insertion_code': None,
                 'coordinate_observed': True, 'protected': True}]
    selection = residue_selection(108, residue_map=doctored)
    assert selection['selection'] is None
    assert selection['status'] == 'unverified_mapping'


def test_protected_triad_is_selectable_and_matches_the_registered_join():
    triad = protected_selections()
    assert [row['full_position'] for row in triad] == [108, 164, 187]
    assert [row['selection']['resi'] for row in triad] == [77, 133, 156]
    assert all(row['status'] == 'observed' for row in triad)


def test_panel_inlines_every_asset_and_loads_nothing_remotely():
    html = structure_panel_html(highlight=residue_selection(108))
    external = re.findall(r'<script[^>]+src\s*=\s*["\']([^"\']+)', html)
    assert external == [], f'panel would fetch remote assets: {external}'
    assert 'GLViewer' in html, 'vendored 3Dmol bundle was not inlined'
    assert 'data_1ISP' in html, 'structure coordinates were not inlined'


def test_panel_states_it_is_the_wild_type_reference_not_a_mutant():
    html = structure_panel_html(highlight=residue_selection(108))
    assert STRUCTURE_LABEL in html
    lowered = STRUCTURE_LABEL.lower()
    assert 'wild-type' in lowered and 'reference' in lowered
    assert 'not a mutant' in lowered


def test_panel_emits_no_residue_selector_for_an_unmodelled_position():
    """The off-by-31 trap: asking for full 32 must not produce resi 32, or any resi."""
    html = structure_panel_html(highlight=residue_selection(32))
    highlight_block = html.split('HIGHLIGHT_START')[1].split('HIGHLIGHT_END')[0]
    assert 'resi' not in highlight_block
    assert '32' not in highlight_block


def test_light_structure_is_themed_and_labels_state_full_reference_numbering():
    html = structure_panel_html(highlight=residue_selection(108), appearance='Light')
    assert 'backgroundColor:0xf8fafc' in html
    assert 'S108 · full' in html
    assert 'D164 · full' in structure_panel_html(highlight=residue_selection(164), appearance='Light')
    # The catalytic triad is spatially close; label only the selected residue so
    # its full-reference identity stays legible rather than overlapping labels.
    generated = html.split('/* HIGHLIGHT_START */')[1]
    assert generated.count('viewer.addLabel(') == 1
    assert 'Fit reference' in html and 'Stop rotation' in html
    assert "viewer.spin(rotating ? 'y' : false" in html
