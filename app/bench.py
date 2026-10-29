"""Unified local BioPilot workflow. Only explicit execution reaches bench_execution."""
import argparse
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.brand import BRAND_ICON
from app.bench_intake import freeze_input
from app.bench_store import ReviewStore
from app.bench_execution import execute_review, local_configuration
from app.core.targets import registered_profile
from app.guided_tour import stop_tour
from app.tour_spotlight import spotlight_document
from app.viewer import render_workbench, _style
from app.viewer_data import load_run_view
from app.viewer_render import init_appearance, appearance_control, render_brand
from app import new_review_tour

ROOT=Path(__file__).resolve().parents[1]


def _arguments():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',type=Path,default=ROOT/'.runtime/bench')
    parser.add_argument('--esm-env',type=Path,default=ROOT/'.cache/local_esm150_verified.env')
    parser.add_argument('--max-runs',type=int,default=3)
    parser.add_argument('--max-requests',type=int,choices=(3,4),default=4)
    parser.add_argument('--artifact',type=Path,default=ROOT/'demo/artifacts/sequence_review.replay.json')
    return parser.parse_known_args()[0]


def _revoke():
    st.session_state['bench_pending']=None
    st.session_state['bench_allow']=False
    st.session_state['bench_cost_ack']=False


def _route(route, review_id=None):
    if st.session_state.get('tour_active'):
        stop_tour(st.session_state)
    _revoke()
    st.session_state['bench_new_tour_active']=False
    st.session_state['bench_route']=route
    st.session_state['bench_record']=review_id
    st.session_state['active_view']='Overview'
    for key in ('compare_candidates','focused_candidate','structure_focus','trace_step','evidence_section'):
        st.session_state.pop(key,None)


def _sidebar(store):
    with st.sidebar:
        render_brand(subtitle='SCIENTIFIC REVIEW')
        st.button('New review',key='bench_new',type='primary',width='stretch',
                  icon=':material/add:',on_click=_route,args=('new',))
        st.markdown('**Recent reviews**')
        st.button('Example · Lipase A',key='bench_example',width='stretch',
                  on_click=_route,args=('result','example'))
        for row in store.recent()[:8]:
            text=row['request']['message']
            label=(text[:34]+'…' if len(text)>34 else text)+' · '+row['status'].upper()
            st.button(label,key='recent_'+row['id'],width='stretch',
                      on_click=_route,args=('record',row['id']))
        st.caption(f'Local execution allowance remaining: {store.remaining_runs}. Stored across refreshes.')
        st.caption('Full-reference 1-based · full_212 · S108 / D164 / H187 protected')
        appearance_control()


def _stages(status):
    active=0 if status in ('input','validated') else (1 if status in ('running','failed') else 2)
    labels=('Input & Validation','Agent Execution','Review Results')
    st.html('<ol class="review-stages" aria-label="Review workflow">'+''.join(
        f'<li class="{"current" if i==active else ""}"><span>{i+1}</span>{label}</li>'
        for i,label in enumerate(labels))+'</ol>')
    st.caption('Review status: '+status.upper())


def _configuration(options):
    try:
        return local_configuration(options.esm_env),None
    except (ValueError,OSError) as error:
        return None,str(error)


def _reuse_input(store,review_id):
    frozen=store.get(review_id)['request']
    fresh=store.create(frozen)
    _route('record',fresh['id'])


def _input_summary(request,store,options):
    first,second,third=st.columns(3)
    first.metric('Full-reference positions',', '.join(map(str,request['positions'])))
    second.metric('ESM checkpoint',request['model_key'])
    third.metric('Meta request cap',options.max_requests)
    st.caption(f"Input: {request['filename']} · full_212 · remaining runs: {store.remaining_runs}")
    st.info('Provider cost is unknown / unverified. The limits below are call limits, not a confirmed bill.')
    with st.expander('Input identity & hashes'):
        st.json({'input':request['filename'],'input_kind':request['input_kind'],
        'full_reference_positions':request['positions'],'reference_sha256':request['reference_sha256'],
        'uploaded_fasta_sha256':request['fasta_sha256'],'uploaded_structure_sha256':request['structure_sha256'],
        'checkpoint':request['model_key'],'sequence_context':'full_212',
        'remaining_local_runs':store.remaining_runs,'max_meta_requests':options.max_requests,
        'provider_cost':'unknown / unverified'},expanded=True)
    st.caption('Each position reviews all 19 non-WT substitutions under one ranking policy. Uploaded files stay local; only the registered public context enters the controlled workflow.')


