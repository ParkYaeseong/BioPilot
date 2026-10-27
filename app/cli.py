"""Local BioPilot launcher. Default commands are offline; no model downloads."""
import argparse
import asyncio
from dataclasses import asdict
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from app.core.artifacts import ArtifactStore
from app.core.runs import RunService
from app.core.runtime_bundle import build_runtime_bundle
from app.core.targets import FRAME, normalize_sequence, registered_profile, validate_target, validate_variant
from app.host.mcp_bridge import connect

ROOT=Path(__file__).resolve().parents[1]

def _load_workspace(workspace):
    workspace=Path(workspace).resolve()
    data=json.loads((workspace/'launcher.json').read_text(encoding='utf-8'))
    return workspace,data,RunService(workspace/'state/runs.sqlite')

async def _mcp_smoke(workspace,data):
    async with connect(workspace/'product',workspace/'state/runs.sqlite',data['run_id'],data['owner_id']) as bridge:
        tools=await bridge.list_allowed()
        result=await bridge.call('validate_target_context',{'reference_id':data['reference_id'],
                                                          'reason_brief':'Local protocol validation'})
        return {'status':result['status'],'source_mode':'live_local_protocol',
                'protocol_version':bridge.protocol_version,'sdk_version':importlib.metadata.version('mcp'),
                'tools':[t['name'] for t in tools], 'result':result,
                'bundle_sha256':data['bundle_sha256'],'external_request_attempts':0}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    validate=commands.add_parser('validate',help='Offline registered reference and variant checks')
    validate.add_argument('--variant')
    validate.add_argument('--frame',default=FRAME)
    validate.add_argument('--sequence')
    validate.add_argument('--objective',default='sequence_plausibility_review')
    prepare=commands.add_parser('prepare',help='Build a fresh allowlisted workspace; no paid execution')
    prepare.add_argument('--workspace',type=Path,required=True)
    prepare.add_argument('--objective',default='sequence_plausibility_review')
    prepare.add_argument('--review',action='store_true')
    prepare.add_argument('--positions',type=int,nargs='+',default=[32])
    prepare.add_argument('--model-key',choices=['esm35','esm150','esm650'],default='esm150')
    prepare.add_argument('--usd-micros',type=int)
    prepare.add_argument('--max-meta-requests',type=int)
    prepare.add_argument('--max-gpu-seconds',type=int,default=0)
    prepare.add_argument('--consent-public-reference-transfer',action='store_true')
    commands.add_parser('esm-status',help='Inspect selected public backend configuration, without dispatch')
    for name in ('mcp-smoke','status','meta-smoke','meta-review','esm-score','esm-poll'):
        command=commands.add_parser(name)
        command.add_argument('--workspace',type=Path,required=True)
        if name in ('meta-smoke','meta-review'):
            command.add_argument('--live',action='store_true')
            command.add_argument('--ack-small-test',action='store_true')
        if name=='esm-score':
            command.add_argument('--approve-plan',action='store_true')
        if name=='esm-poll':
            command.add_argument('--task-id',required=True)
    score=commands.add_parser('score-local',help='CPU inference from explicitly installed pinned local weights')
    score.add_argument('--checkpoint-dir',type=Path,required=True)
    score.add_argument('--weights-sha256',required=True)
    score.add_argument('--tokenizer-sha256',required=True)
    score.add_argument('--positions',type=int,nargs='+',required=True)
    score.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='validate':
            profile=registered_profile()
            target=validate_target(profile,args.objective,reference_numbering=args.frame)
            if args.sequence is not None and normalize_sequence(args.sequence)!=target.reference_sequence:
                raise ValueError('Input sequence differs from registered reference; no crop or substitution')
            output={'status':'ok','target':target.summary(),'external_request_attempts':0}
            if args.variant:
                output['variant']=asdict(validate_variant(target,args.variant,reference_numbering=args.frame))
        elif args.command=='prepare':
            workspace=args.workspace.resolve()
            if workspace.exists():
                raise ValueError('Workspace already exists; use a fresh directory')
            target=validate_target(registered_profile(),args.objective)
            if (not args.positions or len(args.positions)>10 or len(set(args.positions))!=len(args.positions)
                    or any(not 32<=p<=212 or p in target.protected_positions for p in args.positions)
                    or not 0<=args.max_gpu_seconds<=900):
                raise ValueError('Invalid review position or GPU budget policy')
            from app.science.provider_config import load_esm_settings
            settings=load_esm_settings(ROOT/'.env')
            plan={**target.summary(),'objective_profile_id':target.objective_id,
                  'protected_positions':list(target.protected_positions),
                  'allowed_region':{'start_1based':32,'end_1based':212},
                  'requested_budget':{'usd_micros':args.usd_micros if args.usd_micros is not None else (200000 if args.review else 100000),
                     'max_meta_requests':args.max_meta_requests if args.max_meta_requests is not None else (4 if args.review else 2),
                     'max_gpu_seconds':args.max_gpu_seconds},
                  'consent_to_external_sequence_upload':args.consent_public_reference_transfer}
            if args.review:
                plan.update({'esm_model_key':args.model_key,'positions_1based':args.positions,
                    'model_pins':{args.model_key:{'expected_weights_sha256':settings['ESM_WEIGHTS_SHA256'],
                      'expected_tokenizer_sha256':settings['ESM_TOKENIZER_SHA256']}}})
            manifest=build_runtime_bundle(ROOT,workspace/'product')
            (workspace/'state').mkdir()
            runs=RunService(workspace/'state/runs.sqlite')
            run_id=runs.create(plan,'local')
            output={'status':'prepared','run_id':run_id,'owner_id':'local','reference_id':target.reference_id,
                    'bundle_sha256':manifest['bundle_sha256'],'os_sandbox_verified':False,
                    'external_request_attempts':0}
            (workspace/'launcher.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
        elif args.command=='esm-status':
            from app.science.provider_config import load_esm_settings
            from importlib.util import find_spec
            settings=load_esm_settings(ROOT/'.env')
            output={'status':'unconfigured','backend':settings['ESM_BACKEND'],'model_key':settings['ESM_MODEL_KEY'],
                    'modal_sdk_installed':find_spec('modal') is not None,
                    'remote_execution_approved':settings['ESM_REMOTE_EXECUTION_APPROVED'],
                    'modal_compatibility_verified':settings['MODAL_COMPATIBILITY_VERIFIED'],
                    'code':'runpod_explicitly_unconfigured' if settings['ESM_BACKEND']=='runpod' else 'verify_pinned_backend_before_execution',
                    'external_request_attempts':0}
        elif args.command=='score-local':
            from app.science.esm_engine import ESMEngine, LocalHFBackend
            from app.science.ranking import rank_candidates
            target=validate_target(registered_profile(),'sequence_plausibility_review')
            backend=LocalHFBackend(args.checkpoint_dir,expected_weights_sha256=args.weights_sha256,
                                   expected_tokenizer_sha256=args.tokenizer_sha256)
            artifact=ESMEngine(backend).score_positions(target,args.positions)
            artifact['ranked_candidates']=rank_candidates(artifact['rows'])
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x',encoding='utf-8') as handle:
                json.dump(artifact,handle,indent=2,allow_nan=False)
            output={'status':'ok','artifact':str(args.output.resolve()),'source_mode':artifact['source_mode'],
                    'candidate_count':len(artifact['rows']),'external_request_attempts':0}
        else:
            if args.command in ('meta-smoke','meta-review') and not (args.live and args.ack_small_test):
                raise ValueError('Explicit live approval flags --live --ack-small-test required; no secret read')
            workspace,data,runs=_load_workspace(args.workspace)
            if args.command=='status':
                output=runs.get(data['run_id'],data['owner_id'])
            elif args.command=='mcp-smoke':
                output=asyncio.run(_mcp_smoke(workspace,data))
                path=ArtifactStore(workspace/'artifacts',runs).save(data['run_id'],data['owner_id'],output)
                output={**output,'artifact_path':str(path)}
            elif args.command in ('esm-score','esm-poll'):
                from app.core.tool_executor import SessionContext
                from app.science.provider_config import load_esm_settings,make_inference_service
                context=SessionContext(workspace/'state/runs.sqlite',data['run_id'],data['owner_id'])
                settings=load_esm_settings(ROOT/'.env')
                service=make_inference_service(context,settings)
                if args.command=='esm-poll':
                    output=service.poll(context,args.task_id,timeout_seconds=0)
                else:
                    if not args.approve_plan:
                        raise ValueError('Trusted plan approval required')
                    state=runs.get(data['run_id'],data['owner_id'])
                    plan=state['input']
                    target=validate_target(registered_profile(),plan['objective_profile_id'])
                    request=service.request_for(target,plan['positions_1based'],plan['esm_model_key'])
                    runs.approve(data['run_id'],state['plan_digest'],state['budget_version'],data['owner_id'])
                    output=service.submit(context,request)
            else:
                state=runs.get(data['run_id'],data['owner_id'])
                runs.approve(data['run_id'],state['plan_digest'],state['budget_version'],data['owner_id'])
                proc=subprocess.run([sys.executable,'-m','app.host.runner','--db',str(workspace/'state/runs.sqlite'),
                    '--run-id',data['run_id'],'--owner-id',data['owner_id'],'--env-file',str(ROOT/'.env'),
                    '--artifacts',str(workspace/'artifacts'),'--workflow',
                    'sequence_review' if args.command=='meta-review' else 'validation_smoke',
                    '--live','--ack-small-test'],
                    cwd=workspace/'product',capture_output=True,text=True,
                    timeout=state['max_meta_requests']*50+30)
                if proc.returncode not in (0,2):
                    raise ValueError('Controlled host failed; inspect durable run status before any manual retry')
                output=json.loads(proc.stdout)
        print(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False))
        return 0 if output.get('status') not in {'blocked','partial','unconfigured','unknown'} else 2
    except (ValueError,OSError,KeyError,subprocess.TimeoutExpired):
        print(json.dumps({'status':'blocked','reason':
            'Explicit live approval flags required' if args.command in ('meta-smoke','meta-review') and not (args.live and args.ack_small_test)
            else 'Input, local prerequisite, workspace or policy check failed; no automatic retry'}))
        return 2

if __name__=='__main__':
    raise SystemExit(main())
