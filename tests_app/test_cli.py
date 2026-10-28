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
    assert set(report['tools']) == {'validate_target_context', 'get_run_status', 'retrieve_atlas_evidence'}

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

def test_public_esm_configuration_is_separate_from_meta_secret_file(tmp_path):
    workspace=tmp_path/'separate-config'
    config=tmp_path/'local-esm.env'
    config.write_text('ESM_BACKEND=local\nESM_MODEL_KEY=esm150\nESM_WEIGHTS_SHA256='+
                      'a'*64+'\nESM_TOKENIZER_SHA256='+'b'*64+'\n')
    result=run('prepare','--workspace',workspace,'--review','--positions','32',
               '--esm-env-file',config)
    assert result.returncode==0,result.stderr
    state=json.loads(run('status','--workspace',workspace).stdout)
    assert state['input']['model_pins']['esm150']['expected_weights_sha256']=='a'*64


def _synthetic_local_backend(monkeypatch):
    """Exercise real CLI/scoring/save behavior with explicitly synthetic logits."""
    from app.science import esm_engine
    amino_acids='ACDEFGHIKLMNPQRSTVWY'
    forwards=[]

    class Backend:
        mask_token_id=22
        provenance={'checkpoint':'esm2_t30_150M_UR50D','weights_sha256':'a'*64,
                    'tokenizer_sha256':'b'*64,'implementation':'synthetic_cli_fixture',
                    'precision':'float32','source_mode':'synthetic_fixture'}

        def __init__(self,*args,**kwargs):
            pass

        def token_id(self,residue):
            return amino_acids.index(residue)+1

        def tokenize(self,sequence):
            return [0]+[self.token_id(residue) for residue in sequence]+[21]

        def forward(self,tokens):
            forwards.append(list(tokens))
            return [[float(index) for index in range(23)] for _ in tokens]

    monkeypatch.setattr(esm_engine,'LocalHFBackend',Backend)
    return forwards


def _local_score_args(tmp_path,output):
    return ['score-local','--checkpoint-dir',str(tmp_path/'fixture-checkpoint'),
            '--weights-sha256','a'*64,'--tokenizer-sha256','b'*64,
            '--positions','32','--output',str(output)]


def test_score_local_preserves_score_hash_and_saves_separate_ranked_review(tmp_path,monkeypatch,capsys):
    from app.cli import main
    from app.core.artifacts import canonical_hash
    _synthetic_local_backend(monkeypatch)
    path=tmp_path/'scores.json'
    assert main(_local_score_args(tmp_path,path))==0
    output=json.loads(capsys.readouterr().out)
    artifact=json.loads(path.read_text())
    assert 'ranked_candidates' not in artifact
    assert canonical_hash({key:value for key,value in artifact.items() if key!='artifact_sha256'})==artifact['artifact_sha256']
    assert len(artifact['rows'])==19
    assert output['artifact_sha256']==artifact['artifact_sha256']
    review=json.loads(Path(output['review_artifact']).read_text())
    assert review['score_artifact_sha256']==artifact['artifact_sha256']
    assert review['source_mode']==artifact['source_mode']=='synthetic_fixture'
    assert review['rank_policy']==artifact['rank_policy']
    assert canonical_hash({key:value for key,value in review.items() if key!='artifact_sha256'})==review['artifact_sha256']
    assert output['review_artifact_sha256']==review['artifact_sha256']
    assert review['ranked_candidates']==sorted(artifact['rows'],key=lambda row:(-row['score'],row['candidate_id']))


def test_score_local_optional_cache_avoids_repeated_forward(tmp_path,monkeypatch,capsys):
    from app.cli import main
    forwards=_synthetic_local_backend(monkeypatch)
    cache=tmp_path/'score-cache'
    for name in ('first.json','second.json'):
        assert main(_local_score_args(tmp_path,tmp_path/name)+['--cache-dir',str(cache)])==0
        capsys.readouterr()
    second=json.loads((tmp_path/'second.json').read_text())
    assert len(forwards)==1
    assert second['cached_positions_1based']==[32]
    assert second['source_mode']=='synthetic_fixture'


def test_score_local_runtime_error_returns_sanitized_diagnostic(tmp_path,monkeypatch,capsys):
    from app.cli import main
    from app.science import esm_engine

    def fail(*args,**kwargs):
        raise RuntimeError('private fixture detail must not reach public output')

    monkeypatch.setattr(esm_engine,'LocalHFBackend',fail)
    assert main(_local_score_args(tmp_path,tmp_path/'absent.json'))==2
    output=json.loads(capsys.readouterr().out)
    assert output['status']=='blocked'
    assert output['diagnostic']=={'stage':'score-local','error_type':'RuntimeError',
                                  'code':'local_inference_runtime_error','automatic_retry':False}
    assert 'private fixture detail' not in json.dumps(output)
    assert not (tmp_path/'absent.json').exists()


def test_score_local_existing_review_is_preserved_before_inference(tmp_path,monkeypatch,capsys):
    from app.cli import main
    forwards=_synthetic_local_backend(monkeypatch)
    path=tmp_path/'scores.json'
    review=tmp_path/'scores.json.review.json'
    review.write_text('preserved prior review')
    assert main(_local_score_args(tmp_path,path))==2
    assert json.loads(capsys.readouterr().out)['status']=='blocked'
    assert review.read_text()=='preserved prior review'
    assert not path.exists()
    assert forwards==[]
