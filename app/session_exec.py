"""Launch a bounded live review as a separate process, and bound what it may spend.

Kept apart from the replay viewer on purpose. `app/viewer.py` and the modules it
imports are asserted to contain no network or subprocess capability at all, so
opening a saved run provably cannot dispatch work. This module is the one place that
may start a run, and it refuses anything outside the registered contract *before* a
process is created, so an invalid or protected request never reaches a provider.

Command construction is separate from execution so the safety properties can be
tested without dispatching anything.
"""
from pathlib import Path
import re
import subprocess
import sys

from app.core.targets import PROTECTED
from app.science.models import MODEL_REGISTRY

PROTECTED_FULL_POSITIONS = tuple(full for _, full, _ in PROTECTED)
MAX_POSITIONS_PER_RUN = 10
REGION = (32, 212)


def validate_session_request(positions, model_key):
    """Refuse out-of-contract work locally, before any process or provider is reached."""
    if model_key not in MODEL_REGISTRY:
        raise ValueError('Unknown ESM model key; a session never invents a checkpoint')
    if not isinstance(positions, (list, tuple)) or not positions:
        raise ValueError('Select at least one full-reference position')
    if len(positions) > MAX_POSITIONS_PER_RUN:
        raise ValueError(f'At most {MAX_POSITIONS_PER_RUN} positions per run')
    if len(set(positions)) != len(positions):
        raise ValueError('Duplicate positions are not a larger review')
    for position in positions:
        if type(position) is not int or not REGION[0] <= position <= REGION[1]:
            raise ValueError(f'Positions must be full-reference {REGION[0]}..{REGION[1]}')
        if position in PROTECTED_FULL_POSITIONS:
            raise ValueError(f'Protected catalytic site {position} cannot be reviewed')
    return sorted(positions)


class SessionBudget:
    """A hard ceiling the surface cannot talk its way past."""

    def __init__(self, max_runs=3, max_requests_per_run=4):
        if max_runs < 1 or max_requests_per_run < 1:
            raise ValueError('A session budget must allow at least one bounded run')
        self.max_runs = max_runs
        self.max_requests_per_run = max_requests_per_run
        self._spent = []

    @property
    def remaining_runs(self):
        return max(0, self.max_runs - len(self._spent))

    def spend(self, run_key):
        if run_key not in self._spent:
            self._spent.append(run_key)

    def check(self):
        if self.remaining_runs <= 0:
            raise ValueError(
                f'Session budget spent: {len(self._spent)} of {self.max_runs} runs used. '
                'Start a new session deliberately rather than raising the cap here.')


def prepare_command(python, workspace, *, positions, model_key, max_requests, esm_env,
                    goal_text=None):
    """Build the unpaid preparation command. Never carries a live flag."""
    return [str(python), '-m', 'app.cli', 'prepare',
            '--workspace', str(workspace), '--review',
            '--positions', *[str(p) for p in positions],
            '--model-key', str(model_key),
            '--esm-env-file', str(esm_env),
            '--max-meta-requests', str(max_requests)] + (
                ['--goal-text', str(goal_text)] if goal_text else [])


def review_command(python, workspace, *, esm_env, armed):
    """Build the review command. Live flags appear only when explicitly armed."""
    command = [str(python), '-m', 'app.cli', 'meta-review',
               '--workspace', str(workspace), '--esm-env-file', str(esm_env)]
    if armed:
        command += ['--live', '--ack-small-test']
    return command


def run_session(root, workspace, *, positions, model_key, esm_env, budget, armed,
                goal_text=None, timeout_seconds=300):
    """Prepare and run one bounded review. Returns the completed process results."""
    positions = validate_session_request(positions, model_key)
    budget.check()
    workspace = Path(workspace)
    if workspace.exists():
        raise ValueError('Refusing to reuse a session workspace; each run gets fresh state')
    python = sys.executable
    prepared = subprocess.run(
        prepare_command(python, workspace, positions=positions, model_key=model_key,
                        max_requests=budget.max_requests_per_run, esm_env=esm_env,
                        goal_text=goal_text),
        cwd=str(root), capture_output=True, text=True, timeout=timeout_seconds)
    if prepared.returncode != 0:
        return {'stage': 'prepare', 'returncode': prepared.returncode,
                'stdout': prepared.stdout, 'stderr': prepared.stderr}
    budget.spend(str(workspace))
    reviewed = subprocess.run(
        review_command(python, workspace, esm_env=esm_env, armed=armed),
        cwd=str(root), capture_output=True, text=True, timeout=timeout_seconds)
    return {'stage': 'review', 'returncode': reviewed.returncode,
            'stdout': reviewed.stdout, 'stderr': reviewed.stderr,
            'prepared_stdout': prepared.stdout, 'armed': bool(armed),
            'positions': positions, 'model_key': model_key}


# ASCII-only boundaries on purpose: \b treats Hangul as a word character, so a
# request written as 'A32V를 검토해줘' or 'S108을 바꿔줘' would never match.
_VARIANT = re.compile(r'(?<![A-Za-z0-9])([ACDEFGHIKLMNPQRSTVWY])(\d{1,3})'
                      r'([ACDEFGHIKLMNPQRSTVWY])?(?![0-9A-Za-z])')
_BARE = re.compile(r'(?:position|positions|위치|잔기)\s*((?:\d{1,3}[,\s와및and]*)+)', re.IGNORECASE)


def extract_positions(text):
    """Read full-reference positions out of plain language, refusing nothing.

    Deliberately neutral: a protected site must survive extraction so the guard can
    refuse it visibly and for free, rather than the request quietly becoming something
    else. Only in-range numbers are taken, so prose like "1.30 angstrom" is not a
    position. The result is echoed to the operator before anything is armed.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    found = []
    for match in _VARIANT.finditer(text):
        position = int(match.group(2))
        if REGION[0] <= position <= REGION[1]:
            found.append(position)
    for match in _BARE.finditer(text):
        for chunk in re.findall(r'\d{1,3}', match.group(1)):
            position = int(chunk)
            if REGION[0] <= position <= REGION[1]:
                found.append(position)
    return sorted(set(found))
