"""Read-only entry for the previous New Review bookmark."""
import streamlit as st
from app.brand import BRAND_ICON
from app.viewer import _style
from app.viewer_render import init_appearance

st.set_page_config(page_title='BioPilot Bench',page_icon=BRAND_ICON,layout='centered')
init_appearance();_style(st.session_state['appearance'])
st.title('One workspace for every review')
st.write('Input, execution, results and recent reviews are now together in BioPilot Bench.')
appearance=st.session_state['appearance']
st.link_button('Open BioPilot Bench','http://127.0.0.1:8522/?appearance='+appearance,
               type='primary',width='stretch')
st.caption('This page performs no model or GPU calls.')
