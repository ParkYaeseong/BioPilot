"""Server-owned tool boundary shared by MCP and direct invocations.

The caller supplies tool arguments, never ownership, approval or registry policy.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from app.core.runs import RunService
from app.core.targets import registered_profile, validate_target
from app.core.atlas_snapshot import load_registered_atlas_snapshot, atlas_tool_result

@dataclass(frozen=True)
class SessionContext:
    db_path: Path
    run_id: str
    owner_id: str

class ToolExecutor:
    def __init__(self, context, engine=None, *, inference_service=None, backend_status=None):
        self.context = context
        self.engine = engine
        self.inference_service = inference_service
        self.backend_status = backend_status or {'status':'unconfigured','backend':None}
        self.runs = RunService(context.db_path)
        path = Path(__file__).resolve().parents[2] / 'schemas' / 'tools.mcp.json'
        self._catalog = {tool['name']: tool for tool in json.loads(path.read_text(encoding='utf-8'))['tools']}

    def _checked_run(self):
        run = self.runs.get(self.context.run_id, self.context.owner_id)
        data = run['input']
        objective = data.get('objective_profile_id', data.get('objective_id', 'sequence_plausibility_review'))
        target = validate_target(registered_profile(), objective,
                                 reference_numbering=data.get('reference_numbering'))
        if data.get('reference_id') != target.reference_id:
            raise ValueError('Run reference is not registered')
        return run, target

    def list_tools(self):
        names = ['validate_target_context', 'get_run_status']
        try:
            load_registered_atlas_snapshot()
            names.append('retrieve_atlas_evidence')
        except (ValueError, OSError, TypeError, KeyError):
            pass
        if self.inference_service is not None and self.inference_service.model_pins:
            try:
                self.inference_service.ensure_ready()
                names.append('score_positions')
            except ValueError:
                pass
        result = [deepcopy(self._catalog[name]) for name in names]
        for tool in result:
            if tool['name']=='score_positions':
                allowed = [key for key in tool['inputSchema']['properties']['model_key']['enum']
                           if key in self.inference_service.model_pins]
                tool['inputSchema']['properties']['model_key']['enum'] = allowed
        return result

    def dispatch(self, tool_name, arguments, call_id='local'):
        allowed = {tool['name'] for tool in self.list_tools()}
        if tool_name not in allowed:
            return {'status': 'blocked', 'code': 'unknown_or_disabled_tool'}
        if not isinstance(arguments, dict):
            return {'status': 'blocked', 'code': 'invalid_arguments'}
        schema = self._catalog[tool_name]['inputSchema']
        if not Draft202012Validator(schema).is_valid(arguments):
            return {'status': 'blocked', 'code': 'schema_validation_failed'}
        try:
            run, target = self._checked_run()
        except (ValueError, PermissionError, LookupError, KeyError, TypeError):
            return {'status': 'blocked', 'code': 'invalid_session_or_target'}
        if tool_name == 'validate_target_context':
            if arguments['reference_id'] != target.reference_id:
                return {'status': 'blocked', 'code': 'unregistered_reference'}
            return {'status': 'ok', 'target': target.summary(),
                    'source_mode': 'imported_snapshot',
                    'limitations': 'Sequence mapping only; ESM is not a T50 predictor; retained activity is unverified.'}
        if tool_name == 'score_positions':
            if arguments['reference_id'] != target.reference_id:
                return {'status':'blocked','code':'unregistered_reference'}
            try:
                request = self.inference_service.request_for(target,arguments['positions_1based'],arguments['model_key'])
                return self.inference_service.submit(self.context,request)
            except (ValueError,PermissionError):
                return {'status':'blocked','code':'inference_policy_rejected'}
        if tool_name == 'retrieve_atlas_evidence':
            if arguments['reference_id'] != target.reference_id:
                return {'status': 'blocked', 'code': 'unregistered_reference'}
            try:
                return atlas_tool_result(load_registered_atlas_snapshot(), arguments['max_hits'])
            except (ValueError, OSError, TypeError, KeyError):
                return {'status': 'unavailable', 'code': 'atlas_snapshot_unavailable',
                        'scientific_evidence': False}
        # Return a bounded allowlist, not the entire private storage row/input.
        result = {key: run.get(key) for key in ('run_id', 'state', 'budget_version',
                  'usd_micros', 'max_meta_requests', 'meta_requests_reserved',
                  'committed_micros', 'actual_cost_micros', 'cost_status',
                  'budget_conflict', 'cancellation_requested')}
        return {'status': 'ok', 'run': result,
                'capabilities': {'esm': any(tool['name']=='score_positions' for tool in self.list_tools()),
                                 'atlas': any(tool['name']=='retrieve_atlas_evidence' for tool in self.list_tools()),
                                 'coordinates': False, 'fold': False},
                'esm_backend': self.backend_status,
                'inference_jobs': self.inference_service.list_status(self.context) if self.inference_service is not None else [],
                'source_mode': 'live_local_state'}
