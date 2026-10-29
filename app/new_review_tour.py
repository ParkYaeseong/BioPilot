"""New-input spotlight: real local checks, no dispatch or durable review creation."""
import base64
import json
from pathlib import Path
import streamlit as st

from app.bench_intake import freeze_input
from app.review_flow import prepare_review

STEPS=(
    ('Choose your protein input','.st-key-bench_input_panel',
     'Use the registered public example or upload its full-reference FASTA. Optional mmCIF must match the pinned reference.',
     'Your files stay local. This guide does not replace your input or draft.','new_input'),
    ('Describe the variants','.st-key-bench_request_panel',
     'Write a variant such as A32V or a full-reference position. Validate input checks the declared request before any execution.',
     'The current executable target is public Lipase A, using the complete 212-residue reference.','new_request'),
    ('See the real guard refuse S108A','.st-key-new_tour_guard',
     'The guide runs the same local preparation guard on a separate S108A example. The actual refusal is shown here.',
     'This is a local code check, not a Meta decision. Your draft remains unchanged.','new_guard'),
    ('Inspect a valid example','.st-key-new_tour_preflight',
     'A separate registered A32V example passes local validation. Inspect its position, checkpoint and bounded request allowance.',
     'This preview creates no review record and sends no model request.','new_preflight'),
    ('Execute only after explicit approval','.st-key-new_tour_approval',
     'A real request needs execution permission, cost acknowledgment and an explicit Execute click. Tutorial controls cannot grant those approvals.',
     'Finish the guide, validate your own input, then choose whether to execute. Returned results appear here and in Recent reviews.','new_execute'),
)


def action(name):
    if name=='start':
        st.session_state['bench_new_tour_active']=True
        st.session_state['bench_new_tour_step']=0
        st.session_state['bench_allow']=False
        st.session_state['bench_cost_ack']=False
    elif name=='exit':
        st.session_state['bench_new_tour_active']=False
    else:
        delta=1 if name=='next' else -1
        st.session_state['bench_new_tour_step']=max(0,min(len(STEPS)-1,st.session_state.get('bench_new_tour_step',0)+delta))


def render_examples(summary,store,options,model_key):
    step=st.session_state.get('bench_new_tour_step',0)
    if step>=2:
        with st.container(key='new_tour_guard',border=True):
            st.caption('LOCAL TUTORIAL EXAMPLE · S108A · no model call')
            try:
                prepare_review('Review S108A',model_key)
            except ValueError as error:
                st.error(str(error))
    if step>=3:
        with st.container(key='new_tour_preflight',border=True):
            st.caption('LOCAL TUTORIAL EXAMPLE · A32V · separate from your request')
            sample=freeze_input('Review A32V for sequence plausibility.',input_kind='example',model_key=model_key)
            st.success('Example input validated locally; nothing executed or saved as a review.')
            summary(sample,store,options)
    if step>=4:
        with st.container(key='new_tour_approval',border=True):
            st.caption('TUTORIAL PREVIEW · execution stays disabled')
            st.checkbox('Allow Meta and local ESM (tutorial preview)',value=False,disabled=True,key='new_tour_allow_preview')
            st.checkbox('Acknowledge unverified cost (tutorial preview)',value=False,disabled=True,key='new_tour_cost_preview')
            st.button('Execute approved review',key='new_tour_execute_preview',disabled=True)
    with st.container(key='new_tour_controls'):
        st.caption(f'New Review guide · {step+1} / {len(STEPS)} · no execution')
        previous,next_step,close=st.columns(3)
        previous.button('Back',key='new_tour_back',disabled=step==0,on_click=action,args=('back',))
        next_step.button('Next',key='new_tour_next',disabled=step==len(STEPS)-1,on_click=action,args=('next',))
        close.button('Exit',key='new_tour_exit',on_click=action,args=('exit',))


def document(appearance):
    index=st.session_state.get('bench_new_tour_step',0)
    title,selector,body,tip,picture_name=STEPS[index]
    assets=Path(__file__).parent/'assets/tour'
    picture=assets/(picture_name+'.png')
    payload={'index':index,'count':len(STEPS),'selector':selector,'title':title,'body':body,'tip':tip,
        'picture':'data:image/png;base64,'+base64.b64encode(picture.read_bytes()).decode() if picture.is_file() else None,
        'structure_preview':True,
        'light':appearance=='Light','auto':appearance=='Auto','playing':False,'allow_autoplay':False,
        'footer':'LOCAL GUIDE · separate examples · no API or GPU calls',
        'actions':{'tour_next':'new_tour_next','tour_back':'new_tour_back','exit_demo':'new_tour_exit'},
        'focus_height':None}
    script=(Path(__file__).parent/'tour_spotlight.js').read_text(encoding='utf-8')
    return '<script>const tourData='+json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')+';\n'+script+'</script>'
