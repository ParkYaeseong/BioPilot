"""Source inventory excludes local credentials, tools, caches and environments."""
from pathlib import Path

EXCLUDED = frozenset({'.git', '.venv', '.runtime', '.cache', '.pytest_cache',
    '.superpowers', '__pycache__', 'BioPilot_Atlas_Local_Start', 'local_artifacts'})

def package_files(root: Path):
    # Prune before descent: never read the local secret or model/cache contents.
    for directory, dirs, files in root.walk():
        dirs[:] = [d for d in dirs if d not in EXCLUDED and not (directory/d).is_symlink()]
        for name in files:
            path = directory/name
            if name == '.env' or (name.startswith('.env.') and name != '.env.example'):
                continue
            if path.is_symlink() or name.endswith(('.pyc', '.pyo')):
                continue
            yield path
