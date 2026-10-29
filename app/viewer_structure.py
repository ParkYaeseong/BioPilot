"""Read-only structure panel for the saved-run workbench.

Every residue selection is looked up in the registered coordinate join. Nothing here
derives a PDB residue number from a full-reference position by arithmetic, because
1ISP author numbering runs 1-181: asking for full position 32 and emitting `resi 32`
would highlight SER at full position 63 and report it as evidence.

Assets are inlined from the vendored copies so rendering fetches nothing remotely.
This displays the experimental wild-type reference only. It is not a mutant structure,
not validated geometry, and not evidence of activity or retained function.
"""
from functools import lru_cache
from html import escape
import json
import hashlib
import math
from pathlib import Path

from app.core.coordinate_join import derive_coordinate_join, parse_mmcif_loops
from app.core.targets import registered_profile, validate_target, COORDINATE_SOURCE_SHA256

_ROOT = Path(__file__).resolve().parents[1]
_RESIDUE_MAP = _ROOT / 'reference' / 'residue_map.json'
_STRUCTURE = _ROOT / 'reference' / '1ISP.cif'
_BUNDLE = _ROOT / 'app' / 'vendor' / '3Dmol-min.js'

CHAIN = 'A'
STRUCTURE_LABEL = (
    'Experimental wild-type reference structure 1ISP (X-ray, 1.30 A, chain A). '
    'Not a mutant structure, not validated geometry, and not evidence of activity '
    'or retained function. Stability and binding changes are unvalidated.')
UNMODELLED_NOTE = (
    'Deposited in 1ISP but not modelled: this residue has no atoms in the structure, '
    'so no position can be shown. Nearby residues are not a substitute.')
OUTSIDE_NOTE = (
    'Outside the deposited construct. Full positions 1-31 are not part of the '
    '181-residue deposited sequence and have no structural counterpart.')


def _registered_map():
    report = verify_reference()
    return tuple(report.get('mapping', ()))


