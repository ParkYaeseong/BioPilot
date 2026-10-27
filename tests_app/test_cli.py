import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.run([sys.executable,'-m','app.cli',*map(str,args)],cwd=ROOT,
                          capture_output=True,text=True,timeout=30)

def test_validate_cli(tmp_path):
    result=run('validate','--variant','A32V')
    assert result.returncode==0,result.stderr
    output=json.loads(result.stdout)
    assert output['variant']['mature_position']==1
    assert output['target']['coordinate_mapping_verified'] is False

def test_invalid_variant_cli(tmp_path):
    result=run('validate','--variant','S108A')
    assert result.returncode==2
    assert json.loads(result.stdout)['status']=='blocked'

def test_prepare_and_real_mcp_cli(tmp_path):
    workspace=tmp_path/'session'
    result=run('prepare','--workspace',workspace)
    assert result.returncode==0,result.stderr
    assert (workspace/'launcher.json').is_file()
    assert not (workspace/'product/evaluation_private').exists()
    result=run('mcp-smoke','--workspace',workspace)
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout)
    assert report['status']=='ok'
    assert report['protocol_version']=='2025-11-25'
    assert len(report['tools'])==2

def test_live_is_blocked_without_explicit_flags(tmp_path):
    result=run('meta-smoke','--workspace',tmp_path/'absent')
    assert result.returncode==2
    assert 'approval' in json.loads(result.stdout)['reason']

def test_esm_status_is_safe_and_explicitly_default_blocked(tmp_path):
    result=run('esm-status')
    assert result.returncode==2
    output=json.loads(result.stdout)
    assert output['backend']=='modal'
    assert output['status']=='unconfigured'
    assert output['external_request_attempts']==0
    assert not any('API_KEY' in key for key in output)

def test_review_plan_freezes_positions_and_model_without_dispatch(tmp_path):
    workspace=tmp_path/'review'
    result=run('prepare','--workspace',workspace,'--review','--positions','32','--model-key','esm650')
    assert result.returncode==0,result.stderr
    context=json.loads((workspace/'launcher.json').read_text())
    result=run('status','--workspace',workspace)
    state=json.loads(result.stdout)
    assert state['input']['esm_model_key']=='esm650'
    assert state['input']['positions_1based']==[32]
    assert state['input']['requested_budget']['max_gpu_seconds']==0
    assert state['meta_requests_reserved']==0
