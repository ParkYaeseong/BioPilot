"""Local tutorial presentation; it can only activate existing safe tour controls."""
import base64
import json
from pathlib import Path

from app.guided_tour import STEPS

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'valid_input': '.st-key-tour_input',
    'protected_input': '.st-key-tour_input',
    'compare': '.st-key-comparison_table',
    'unmodelled_position': '.st-key-tour_structure',
    'protected_structure': '.st-key-tour_structure',
    'validation_trace': '.st-key-trace_card_1',
    'scoring_trace': '.st-key-trace_card_2',
    'provenance': '.st-key-tour_provenance',
}
COPY = (
    ('Check a valid request', 'A32V is entered in Input. Review its numbering and goal, then inspect the real local check against the registered reference.', 'Confirm that A32V passes, then select Next.'),
    ('See the guard stop a request', 'S108A is now entered in the same input. The local guard blocks this change at a protected catalytic site.', 'Code enforces this rule. Protection does not establish retained function.'),
    ('Compare the saved shortlist', 'The top three saved candidates are selected in Candidates. Compare their ranks and ESM sequence preferences under one scoring policy.', 'Selection and CSV export preserve the recorded scores and ranks.'),
    ('Check the structure evidence', 'An A32 candidate is selected in Structure. Full-reference position 32 has no atoms in 1ISP, so no residue is highlighted there.', 'Missing residues are reported; nearby atoms are never used as substitutes.'),
    ('Locate a protected residue', 'S108 is selected. Its verified numbering join highlights author residue 77. Drag the structure or use Rotate to inspect it.', 'This is the experimental reference structure, not validation of a variant.'),
    ('Inspect Meta\u2019s validation request', 'Meta trace shows the first recorded MCP call. Inspect its public rationale, actual arguments and result.', 'This is a saved run. No new Meta request is sent.'),
    ('Inspect the recorded scoring call', 'The second recorded MCP call is open. ESM computes sequence preferences; registered code ranks candidates under a common policy.', 'ESM scores are not measurements of T50, activity, solubility or Tm.'),
    ('Verify what supports the result', 'Evidence checks that the displayed candidates match the saved scores. Unknown costs and verification limits remain visible.', 'Finish or Close restores the inputs and selections you had before the tour.'),
)


def spotlight_document(index, *, appearance='Dark', playing=False):
    if index is None:
        return '<script>const d=window.parent.document;d.getElementById("bio-tour-root")?.remove();d.body.classList.remove("tour-overlay-active");</script>'
    step = STEPS[index]
    path = ROOT / 'assets' / 'tour' / (step.id + '.png')
    picture = ('data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')) if path.is_file() else None
    title, body, tip = COPY[index]
    payload = {'index': index, 'count': len(STEPS), 'selector': TARGETS[step.id],
               'title': title, 'body': body, 'tip': tip, 'picture': picture,
               'light': appearance == 'Light', 'playing': playing,
               'focus_height': 340 if step.focus == 'trace' else (450 if step.focus == 'evidence' else None)}
    data = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    script = (ROOT/'tour_spotlight.js').read_text(encoding='utf-8')
    return '<script>const tourData=' + data + ';\n' + script + '</script>'
