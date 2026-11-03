"""Source inventory excludes local credentials, tools, caches and environments."""
from pathlib import Path

EXCLUDED = frozenset({'.git', '.venv', '.runtime', '.cache', '.pytest_cache',
    '.superpowers', '__pycache__', 'BioPilot_Atlas_Local_Start', 'local_artifacts',
    '.ssh', '.ruff_cache', '.mypy_cache', '.tox', '.nox', 'htmlcov',
    'build', 'dist'})
EXCLUDED_FOLDED = frozenset(name.casefold() for name in EXCLUDED)
LOCAL_SUFFIXES = ('.pyc', '.pyo', '.safetensors', '.pt', '.pth',
    '.db', '.db-wal', '.db-shm', '.db-journal', '.pem', '.key', '.ppk', '.p12', '.pfx',
    '.mp4', '.mov', '.mkv', '.webm', '.wav', '.mp3', '.zip', '.7z', '.tar', '.gz', '.log')
EVALUATOR_SCAFFOLDS = frozenset({'assay_protocol.json','dataset_reconciliation.json'})

def package_files(root: Path):
    # Prune before descent: never read the local secret or model/cache contents.
    for directory, dirs, files in root.walk():
        if directory==root/'evaluation_private':
            # Preserve only the original label-free protocol scaffolding. Local
            # assay imports, frozen predictions and evaluator results stay local.
            dirs[:]=[]
            files=[name for name in files if name in EVALUATOR_SCAFFOLDS]
        else:
            dirs[:] = [d for d in dirs if d.casefold() not in EXCLUDED_FOLDED
                       and not d.casefold().endswith('.egg-info') and not (directory/d).is_symlink()
                       and (d.casefold()!='evaluation_private' or directory==root)]
        for name in files:
            path = directory/name
            lower=name.casefold()
            if (lower == '.env' or lower.endswith('.env')
                    or (lower.startswith('.env.') and lower != '.env.example')):
                continue
            if directory == root/'validation' and lower.endswith('.txt'):
                continue
            if (directory == root/'submission' and lower.endswith('.md')
                    and lower.startswith(('form_answers', 'form_draft'))):
                continue
            if (path.is_symlink() or lower.endswith(LOCAL_SUFFIXES)
                    or lower in {'.coverage', 'coverage.xml', '.ds_store', 'thumbs.db'}
                    or '.sqlite' in lower):
                continue
            yield path
