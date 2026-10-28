"""Operator CLI for one pinned optional prediction; never a product shell tool.

Examples and provisioning requirements: docs/OPTIONAL_SCIENCE_KO.md.
No command provisions GPUs, downloads weights, or changes account settings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from app.science.optional_science import StructureRequest, optional_capabilities, run_structure


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--model', choices=['esm3', 'esmfold2'], required=True)
    prepare.add_argument('--variant', default='WT')
    prepare.add_argument('--output', type=Path, required=True)
    for command in ('run', '_execute'):
        run = sub.add_parser(command)
        run.add_argument('--request', type=Path, required=True)
        run.add_argument('--request-sha256', required=True)
        run.add_argument('--checkpoint-dir', type=Path, required=True)
        run.add_argument('--manifest', type=Path, required=True)
        run.add_argument('--manifest-sha256', required=True)
        run.add_argument('--output-dir', type=Path, required=True)
        run.add_argument('--execution-approved', action='store_true')
        run.add_argument('--timeout-seconds', type=int, default=300)
    atlas = sub.add_parser('atlas-reference')
    atlas.add_argument('--external-read-approved', action='store_true')
    atlas.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'status':
        print(json.dumps(optional_capabilities(), indent=2))
        return 0
    if args.command == 'prepare':
        request = StructureRequest(args.model, args.variant)
        raw = json.dumps(request.to_payload(), indent=2).encode('utf-8')
        with args.output.open('xb') as stream:
            stream.write(raw)
        print(json.dumps({'status': 'prepared_not_executed',
                          'request_sha256': hashlib.sha256(raw).hexdigest()}))
        return 0
    if args.command == 'atlas-reference':
        # Reserve immutable destination before a network request can happen.
        with args.output.open('x', encoding='utf-8') as stream:
            from app.science.atlas_context import AtlasContextClient
            result = AtlasContextClient(read_approved=args.external_read_approved).lookup_reference()
            json.dump(result, stream, indent=2, allow_nan=False)
        print(json.dumps({'status': result['status'], 'reason': result.get('reason'),
                          'provider': result['provider']}))
        return 0 if result['status'] == 'available' else 2
    if args.execution_approved is not True:
        parser.error('--execution-approved is required; no model was loaded')
    if not 1 <= args.timeout_seconds <= 900:
        parser.error('--timeout-seconds must be 1..900')
    raw = args.request.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.request_sha256:
        parser.error('Request SHA256 mismatch')
    request = StructureRequest.from_payload(json.loads(raw))
    if args.output_dir.exists():
        parser.error('Output directory exists; prior predictions are preserved')
    if args.command == '_execute':
        receipt = run_structure(request, args.checkpoint_dir, args.manifest,
                                args.manifest_sha256, args.output_dir, execution_approved=True)
        print(json.dumps({'status': receipt['status'], 'structure_sha256': receipt['structure_sha256']}))
        return 0
    command = [sys.executable, '-m', 'app.science.optional_worker', '_execute',
        '--request', str(args.request.resolve()), '--request-sha256', args.request_sha256,
        '--checkpoint-dir', str(args.checkpoint_dir.resolve()),
        '--manifest', str(args.manifest.resolve()), '--manifest-sha256', args.manifest_sha256,
        '--output-dir', str(args.output_dir.resolve()), '--execution-approved',
        '--timeout-seconds', str(args.timeout_seconds)]
    try:
        result = subprocess.run(command, timeout=args.timeout_seconds, check=False)
        return result.returncode
    except subprocess.TimeoutExpired:
        # subprocess.run kills/reaps the single worker. No retries or fallback.
        args.output_dir.mkdir(exist_ok=True)
        with (args.output_dir / 'timeout.json').open('x', encoding='utf-8') as stream:
            json.dump({'status': 'timeout', 'scientific_evidence': False,
                       'wall_timeout_seconds': args.timeout_seconds,
                       'request': request.to_payload()}, stream)
        print(json.dumps({'status': 'timeout', 'scientific_evidence': False}))
        return 124


if __name__ == '__main__':
    raise SystemExit(main())
