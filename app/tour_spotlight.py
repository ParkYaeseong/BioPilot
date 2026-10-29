"""Local tutorial presentation; it can only activate existing safe tour controls."""
import base64
import json
from pathlib import Path

from app.guided_tour import STEPS

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'overview': '.st-key-tour_overview',
    'valid_input': '.st-key-tour_input',
    'protected_input': '.st-key-tour_input',
    'compare': '.st-key-comparison_table',
    'unmodelled_position': '.st-key-tour_structure',
    'protected_structure': '.st-key-tour_structure',
    'validation_trace': '.st-key-trace_card_1',
    'scoring_trace': '.st-key-trace_card_2',
    'provenance': '.st-key-tour_provenance',
}
COPY = {'overview': ('Understand the saved review',
              'Overview introduces the research purpose, saved ESM results, Meta execution stages and '
              'verification limits before any diagnostics.',
              'REPLAY shows recorded evidence. Tutorial controls do not call an API or GPU.'),
 'compare': ('Compare the saved shortlist',
             'The top three saved candidates are selected in Candidates. Compare their ranks and ESM '
             'sequence preferences under one scoring policy.',
             'Selection and CSV export preserve the recorded scores and ranks.'),
 'validation_trace': ('Inspect Meta’s validation request',
                      'Agent Trace shows the first recorded MCP call. Inspect its public rationale, actual '
                      'arguments and result.',
                      'This is a saved run. No new Meta request is sent.'),
 'scoring_trace': ('Inspect the recorded scoring call',
                   'The second recorded MCP call is open. ESM computes sequence preferences; registered code '
                   'ranks candidates under a common policy.',
                   'ESM scores are not measurements of T50, activity, solubility or Tm.'),
 'provenance': ('Verify what supports the result',
                'Evidence checks that the displayed candidates match the saved scores. Unknown costs and '
                'verification limits remain visible.',
                'Local consistency checks do not establish external authenticity or biological efficacy.'),
 'unmodelled_position': ('Check the reference mapping',
                         'Evidence shows Reference mapping & saved structures. Full-reference position 32 '
                         'has no atoms in 1ISP, so no residue is highlighted there.',
                         'Missing residues are reported; nearby atoms are never used as substitutes.'),
 'protected_structure': ('Locate a protected residue',
                         'S108 is selected. Its verified numbering join highlights author residue 77. Drag '
                         'the reference structure or use Rotate to inspect it.',
                         'The reference and saved predictions do not validate a variant or its atom '
                         'geometry.'),
 'valid_input': ('Try an optional local diagnostic',
                 'Advanced diagnostics checks A32V locally. This demonstration is separate from the '
                 'historical Meta run.',
                 'No saved evidence is changed and no model is called.'),
 'protected_input': ('Inspect the local protection guard',
                     'The optional local diagnostic blocks S108A at a protected site. This is code behavior, '
                     'not a recorded Meta decision.',
                     'Finish restores the previous view and selections.')}


def spotlight_document(index, *, appearance='Dark', playing=False):
    if index is None:
        return '<script>const d=window.parent.document;d.getElementById("bio-tour-root")?.remove();d.body.classList.remove("tour-overlay-active");</script>'
    step = STEPS[index]
    path = ROOT / 'assets' / 'tour' / (step.id + '.png')
    picture = ('data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')) if path.is_file() else None
    title, body, tip = COPY[step.id]
    payload = {'index': index, 'count': len(STEPS), 'selector': TARGETS[step.id],
               'title': title, 'body': body, 'tip': tip, 'picture': picture,
               'light': appearance == 'Light', 'auto': appearance == 'Auto', 'playing': playing,
               'focus_height': 340 if step.focus == 'trace' else (450 if step.focus in {'overview', 'evidence'} else None)}
    data = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    script = (ROOT/'tour_spotlight.js').read_text(encoding='utf-8')
    return '<script>const tourData=' + data + ';\n' + script + '</script>'
