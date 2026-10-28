"""Source inventory excludes local credentials, tools, caches and environments."""
from pathlib import Path

EXCLUDED = frozenset({'.git', '.venv', '.runtime', '.cache', '.pytest_cache',
    '.superpowers', '__pycache__', 'BioPilot_Atlas_Local_Start', 'local_artifacts'})
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
            dirs[:] = [d for d in dirs if d not in EXCLUDED and not (directory/d).is_symlink()
                       and (d.casefold()!='evaluation_private' or directory==root)]
        for name in files:
            path = directory/name
            lower=name.casefold()
            if name == '.env' or (name.startswith('.env.') and name != '.env.example'):
                continue
            if (path.is_symlink() or lower.endswith(('.pyc','.pyo','.safetensors','.pt','.pth',
                                                   '.db','.db-wal','.db-shm','.db-journal'))
                    or '.sqlite' in lower):
                continue
            yield path
