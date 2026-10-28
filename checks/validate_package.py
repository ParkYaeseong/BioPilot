#!/usr/bin/env python3
"""Validate offline package consistency, never scientific efficacy or live APIs."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit('Missing local checker dependency. Review requirements-checks.txt before installation.')

from science_contracts import verify_target
from hackathon_contracts import to_chat_tools, select_tools, validate_timeline, validate_bundle_paths, RUBRIC_WEIGHTS
from datetime import datetime
from zoneinfo import ZoneInfo
from package_files import package_files

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args=parser.parse_args();root=args.root.resolve();checks=[];failures=[]
    def check(name, condition):
        checks.append(name)
        if not condition:failures.append(name)
    def load(path):return json.loads((root/path).read_text(encoding='utf-8'))
    files=list(package_files(root))
    for p in files:
        rel=p.relative_to(root).as_posix()
        if p.suffix in {'.md','.txt','.json','.yaml','.mmd','.py','.fasta'} or p.name in {'.env.example','MANIFEST.sha256'}:
            text=p.read_text(encoding='utf-8');check('nonempty UTF-8 '+rel,bool(text.strip()))
            if p.suffix=='.md':check('balanced fences '+rel,len(re.findall(r'^```',text,re.M))%2==0)
            if p.suffix=='.py':ast.parse(text,filename=rel);check('Python parses '+rel,True)
            if p.suffix=='.json':json.loads(text);check('JSON parses '+rel,True)
    for p in (root/'schemas').glob('*.schema.json'):
        Draft202012Validator.check_schema(json.loads(p.read_text(encoding='utf-8')));check('valid JSON Schema '+p.name,True)
    for instance,schema in [
        ('run_input','run_input'),('lipase_run_input','run_input'),('plan_response','plan'),
        ('report_narrative','report_narrative'),('tool_result_blocked','tool_result')]:
        v=Draft202012Validator(load('schemas/'+schema+'.schema.json'))
        errors=list(v.iter_errors(load('examples/'+instance+'.json')))
        check('example '+instance,not errors)
        if errors:failures.extend(str(e) for e in errors)
    # Negative cases pin our public contract, not the provider's implementation.
    ri=load('examples/run_input.json');rs=Draft202012Validator(load('schemas/run_input.schema.json'))
    for field,value in [('reference_numbering','mature_1based'),('objective_profile_id','activity_optimization')]:
        changed=dict(ri);changed[field]=value;check('reject unsupported '+field,not rs.is_valid(changed))
    report=load('examples/report_narrative.json');rv=Draft202012Validator(load('schemas/report_narrative.schema.json'))
    invalid=dict(report);invalid['biological_efficacy_established']=True
    check('reject efficacy=true',not rv.is_valid(invalid))
    invalid=dict(report);invalid['ranking_scope']='measured_T50_prediction'
    check('reject fabricated calibrated rank',not rv.is_valid(invalid))
    cfg=yaml.safe_load((root/'config/development.yaml').read_text(encoding='utf-8'))
    for k in ['paid_execution_enabled','external_sequence_upload_enabled','public_write_demo_enabled']:
        check('default off '+k,cfg[k] is False)
    check('live Meta contract blocked',cfg['meta']['model'] is None and cfg['meta']['base_url'] is None and not cfg['meta']['provider_contract_verified'])
    check('coordinate features blocked',not cfg['science']['coordinate_features_enabled'])
    check('no WT hit claim default',not cfg['evaluation']['wt_improvement_metric_enabled'])
    check('optional fold disabled',not cfg['science']['fold_enabled'] and cfg['science']['max_structure_predictions']==0)
    check('runtime labels not mounted',cfg['runtime']['label_directory_mounted'] is False and cfg['runtime']['evaluator_directory_mounted'] is False)
    p=load('reference/target_profile.json');target=verify_target(p)
    check('target guard pass',target['protected_full_positions']==[108,164,187])
    for fn,seq in [('reference/lipase_full_212.fasta',p['reference_sequence']),('reference/1ISP_A_deposited_181.fasta',p['mature_sequence'])]:
        lines=(root/fn).read_text(encoding='utf-8').splitlines();actual=''.join(x for x in lines if not x.startswith('>'))
        check('FASTA/profile consistency '+fn,actual==seq)
    mapping=load('reference/residue_map.json')
    check('map length',len(mapping['mapping'])==len(p['reference_sequence']))
    for row in mapping['mapping']:
        i=row['full_position'];expected=i-31 if i>=32 else None
        check('sequence-map row '+str(i),row['residue']==p['reference_sequence'][i-1] and row['mature_position']==expected)
    unmodelled={row['full_position'] for row in p['structure']['missing_residue_ids']}
    for row in mapping['mapping']:
        i=row['full_position']
        if i<32:
            ok=all(row[k] is None for k in ['pdb_label_seq_id','pdb_auth_seq_id','pdb_insertion_code','coordinate_observed'])
        else:
            ok=(row['pdb_label_seq_id']==i-31 and row['pdb_auth_seq_id']==str(i-31)
                and row['pdb_insertion_code'] is None and row['coordinate_observed'] is (i not in unmodelled))
        check('coordinate-join row '+str(i),ok)
    check('index join registered',mapping['coordinate_index_join_verified'] is True)
    check('geometry still not claimed',mapping['geometry_validated'] is False and p['structure']['geometry_validated'] is False)
    check('coordinate source pinned to one file',mapping['coordinate_source']['sha256']==p['structure']['coordinate_file_sha256'] and len(mapping['coordinate_source']['sha256'])==64)
    check('unmodelled residues identified',sorted(unmodelled)==[32,212] and mapping['coordinate_source']['unmodelled_full_positions']==[32,212])
    check('no insertion codes or author offset',mapping['coordinate_source']['insertion_codes']==[] and mapping['coordinate_source']['auth_minus_label_offsets']==[0])
    ap=load('evaluation_private/assay_protocol.json')
    check('median not WT',ap['proteingym_binary_method']=='median' and ap['wild_type_t50'] is None)
    check('no real assay labels',ap['actual_candidate_measurements_included'] is False)
    recon=load('evaluation_private/dataset_reconciliation.json')
    check('counts not silently reconciled',recon['raw_library_reported_count']-recon['proteingym_metadata_reported_count']==recon['count_difference'] and recon['status']=='pending_row_level_audit')
    tools=load('schemas/tools.chat_completions.json')
    check('unique native tool names',len({t['function']['name'] for t in tools})==len(tools))
    prompt=(root/'prompts/runtime/00_developer.txt').read_text(encoding='utf-8')
    for phase in ['plan','execute','report']:
        d=load('examples/meta_'+phase+'_request.json')
        check('request model placeholder '+phase,d['model']=='__VERIFY_META_MODEL_ID__')
        dev=[m['content'] for m in d['messages'] if m['role']=='developer']
        check('canonical developer prompt '+phase,dev==[prompt])
        if phase!='execute':
            schema=load('schemas/'+('plan' if phase=='plan' else 'report_narrative')+'.schema.json')
            check('canonical schema '+phase,d['response_format']['json_schema']['schema']==schema)
            check('no tools in structured phase '+phase,not d.get('tools'))
    for pth in (root/'prompts/runtime').glob('*.txt'):
        text=pth.read_text(encoding='utf-8');check('no numeric assay cutoff in runtime '+pth.name,'46.34' not in text)
    sources=load('sources.json');ids=[s['id'] for s in sources]
    check('source IDs unique',len(ids)==len(set(ids)))
    for doc in (root/'docs').rglob('*.md'):
        for token in re.findall(r'\[(S[0-9]{2}(?:[^\]]*)?)\]',doc.read_text(encoding='utf-8')):
            for sid in re.findall(r'S[0-9]{2}',token):check('source resolves '+doc.name+' '+sid,sid in ids)
    prompts=list((root/'prompts').rglob('*.txt'))
    inventory=load('prompts/inventory.json')
    check('prompt inventory complete',sorted(p.relative_to(root).as_posix() for p in prompts)==sorted(inventory['paths']))
    mcp=load('schemas/tools.mcp.json')['tools']
    check('MCP/native catalog parity',to_chat_tools(mcp)==tools)
    filtered=select_tools(mcp,{t['name'] for t in mcp})
    check('default catalog excludes fold',not any(t['name']=='predict_structure' for t in filtered))
    check('default catalog verifier hidden',next(t for t in filtered if t['name']=='score_positions')['inputSchema']['properties']['model_key']['enum']==['esm150'])
    check('server guards required',cfg['mcp']['server_side_guards_required'] is True)
    check('remote MCP disabled',cfg['mcp']['remote_enabled'] is False)
    check('evaluator tools disabled',cfg['mcp']['evaluator_tools_enabled'] is False)
    check('live MCP not falsely claimed',cfg['mcp']['server_implemented'] is False and cfg['mcp']['compatibility_verified'] is False)
    hc=yaml.safe_load((root/'config/hackathon.yaml').read_text(encoding='utf-8'))
    check('captured rubric weights match contract',hc['rubric_weights']==RUBRIC_WEIGHTS)
    check('rubric sums to one',abs(sum(hc['rubric_weights'].values())-1)<1e-12)
    end=datetime.fromisoformat(hc['submission_deadline']['local'])
    check('deadline KST conversion',end.astimezone(ZoneInfo('Asia/Seoul')).isoformat()==hc['submission_deadline']['kst'])
    check('deadline New York zone',end.astimezone(ZoneInfo('America/New_York')).isoformat()==hc['submission_deadline']['local'])
    pools=hc['prizes_usd']
    check('prize pools reconcile',sum(pools['indie'])==400000 and sum(pools['startup'])==550000 and sum(pools['bonuses'].values())==50000)
    story=load('demo/storyboard.json')
    try:
        seconds=validate_timeline(story['segments'])
        check('recording plan within 180 seconds',seconds==story['target_duration_seconds']==hc['planned_video_seconds']==180)
    except (ValueError,KeyError,TypeError):check('recording plan within 180 seconds',False)
    bundle=load('config/runtime_bundle.allowlist.json')
    try:
        paths=validate_bundle_paths(bundle['sources'],set(bundle['sources']))
        check('runtime source allowlist guarded',all((root/p).is_file() for p in paths))
    except (ValueError,KeyError,TypeError):check('runtime source allowlist guarded',False)
    manifest_template=load('submission/manifest.template.json')
    check('submission not falsely claimed',manifest_template['status']=='not_submitted' and manifest_template['submission_receipt'] is None)
    evidence_matrix=load('submission/evidence_matrix.json')
    check('judge evidence not falsely completed',all(x['verified'] is False and x['artifact'] is None for x in evidence_matrix['rows']))
    check('judge matrix rubric parity',{x['criterion']:x['weight'] for x in evidence_matrix['rows']}==hc['rubric_weights'])
    check('video not falsely verified',cfg['demo']['actual_video_verified'] is False and cfg['demo']['actual_video_path'] is None)
    rule_snapshot=load('compliance/rules_snapshot.json')
    check('rules capture accurately scoped',rule_snapshot['fresh_authenticated_retrieval'] is False)
    for rp in (root/'prompts/runtime').glob('*.txt'):
        check('runtime no numeric outcome cutoff '+rp.name,'46.34' not in rp.read_text(encoding='utf-8'))

    # Optional manifest verification allows validation before packaging and after unpacking.
    manifest=root/'MANIFEST.sha256'
    if manifest.exists():
        covered=set()
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest,rel=line.split('  ',1);f=(root/rel).resolve()
            check('safe manifest path '+rel,root in f.parents)
            check('manifest hash '+rel,f.exists() and hashlib.sha256(f.read_bytes()).hexdigest()==digest)
            covered.add(rel)
        actual={p.relative_to(root).as_posix() for p in files if p.name!='MANIFEST.sha256'}
        check('manifest complete',actual==covered)
    result={'status':'PASS' if not failures else 'FAIL','check_count':len(checks),'failed_count':len(failures),
            'prompt_count':len(prompts),'scope':'offline package/science/MCP-catalog/rubric/recording-plan consistency; no live app, transport, model efficacy or video verification',
            'failures':failures}
    print(json.dumps(result,indent=2))
    return int(bool(failures))

if __name__=='__main__':raise SystemExit(main())