def _confirmation(store,row,options):
    st.subheader('Confirm this review')
    request=row['request']
    st.text(request['message'])
    _input_summary(request,store,options)
    st.caption('Call/run limits are not a verified currency ceiling. Nothing has been sent by validation.')
    config,error=_configuration(options)
    if error:
        st.error(error)
    st.checkbox('Allow this review to call Meta and run local ESM',key='bench_allow')
    st.checkbox('I understand provider cost is unverified',key='bench_cost_ack')
    approved=st.session_state.get('bench_allow') and st.session_state.get('bench_cost_ack')
    if st.button('Execute approved review',key='bench_execute',type='primary',
        disabled=not (approved and config and config['model_key']==request['model_key'] and store.remaining_runs>0)):
        st.session_state['bench_pending']=None
        st.session_state['bench_record']=row['id']
        st.session_state['bench_route']='record'
        progress=st.empty()
        with progress.container():
            _stages('running')
        with st.status('Executing approved review · Meta → MCP → local ESM',expanded=True) as status:
            try:
                result=execute_review(store,row['id'],root=ROOT,esm_env=options.esm_env,
                    approved=True,max_requests=options.max_requests)
            except (ValueError,OSError) as error:
                st.error(str(error))
                return
            status.update(label='Review '+result['status'].upper(),
                          state='complete' if result['status']=='completed' else 'error')
        st.session_state['bench_reset_approval']=True
        if result['report_sha256']:
            st.session_state['bench_route']='result'
            st.session_state['active_view']='Overview'
        st.rerun()


def _new_review(store,options):
    with st.container(key='workspace_header'):
        heading,guide=st.columns([3,1],vertical_alignment='bottom')
        with heading:
            st.html('<div class="workspace-kicker">PUBLIC LIPASE A <span class="workspace-mode">NEW REQUEST</span></div>')
            st.title('New review')
        guide.button('Start guided demo',key='start_new_demo',type='secondary',width='stretch',
            icon=':material/help_outline:',on_click=new_review_tour.action,args=('start',))
    touring=st.session_state.get('bench_new_tour_active',False)
    pending=st.session_state.get('bench_pending')
    _stages('validated' if pending else 'input')
    if pending:
        st.success('Input validated locally. No model request has been sent.')
    st.caption('Choose your input, describe the variants, then validate before approving execution.')
    config,error=_configuration(options)
    model_key=config['model_key'] if config else 'esm150'
    with st.container(key='view_content'):
        source,request=st.columns([1,1.2])
        with source, st.container(key='bench_input_panel'):
            st.subheader('Protein input')
            kind=st.radio('Input source',('Registered example','Upload FASTA'),
                key='bench_input_kind',on_change=_revoke)
            fasta=None;filename=None
            if kind=='Upload FASTA':
                upload=st.file_uploader('Upload full-reference FASTA',type=['fasta','fa','faa','txt'],
                    key='bench_fasta',on_change=_revoke,max_upload_size=1)
                if upload is not None:
                    fasta=upload.getvalue();filename=upload.name
            else:
                st.caption('Public Lipase A · 212 residues · fixed full-reference numbering')
            sequence=registered_profile()['reference_sequence']
            st.download_button('Download example FASTA','>public_Lipase_A_full_212\n'+sequence+'\n',
                file_name='Lipase_A_full_212.fasta',mime='text/plain',key='bench_download_example')
            with st.expander('Optional reference structure'):
                structure=st.file_uploader('Public 1ISP mmCIF (optional)',type=['cif','mmcif'],
                    key='bench_cif',on_change=_revoke,max_upload_size=8)
                st.caption('Optional: exact pinned public 1ISP only. PDB conversion and arbitrary target registration are not supported. The existing verified reference is used when no file is supplied.')
        with request, st.container(key='bench_request_panel'):
            st.subheader('Review request')
            st.text_area('What would you like to review?',value='Review A32V for sequence plausibility.',
                key='bench_message',height=140,max_chars=800,on_change=_revoke)
            st.caption('Use full-reference positions, for example A32V or position 45. The current executable target is public Lipase A; another protein or the 181-residue mature sequence is refused.')
            st.caption('Checkpoint: '+model_key+' · local CPU. ESM preference is not T50, activity or experimental validation.')
            if st.button('Validate input',key='bench_validate',type='primary',disabled=touring):
                _revoke()
                try:
                    frozen=freeze_input(st.session_state['bench_message'],
                        input_kind='upload' if kind=='Upload FASTA' else 'example',
                        fasta=fasta,filename=filename,cif=structure.getvalue() if structure else None,
                        model_key=model_key)
                    row=store.create(frozen)
                    st.session_state['bench_pending']=row['id']
                    st.rerun()
                except (ValueError,OSError) as error:
                    st.error(str(error))
        pending=st.session_state.get('bench_pending')
        if pending and not touring:
            _confirmation(store,store.get(pending),options)
        if touring:
            new_review_tour.render_examples(_input_summary,store,options,model_key)
    guide_document=(new_review_tour.document(st.session_state['appearance'])
                    if touring else spotlight_document(None))
    components.html(guide_document,height=0,scrolling=False)


