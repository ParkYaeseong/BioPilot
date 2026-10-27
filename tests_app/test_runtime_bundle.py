from pathlib import Path
import json
import pytest

def test_runtime_source_allowlist_has_unique_members():
    from app.core.runtime_bundle import CODE_ALLOWLIST, DATA_ALLOWLIST
    paths=CODE_ALLOWLIST+DATA_ALLOWLIST
    assert len(paths)==len(set(paths))
from app.core.runtime_bundle import build_runtime_bundle

ROOT = Path(__file__).resolve().parents[1]

def test_only_reviewed_product_sources_are_provisioned(tmp_path):
    destination = tmp_path / 'product'
    manifest = build_runtime_bundle(ROOT, destination)
    files = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
    assert 'app/mcp_server.py' in files
    assert 'reference/target_profile.json' in files
    assert not any(p.split('/')[0] in {'evaluation_private', 'evaluation', 'tests', 'tests_app', 'checks', 'docs', 'BioPilot_Atlas_Local_Start'} for p in files)
    assert not any('.env' in p or '__pycache__' in p for p in files)
    assert manifest['source_mode'] == 'local_provisioned_code'
    assert manifest['files']
    assert json.loads((destination / 'bundle_manifest.json').read_text()) == manifest

def test_existing_destination_is_never_overwritten(tmp_path):
    destination = tmp_path / 'product'
    destination.mkdir()
    (destination / 'keep.txt').write_text('untouched')
    with pytest.raises(ValueError, match='exists'):
        build_runtime_bundle(ROOT, destination)
    assert (destination / 'keep.txt').read_text() == 'untouched'

def test_source_symlink_is_rejected(tmp_path):
    # Windows non-admin environments cannot always create symlinks.
    source = tmp_path / 'source'
    source.mkdir()
    try:
        (source / 'app').symlink_to(ROOT / 'app', target_is_directory=True)
    except OSError:
        pytest.skip('Symlink creation requires an OS privilege')
    with pytest.raises(ValueError, match='symlink'):
        build_runtime_bundle(source, tmp_path / 'product')
