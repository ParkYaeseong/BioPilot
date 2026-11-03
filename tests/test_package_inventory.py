"""Source archives retain evaluator scaffolding but exclude local data/weights."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from checks.package_files import package_files


ROOT=Path(__file__).resolve().parents[1]
SCAFFOLDS={'assay_protocol.json','dataset_reconciliation.json'}


def write(root,relative):
    path=root/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('synthetic test material only\n',encoding='utf-8')
    return path


def inventory(root):
    return {path.relative_to(root).as_posix() for path in package_files(root)}


def test_only_original_root_evaluator_scaffolds_are_package_sources(tmp_path):
    keep={'README.md'}|{'evaluation_private/'+name for name in SCAFFOLDS}
    excluded={'evaluation_private/raw_assay.csv','evaluation_private/report.json',
              'evaluation_private/real_run/assay_protocol.json',
              'evaluation_private/real_run/frozen_predictions.json',
              'nested/evaluation_private/assay_protocol.json'}
    for relative in keep|excluded:
        write(tmp_path,relative)
    assert inventory(tmp_path)==keep


def test_private_run_directories_are_pruned_before_descent(tmp_path,monkeypatch):
    write(tmp_path,'evaluation_private/do_not_enter/raw_assay.csv')
    original_walk=Path.walk

    def guarded_walk(root,*args,**kwargs):
        for directory,dirs,files in original_walk(root,*args,**kwargs):
            assert directory.name!='do_not_enter','Private run directory was traversed'
            yield directory,dirs,files

    monkeypatch.setattr(Path,'walk',guarded_walk)
    assert inventory(tmp_path)==set()


@pytest.mark.parametrize('relative',[
    'weights/model.safetensors','weights/MODEL.PT','models/checkpoint.pth',
    'app/runtime.sqlite','state/runs.sqlite3','state/run.sqlite-wal',
    'state/run.db','state/run.db-shm',
])
def test_local_weights_and_databases_are_not_package_sources(tmp_path,relative):
    write(tmp_path,relative)
    write(tmp_path,'app/source.py')
    assert inventory(tmp_path)=={'app/source.py'}


def test_manifest_updater_emits_lf_bytes_including_on_windows(tmp_path):
    checks=tmp_path/'checks'
    checks.mkdir()
    for name in ('package_files.py','update_manifest.py'):
        shutil.copyfile(ROOT/'checks'/name,checks/name)
    write(tmp_path,'README.md')
    result=subprocess.run([sys.executable,str(checks/'update_manifest.py')],
        capture_output=True,text=True,encoding='utf-8',timeout=30)
    assert result.returncode==0,result.stderr
    manifest=(tmp_path/'MANIFEST.sha256').read_bytes()
    assert b'\r' not in manifest
    assert manifest.endswith(b'\n')
    assert len(manifest.splitlines())==3


@pytest.mark.parametrize('relative',[
    '.ssh/id_ed25519', 'operator/server.pem', 'operator/client.ppk',
    'config/local.env', 'submission/FORM_ANSWERS_next.md',
    'submission/FORM_DRAFT_next.md', 'demo/recording.mp4',
    'demo/narration.wav', 'exports/source.zip', 'logs/session.log',
    '.ruff_cache/state', 'htmlcov/index.html', 'dist/package.json',
    'validation/current_test_output.txt',
])
def test_source_delivery_excludes_private_and_generated_material(tmp_path,relative):
    write(tmp_path,relative)
    write(tmp_path,'app/source.py')
    assert inventory(tmp_path)=={'app/source.py'}


def test_public_scientific_evidence_and_readme_media_remain_packaged(tmp_path):
    keep={'docs/images/feature.gif','demo/artifacts/structures/prediction.pdb',
          'validation/optional_science_runtime_20261028.json',
          'validation/history_v2/science_tests.txt','prompts/runtime/system.txt',
          'requirements/workbench.txt','templates/.env.example'}
    for relative in keep:
        write(tmp_path,relative)
    assert inventory(tmp_path)==keep


@pytest.mark.parametrize('relative',[
    'AGENTS.md', 'START_HERE_KO.md', 'MANIFEST.sha256',
    'docs/STATUS.md', 'docs/01_product_spec.md',
    'docs/superpowers/plans/design.md', 'docs/archive/demo/old_script.md',
    'docs/images/biopilot-demo.gif',
])
def test_local_development_material_is_not_published_as_source(tmp_path,relative):
    write(tmp_path,relative)
    write(tmp_path,'README.md')
    assert inventory(tmp_path)=={'README.md'}
