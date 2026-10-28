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
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_RESIDUE_MAP = _ROOT / 'reference' / 'residue_map.json'
_STRUCTURE = _ROOT / 'reference' / '1ISP.cif'
_BUNDLE = _ROOT / 'app' / 'vendor' / '3Dmol-min.js'

CHAIN = 'A'
STRUCTURE_LABEL = (
    'Experimental wild-type reference structure 1ISP (X-ray, 1.30 A, chain A). '
    'Not a mutant structure, not validated geometry, and not evidence of activity '
    'or retained function.')
UNMODELLED_NOTE = (
    'Deposited in 1ISP but not modelled: this residue has no atoms in the structure, '
    'so no position can be shown. Nearby residues are not a substitute.')
OUTSIDE_NOTE = (
    'Outside the deposited construct. Full positions 1-31 are not part of the '
    '181-residue deposited sequence and have no structural counterpart.')


@lru_cache(maxsize=1)
def _registered_map():
    return tuple(json.loads(_RESIDUE_MAP.read_text(encoding='utf-8'))['mapping'])


@lru_cache(maxsize=1)
def _structure_text():
    return _STRUCTURE.read_text(encoding='utf-8')


@lru_cache(maxsize=1)
def _bundle_text():
    return _BUNDLE.read_text(encoding='utf-8')


def residue_selection(full_position, residue_map=None):
    """Resolve a full-reference position to a PDB selection, or to an explicit absence.

    Returns a dict whose 'selection' is None unless the registered join records an
    observed residue. A caller must never substitute its own residue number.
    """
    rows = _registered_map() if residue_map is None else tuple(residue_map)
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
        calls.append(
            f"viewer.addStyle({{chain:'{picked['chain']}',resi:{picked['resi']}}},"
            "{stick:{colorscheme:'greenCarbon',radius:0.22}});")
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
        calls.append(
            f"viewer.zoomTo({{chain:'{picked['chain']}',resi:{picked['resi']}}});")
    else:
        calls.append('viewer.zoomTo();')
    calls.append('/* HIGHLIGHT_END */')
    return '\n'.join(calls)


def structure_panel_html(highlight=None, *, height=430, background=None, appearance='Dark', prediction=None):
    """Self-contained viewer document. Inlines the bundle and the coordinates."""
    protected = protected_selections() if prediction is None else []
    coordinates = _structure_text() if prediction is None else prediction['pdb']
    model_format = 'cif' if prediction is None else 'pdb'
    label = STRUCTURE_LABEL if prediction is None else prediction['label']
    fit_label = 'Fit reference' if prediction is None else 'Fit prediction'
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
 #controls{{display:flex;gap:8px;padding:6px 0;align-items:center;font:12px system-ui;color:{text};}}
 button{{border:1px solid {border};border-radius:6px;padding:6px 12px;background:{surface};color:{text};cursor:pointer;}}
 button:focus-visible{{outline:2px solid #007d6f;outline-offset:2px;}}
</style></head>
<body>
<div id="box"></div>
<div id="controls"><button id="fit" type="button">{fit_label}</button><button id="rotate" type="button" aria-pressed="false">Rotate</button><span>Drag to rotate · scroll to zoom</span></div>
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
