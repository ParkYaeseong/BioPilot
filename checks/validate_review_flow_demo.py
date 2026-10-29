"""Validate the current bilingual recording plan against offline UI/guard evidence.

This verifies planned timing and captions, not an exported video or measured voice.
No model dispatch, provider client or GPU operation is performed.
"""
from pathlib import Path
import json, re, sys, hashlib
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from app.viewer import VIEWS
from app.review_flow import prepare_review
from app.viewer_data import load_run_view
from app.viewer_structure import residue_selection, verify_reference

data=json.loads((root/'demo/review_flows_180s.json').read_text(encoding='utf-8'))
segments=data['segments'];previous=0
assert len(segments)==9
for segment in segments:
    assert segment['start_s']==previous
    assert segment['end_s']>segment['start_s']
    assert len(segment['en'])==len(segment['ko'])
    previous=segment['end_s']
assert previous==180==data['target_duration_seconds']
assert VIEWS==('Overview','Candidates','Structure','Agent Trace','Evidence')
assert prepare_review('Review A32V for sequence plausibility.','esm150')['positions']==[32]
try:
    prepare_review('Review S108A for sequence plausibility.','esm150')
    raise AssertionError('Protected-site script would not match the current guard')
except ValueError as error:
    assert 'Protected catalytic site' in str(error)
view=load_run_view(root/'demo/artifacts/sequence_review.replay.json')
assert view['candidate_count']==19 and view['actual_model']=='muse-spark-1.3'
assert residue_selection(32)['selection'] is None
assert residue_selection(108)['pdb_auth_seq_id']=='77'
assert verify_reference()['status']=='verified_index_join'

def ms(text):
    hours,minutes,seconds,millis=map(int,re.split('[:,]',text))
    return ((hours*60+minutes)*60+seconds)*1000+millis

subtitles={}
for language in ('en','ko'):
    path=root/f'demo/REVIEW_FLOWS_180S_{language.upper()}.srt'
    blocks=path.read_text(encoding='utf-8').strip().split('\n\n')
    previous=0;strings=[];durations=[]
    for index,block in enumerate(blocks,1):
        lines=block.splitlines()
        assert lines[0]==str(index)
        start,end=map(ms,lines[1].split(' --> '))
        assert start==previous and end>start
        assert end-start>=1200, 'Caption is too brief for this planned demo'
        assert 1<=len(lines[2:])<=2
        assert max(map(len,lines[2:]))<=(44 if language=='en' else 30)
        strings.extend(lines[2:]);durations.append(end-start);previous=end
    assert previous==180000
    expected=' '.join(sentence for s in segments for sentence in s[language])
    assert ' '.join(' '.join(strings).split())==' '.join(expected.split())
    subtitles[language]={'cues':len(blocks),'start_ms':0,'end_ms':previous,
        'overlap_or_gap_count':0,'max_lines_per_cue':2,'shortest_cue_ms':min(durations),
        'text_matches_narration':True}

paths=['demo/review_flows_180s.json','demo/REVIEW_FLOWS_180S_EN.md','demo/REVIEW_FLOWS_180S_KO.md',
       'demo/REVIEW_FLOWS_180S_EN.srt','demo/REVIEW_FLOWS_180S_KO.srt']
report={'date_kst':'2026-10-29','status':'PASS','scope':'offline recording-plan/caption/current-UI consistency; not rendered video or measured narration',
    'timeline_seconds':180,'segments':9,'english_words':data['english_word_count'],
    'subtitles':subtitles,'ui_and_reference_checks':['five unnumbered Saved Review views','A32V local validation','S108A local refusal',
        '19saved candidates','actual saved Meta model','A32 atom absence','S108 author77','pinned public reference join'],
    'new_provider_calls':0,'new_gpu_calls':0,'video_exported':False,'voice_duration_measured':False,
    'existing_test_fixtures_used_as_live_evidence':False,
    'files':[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths]}
(root/'validation/review_flow_demo_script_20261029.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({key:report[key] for key in ('status','scope','timeline_seconds','segments','english_words','subtitles')},indent=2))
