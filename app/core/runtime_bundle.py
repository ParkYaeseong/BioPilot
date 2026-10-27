"""Provision a label-free product workspace from an explicit reviewed file list.

This separates runtime contents; it is not an operating-system sandbox. The
controlled host has no file/shell tools. Native-host ACL isolation is unverified.
"""
import hashlib
import json
from pathlib import Path
import shutil

CODE_ALLOWLIST = (
    'app/__init__.py',
    'app/core/__init__.py',
    'app/core/targets.py',
    'app/core/capabilities.py',
    'app/core/runs.py',
    'app/core/budget.py',
    'app/core/artifacts.py',
    'app/core/runtime_bundle.py',
    'app/core/tool_executor.py',
    'app/science/__init__.py',
    'app/science/esm_engine.py',
    'app/science/ranking.py',
    'app/science/models.py',
    'app/science/providers.py',
    'app/science/inference_service.py',
    'app/science/provider_config.py',
    'app/mcp_server.py',
    'app/host/__init__.py',
    'app/host/meta_client.py',
    'app/host/mcp_bridge.py',
    'app/host/runner.py',
)
DATA_ALLOWLIST = (
    'reference/target_profile.json',
    'reference/residue_map.json',
    'reference/lipase_full_212.fasta',
    'reference/1ISP_A_deposited_181.fasta',
    'schemas/tools.mcp.json',
)

def _check_file(source_root: Path, relative: str) -> Path:
    path = source_root / relative
    current = path
    while current != source_root:
        if current.is_symlink():
            raise ValueError('Runtime source symlink is not allowed')
        current = current.parent
    if not path.is_file() or source_root not in path.resolve().parents:
        raise ValueError('Required reviewed runtime source is missing or outside source root')
    return path

def build_runtime_bundle(source_root, destination):
    source_root = Path(source_root).absolute()
    if source_root.is_symlink():
        raise ValueError('Runtime source symlink is not allowed')
    source_root = source_root.resolve()
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Runtime destination already exists; never overwrite a workspace')
    if source_root == destination or destination in source_root.parents:
        raise ValueError('Runtime destination must be a dedicated new directory')
    sources = [(relative, _check_file(source_root, relative))
               for relative in CODE_ALLOWLIST + DATA_ALLOWLIST]
    destination.mkdir(parents=True, exist_ok=False)
    records = []
    for relative, source in sources:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({'path': relative, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    body = json.dumps(records, sort_keys=True, separators=(',', ':')).encode()
    manifest = {'bundle_version': 1, 'source_mode': 'local_provisioned_code',
                'files': records, 'bundle_sha256': hashlib.sha256(body).hexdigest(),
                'os_sandbox_verified': False}
    (destination / 'bundle_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest
