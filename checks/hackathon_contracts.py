"""Offline helpers for the v3 design pack, not a running MCP server or live judge.

The product must explicitly integrate equivalent guards at its trust boundary.
No function here contacts a provider, runs ESM, evaluates labels, or submits an entry.
"""
from __future__ import annotations
from copy import deepcopy
import math
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

TOOL_ALLOWLIST=frozenset({
    'validate_target_context','retrieve_atlas_evidence','score_positions',
    'fetch_atlas_structure','predict_structure','get_run_status',
})
RUBRIC_WEIGHTS={'impact':0.30,'meta_tooling':0.25,'technical_execution':0.20,'demo':0.25}


def select_tools(catalog: Iterable[Mapping[str, Any]], available: set[str], *,
                 fold_enabled: bool=False, verifier_enabled: bool=False) -> list[dict[str, Any]]:
    """Filter an already trusted MCP catalog; flags do not grant execution permission."""
    rows=[deepcopy(dict(x)) for x in catalog]
    names=[r.get('name') for r in rows]
    if any(not isinstance(n,str) or n not in TOOL_ALLOWLIST for n in names):
        raise ValueError('Untrusted or evaluator tool in product catalog')
    if len(names)!=len(set(names)):
        raise ValueError('Duplicate tool name')
    if not set(available)<=set(names):
        raise ValueError('Requested unavailable tool')
    result=[]
    for row in rows:
        name=row['name']
        if name not in available or (name=='predict_structure' and not fold_enabled):
            continue
        schema=row.get('inputSchema')
        if not isinstance(schema,dict) or schema.get('type')!='object':
            raise ValueError('Missing object input schema')
        if name=='score_positions' and not verifier_enabled:
            schema['properties']['model_key']['enum']=['esm150']
        result.append(row)
    return result


def to_chat_tools(catalog: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Translate a pre-filtered MCP catalog to a proposed Chat function catalog.

    Provider schema support must still be tested; this is not MCP transport code.
    """
    output=[];seen=set()
    for row in catalog:
        name=row.get('name')
        if name not in TOOL_ALLOWLIST or name in seen:
            raise ValueError('Unknown or duplicate tool')
        seen.add(name)
        output.append({'type':'function','function':{
            'name':name,'description':row['description'],'strict':True,
            'parameters':deepcopy(row['inputSchema'])}})
    return output


def weighted_score(scores: Mapping[str, float]) -> float:
    """Local self-review only. These weights do not predict the judges' decisions."""
    if set(scores)!=set(RUBRIC_WEIGHTS):
        raise ValueError('Every rubric category must have exactly one score')
    for value in scores.values():
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=10:
            raise ValueError('Each category must be a finite number from 0 to 10')
    return sum(scores[key]*weight for key,weight in RUBRIC_WEIGHTS.items())


def validate_timeline(segments: Iterable[Mapping[str, int]], max_seconds: int=180) -> int:
    """Check a recording plan; this does not inspect or certify a video file."""
    end=0;seen=False
    for segment in segments:
        start,stop=segment['start_s'],segment['end_s']
        if type(start) is not int or type(stop) is not int or start!=end or stop<=start:
            raise ValueError('Timeline must start at zero and be positive and contiguous')
        end=stop;seen=True
    if not seen or end>max_seconds:
        raise ValueError('Empty or overlong recording timeline')
    return end


def validate_bundle_paths(paths: Iterable[str], allowlist: set[str]) -> list[str]:
    """Validate relative source names only. A real bundler must also resolve symlinks.

    Restrict to the intended runtime roots even if an allowlist is misconfigured.
    This cannot detect mislabeled contents: review and hash every allowed source.
    """
    result=[];seen=set()
    for name in paths:
        if not isinstance(name,str) or not name or '\\' in name or ':' in name:
            raise ValueError('Use safe relative POSIX paths')
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or name!=path.as_posix():
            raise ValueError('Unsafe or noncanonical runtime path')
        trusted_root=bool(path.parts) and (path.parts[0]=='reference' or path.parts[:2]==('prompts','runtime'))
        if not trusted_root or name not in allowlist or name in seen:
            raise ValueError('Unapproved, evaluator-bearing or duplicate runtime path')
        seen.add(name);result.append(name)
    return result


def evidence_badge(source_mode: str) -> str:
    badges={
        'live':'LIVE - current execution',
        'imported_snapshot':'IMPORTED SNAPSHOT - source-captured data',
        'replay':'REPLAY - previously recorded real execution',
        'synthetic_fixture':'SYNTHETIC FIXTURE - not scientific evidence',
    }
    if source_mode not in badges:raise ValueError('Unknown source mode')
    return badges[source_mode]