def verify_reference(*, cif_text=None, mapping=None):
    """Recheck pinned public bytes and exact sequence/atom numbering, not geometry."""
    try:
        text = _STRUCTURE.read_text(encoding='utf-8') if cif_text is None else cif_text
        rows = json.loads(_RESIDUE_MAP.read_text(encoding='utf-8'))['mapping'] if mapping is None else mapping
        return _verify_reference(text, json.dumps(rows, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {'status': 'unverified', 'reason': str(error)}


@lru_cache(maxsize=4)
def _verify_reference(text, mapping_json):
    try:
        if hashlib.sha256(text.encode('utf-8')).hexdigest() != COORDINATE_SOURCE_SHA256:
            raise ValueError('Public mmCIF checksum differs from the registered source.')
        profile = registered_profile()
        validate_target(profile, 'sequence_plausibility_review')
        full, deposited = profile['reference_sequence'], profile['mature_sequence']
        starts = [i for i in range(len(full)) if full.startswith(deposited, i)]
        if len(starts) != 1:
            raise ValueError('Deposited sequence has no unique exact full-reference match.')
        offset = starts[0]
        joined = derive_coordinate_join(text, deposited, chain=CHAIN)
        rows = json.loads(mapping_json)
        if len(rows) != len(full):
            raise ValueError('Registered mapping length disagrees with the full reference.')
        for position, row in enumerate(rows, 1):
            if row['full_position'] != position or row['residue'] != full[position - 1]:
                raise ValueError('Registered full-reference identity or position differs.')
            if row.get('protected') != (position in (108, 164, 187)):
                raise ValueError('Registered catalytic identities differ.')
            if not offset < position <= offset + len(deposited):
                if any(row.get(k) is not None for k in ('coordinate_observed', 'pdb_auth_seq_id', 'pdb_label_seq_id')):
                    raise ValueError('Outside-construct position has an invented correspondence.')
                continue
            actual = joined['rows'][position - offset - 1]
            for key in ('residue', 'pdb_label_seq_id', 'pdb_auth_seq_id', 'pdb_insertion_code', 'coordinate_observed'):
                if row.get(key) != actual[key]:
                    raise ValueError(f'Registered mapping disagrees with mmCIF at full {position}: {key}.')
            if row.get('deposited_sequence_position') != actual['deposited_position']:
                raise ValueError('Deposited sequence correspondence differs.')
        by_label = {r['pdb_label_seq_id']: r for r in joined['rows']}
        for atom in parse_mmcif_loops(text).get('_atom_site', []):
            if atom.get('group_PDB') != 'ATOM' or atom.get('auth_asym_id') != CHAIN:
                continue
            actual = by_label[int(atom['label_seq_id'])]
            if (atom['label_comp_id'] != actual['mon_id'] or atom['auth_seq_id'] != actual['pdb_auth_seq_id']
                    or atom['pdbx_PDB_model_num'] != '1'
                    or atom.get('pdbx_PDB_ins_code') not in ('?', '.', '')):
                raise ValueError('Atom identity, numbering, model or insertion policy differs.')
            if not all(math.isfinite(float(atom[k])) for k in ('Cartn_x', 'Cartn_y', 'Cartn_z')):
                raise ValueError('Nonfinite coordinate; visualization refused.')
        return {'status': 'verified_index_join', 'pdb_id': '1ISP', 'chain': CHAIN,
                'source_url': profile['structure']['coordinate_source_url'],
                'coordinate_sha256': COORDINATE_SOURCE_SHA256,
                'reference_sha256': profile['reference_sha256'],
                'mapping_sha256': hashlib.sha256(mapping_json.encode()).hexdigest(),
                'observed_count': joined['modelled_residue_count'],
                'missing_full_positions': [r['full_position'] for r in rows if r.get('coordinate_observed') is False],
                'geometry_validated': False, 'mapping': rows}
    except (ValueError, KeyError, TypeError, IndexError) as error:
        return {'status': 'unverified', 'reason': str(error)}


@lru_cache(maxsize=1)
def _structure_text():
    return _STRUCTURE.read_text(encoding='utf-8')


@lru_cache(maxsize=1)
def _bundle_text():
    return _BUNDLE.read_text(encoding='utf-8')


def sequence_neighborhood(full_position):
    """Pinned sequence context remains available when atom correspondence fails."""
    profile = registered_profile()
    target = validate_target(profile, 'sequence_plausibility_review')
    return [{'full_position': p, 'residue': target.reference_sequence[p - 1]}
            for p in range(max(1, full_position - 8), min(212, full_position + 8) + 1)]


def residue_selection(full_position, residue_map=None):
    """Resolve a full-reference position to a PDB selection, or to an explicit absence.

    Returns a dict whose 'selection' is None unless the registered join records an
    observed residue. A caller must never substitute its own residue number.
    """
    report = verify_reference(mapping=residue_map)
    if report['status'] != 'verified_index_join':
        return {'full_position': full_position, 'residue': None, 'status': 'unverified_mapping',
                'chain': CHAIN, 'pdb_auth_seq_id': None, 'selection': None,
                'note': 'Coordinate correspondence is unverified; no atoms are selected.'}
    rows = tuple(report['mapping'])
    row = next((r for r in rows if r.get('full_position') == full_position), None)
    if row is None:
        return {'full_position': full_position, 'residue': None,
                'status': 'unknown_position', 'chain': CHAIN,
                'pdb_auth_seq_id': None, 'selection': None,
                'note': 'Not a registered full-reference position.'}
    base = {'full_position': full_position, 'residue': row.get('residue'),
            'chain': CHAIN, 'pdb_auth_seq_id': row.get('pdb_auth_seq_id'),
            'protected': bool(row.get('protected'))}
    observed = row.get('coordinate_observed')
    if observed is None:
        return {**base, 'status': 'outside_deposited_construct',
                'selection': None, 'note': OUTSIDE_NOTE}
    if observed is not True:
        return {**base, 'status': 'unmodelled', 'selection': None,
                'note': UNMODELLED_NOTE}
    auth = row.get('pdb_auth_seq_id')
    if auth in (None, '', '?', '.'):
        # Registered as observed without a usable author number: refuse rather than guess.
        return {**base, 'status': 'unmodelled', 'selection': None,
                'note': 'Author numbering is incomplete for this residue; nothing is shown.'}
    return {**base, 'status': 'observed',
            'selection': {'chain': CHAIN, 'resi': int(auth)},
            'note': 'Author numbering taken from the registered coordinate join.'}


def protected_selections(residue_map=None):
    """The registered catalytic triad, resolved through the same join."""
    rows = _registered_map() if residue_map is None else tuple(residue_map)
    return [residue_selection(row['full_position'], residue_map=rows)
            for row in rows if row.get('protected')]


def _style_calls(highlight, protected, *, light=False):
    """Emit 3Dmol selection calls. A selection of None emits nothing at all."""
    calls = []
    for row in protected:
        picked = row.get('selection')
        if not picked:
            continue
        color = {108: '0x008577', 164: '0x2563eb', 187: '0x9333ea'}[row['full_position']]
        calls.append(
            f"viewer.addStyle({{chain:'{picked['chain']}',resi:{picked['resi']}}},"
            f"{{stick:{{color:{color},radius:0.25}}}});")
    # HIGHLIGHT_START/END bracket the reviewed-position block so a test can prove that
    # an unmodelled position produces no residue selector whatsoever.
    calls.append('/* HIGHLIGHT_START */')
    picked = (highlight or {}).get('selection')
    if picked:
        calls.append(
            f"viewer.addStyle({{chain:'{picked['chain']}',resi:{picked['resi']}}},"
            "{stick:{colorscheme:'orangeCarbon',radius:0.3}});")
        label = json.dumps(f"{highlight['residue']}{highlight['full_position']} · full", ensure_ascii=False)
        font_color = '0x00695c' if light else '0x6ce4cb'
        calls.append(
            f"viewer.addLabel({label}, {{font:'sans-serif',fontSize:12,"
            f"showBackground:false,fontColor:'{font_color}'}},"
            f"{{chain:'{picked['chain']}',resi:{picked['resi']}}});")
        calls.append('viewer.zoomTo();')
    else:
        calls.append('viewer.zoomTo();')
    calls.append('/* HIGHLIGHT_END */')
    return '\n'.join(calls)


def structure_panel_html(highlight=None, *, height=430, background=None, appearance='Dark', prediction=None):
    """Self-contained viewer document. Inlines the bundle and the coordinates."""
    if prediction is None and verify_reference()['status'] != 'verified_index_join':
        return '<p>Reference correspondence unverified. 3D visualization is disabled.</p>'
    if prediction is None and highlight is not None:
        highlight = residue_selection(highlight.get('full_position'))
    if appearance == 'Auto':
        document = structure_panel_html(highlight, height=height, background=background,
                                        appearance='Light', prediction=prediction)
        document = document.replace('</style>', '@media(prefers-color-scheme:dark){#note,#controls{color:#bdc7d3}button{background:#19222c;color:#bdc7d3;border-color:#64748b}}</style>')
        document = document.replace('backgroundColor:0xf8fafc', "backgroundColor:(window.matchMedia('(prefers-color-scheme:dark)').matches?0x0b0f14:0xf8fafc)")
        document = document.replace('  var originalView', "  window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',function(e){viewer.setBackgroundColor(e.matches?0x0b0f14:0xf8fafc);viewer.render();});\n  var originalView")
        return document
    protected = protected_selections() if prediction is None else []
    coordinates = _structure_text() if prediction is None else prediction['pdb']
    model_format = 'cif' if prediction is None else 'pdb'
    label = STRUCTURE_LABEL if prediction is None else prediction['label']
    fit_label = 'Fit reference' if prediction is None else 'Fit prediction'
    focus_selection = (highlight or {}).get('selection') if prediction is None else None
    focus_button = '<button id="focus" type="button">Focus residue</button>' if focus_selection else ''
    focus_script = ("document.getElementById('focus').addEventListener('click',function(){viewer.zoomTo("
                    + json.dumps(focus_selection) + ");viewer.render();});") if focus_selection else ''
    light = appearance == 'Light'
    background = background or ('0xf8fafc' if light else '0x0b0f14')
    text = '#334155' if light else '#bdc7d3'
    surface = '#ffffff' if light else '#19222c'
    border = '#cbd5e1' if light else '#64748b'
    document = f"""<!doctype html>
<html><head><meta charset="utf-8">
<script>{_bundle_text()}</script>
<style>
 html,body{{margin:0;padding:0;background:transparent;}}
 #box{{position:relative;width:100%;height:{height}px;border-radius:10px;overflow:hidden;}}
 #note{{font:11px ui-sans-serif,system-ui,sans-serif;color:{text};padding:6px 2px 0;line-height:1.5;}}
 #controls{{display:flex;flex-wrap:wrap;gap:8px;padding:6px 0;align-items:center;font:12px system-ui;color:{text};}}
 button{{border:1px solid {border};border-radius:6px;padding:6px 12px;background:{surface};color:{text};cursor:pointer;}}
 button:focus-visible{{outline:2px solid #007d6f;outline-offset:2px;}}
</style></head>
<body>
<div id="box"></div>
<div id="controls"><button id="fit" type="button">{fit_label}</button>{focus_button}<button id="rotate" type="button" aria-pressed="false">Rotate</button><span>Drag to rotate · scroll to zoom</span></div>
<div id="note">{escape(label)}</div>
<script id="cif" type="text/plain">{coordinates}</script>
<script>
(function(){{
  var viewer = $3Dmol.createViewer(document.getElementById('box'),
                                   {{backgroundColor:{background}}});
  viewer.addModel(document.getElementById('cif').textContent, '{model_format}');
  viewer.setStyle({{}}, {{cartoon:{{color:'spectrum',opacity:0.92}}}});
{_style_calls(highlight, protected, light=light)}
  viewer.render();
  var originalView = viewer.getView();
  {focus_script}
  document.getElementById('fit').addEventListener('click', function(){{
    viewer.spin(false); rotating=false;
    document.getElementById('rotate').textContent='Rotate';
    document.getElementById('rotate').setAttribute('aria-pressed','false');
    viewer.setView(originalView); viewer.zoomTo(); viewer.render();
  }});
  var rotating=false;
  document.getElementById('rotate').addEventListener('click', function(){{
    rotating=!rotating; viewer.spin(rotating ? 'y' : false, 0.6);
    this.textContent=rotating ? 'Stop rotation' : 'Rotate';
    this.setAttribute('aria-pressed', String(rotating));
  }});
  window.addEventListener('resize', function(){{ viewer.resize(); }});
}})();
</script>
</body></html>"""
    return document
