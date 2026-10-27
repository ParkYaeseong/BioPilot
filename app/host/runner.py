"""Launch the bounded Meta host from the provisioned workspace only."""
import argparse
import asyncio
import json
from pathlib import Path

from app.core.artifacts import ArtifactStore
from app.core.runs import RunService
from app.host.meta_client import MetaClient, MetaHost
from app.host.mcp_bridge import connect

async def run(args):
    if not args.live or not args.ack_small_test or not (Path.cwd()/'bundle_manifest.json').is_file():
        raise ValueError('Approved provisioned workspace required')
    runs=RunService(args.db)
    async with connect(Path.cwd(),args.db,args.run_id,args.owner_id,
                       esm_env_file=args.env_file if args.workflow=='sequence_review' else None) as bridge:
        report=await MetaHost(MetaClient(env_file=args.env_file,live=True),bridge,runs,
                              args.run_id,args.owner_id,source_mode='live',workflow=args.workflow).run()
        report['mcp_protocol_version']=bridge.protocol_version
        manifest=json.loads((Path.cwd()/'bundle_manifest.json').read_text(encoding='utf-8'))
        report['bundle_sha256']=manifest['bundle_sha256']
        report.pop('artifact_sha256',None)
        path=ArtifactStore(args.artifacts,runs).save(args.run_id,args.owner_id,report)
        return {**report,'artifact_path':str(path)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--owner-id',required=True)
    parser.add_argument('--env-file',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--ack-small-test',action='store_true')
    parser.add_argument('--workflow',choices=['validation_smoke','sequence_review'],default='validation_smoke')
    args=parser.parse_args()
    try:
        result=asyncio.run(run(args))
    except Exception:
        result={'status':'partial','stop_reason':'host_prerequisite_or_policy_failure','cost_status':'unknown'}
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
    return 0 if result.get('status') in {'validation_complete','sequence_review_complete'} else 2

if __name__=='__main__':
    raise SystemExit(main())
