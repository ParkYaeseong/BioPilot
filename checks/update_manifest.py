"""Explicit local source-manifest update; never includes .env or model files."""
import hashlib
from pathlib import Path
from package_files import package_files

def main():
    root = Path(__file__).resolve().parents[1]
    rows = []
    for path in sorted(package_files(root)):
        if path.name == 'MANIFEST.sha256':
            continue
        rows.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}')
    (root/'MANIFEST.sha256').write_text('\n'.join(rows)+'\n', encoding='utf-8', newline='\n')
    print(f'Updated source manifest: {len(rows)} files (local credentials/environments excluded)')

if __name__ == '__main__':
    main()