def _result(store,options,review_id):
    row=None
    if review_id and review_id!='example':
        row=store.get(review_id)
        path=store.report_path(review_id)
    else:
        path=options.artifact
    view=load_run_view(path)
    if row and not view['is_complete'] and not view['candidates']:
        st.title('Review stopped before results')
        _stages(row['status'])
        st.error('No candidate result is available. Stop reason: '+str(view['stop_reason'] or view['status']))
        st.caption('Existing records are preserved. Opening this review never retries execution.')
        st.button('New request from this input',key='bench_reuse',on_click=_reuse_input,args=(store,row['id']))
        with st.expander('Recorded stop details'):
            st.json({'run_id':view['run_id'],'status':view['status'],'stop_reason':view['stop_reason'],
                     'recorded_model':view['actual_model'],'meta_request_attempts':view['meta_request_attempts'],
                     'report_sha256':row['report_sha256'],'input':row['request']})
        return
    badge='EXAMPLE / REPLAY' if row is None else row['status'].upper()+' / RECORDED RESULT'
    if row:
        with st.expander('Execution record · '+row['status'].upper()):
            _stages(row['status'])
            st.caption('Result of the approved request: '+row['request']['message'])
            st.button('New request from this input',key='bench_reuse',
                on_click=_reuse_input,args=(store,row['id']),
                help='Creates a separate validated request. Previous execution is never retried; new approval is required.')
    render_workbench(view,show_sidebar=False,badge=badge)
    if row and st.session_state.get('active_view')=='Evidence':
        with st.expander('Input receipt for this review'):
            st.json({'review_id':row['id'],'input_digest':row['digest'],
                     'input':row['request'],'report_sha256':row['report_sha256']})


def _record(store,options,review_id):
    row=store.get(review_id)
    if row['report_sha256']:
        _result(store,options,review_id)
        return
    st.title('Review record')
    _stages(row['status'])
    if row['status']=='validated':
        st.info('This frozen input has not been executed. Inspect it before granting approval.')
        _confirmation(store,row,options)
    elif row['status']=='running':
        st.warning('Execution is running or its outcome is unconfirmed. This record cannot be executed again. Inspect the existing run before a deliberate new request.')
    else:
        st.error(row['error'] or 'Execution failed. No automatic retry.')
    with st.expander('Frozen input receipt'):
        st.json(row['request'])


def main():
    options=_arguments()
    st.set_page_config(page_title='BioPilot Bench',page_icon=BRAND_ICON,layout='wide',initial_sidebar_state='auto')
    init_appearance();_style(st.session_state['appearance'])
    if st.session_state.pop('bench_reset_approval',False):
        _revoke()
    store=ReviewStore(options.state_dir,max_runs=options.max_runs)
    st.session_state.setdefault('bench_route','result')
    st.session_state.setdefault('bench_record','example')
    _sidebar(store)
    try:
        route=st.session_state['bench_route']
        if route=='new':
            components.html(spotlight_document(None),height=0)
            _new_review(store,options)
        elif route=='record':
            _record(store,options,st.session_state['bench_record'])
        else:
            _result(store,options,st.session_state.get('bench_record'))
    except (ValueError,OSError) as error:
        st.error(str(error))


if __name__=='__main__':
    main()
