from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


def bench(monkeypatch,tmp_path):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr('sys.argv',['bench.py','--state-dir',str(tmp_path/'journal')])
    monkeypatch.setattr('app.bench_execution.local_configuration',lambda *_:{
        'backend':'local','device':'cpu','model_key':'esm150','pins_checked_during_execution':True})
    return AppTest.from_file(str(ROOT/'app/bench.py'),default_timeout=60).run()


def test_one_app_has_new_review_recent_records_and_the_same_results(monkeypatch,tmp_path):
    app=bench(monkeypatch,tmp_path)
    assert not app.exception
    assert app.button(key='bench_new')
    assert not any('Live session' in str(x.value) for x in app.markdown)
    assert app.session_state['active_view']=='Overview'
    app.button(key='bench_new').click().run()
    assert not app.exception
    assert app.text_area(key='bench_message')
    assert app.radio(key='bench_input_kind')
    assert app.button(key='bench_validate')
    app.radio(key='bench_input_kind').set_value('Upload FASTA').run()
    assert app.get('file_uploader')[0].key=='bench_fasta'


def test_validation_and_navigation_never_execute_and_edit_revokes_confirmation(monkeypatch,tmp_path):
    def forbidden(*args,**kwargs):
        pytest.fail('Navigation or preparation dispatched a run')
    monkeypatch.setattr('app.session_exec.run_session',forbidden)
    app=bench(monkeypatch,tmp_path)
    app.button(key='bench_new').click().run()
    app.text_area(key='bench_message').set_value('Review S108A').run()
    app.button(key='bench_validate').click().run()
    assert any('Protected catalytic site' in x.value for x in app.error)
    app.text_area(key='bench_message').set_value('Review A32V').run()
    app.button(key='bench_validate').click().run()
    assert app.session_state['bench_pending']
    assert app.button(key='bench_execute').disabled
    app.checkbox(key='bench_allow').check().run()
    app.checkbox(key='bench_cost_ack').check().run()
    assert not app.button(key='bench_execute').disabled
    app.text_area(key='bench_message').set_value('Review position 45').run()
    assert app.session_state.get('bench_pending') is None
    try:
        permission=app.session_state['bench_allow']
    except KeyError:
        permission=False
    assert permission is False
    app.button(key='bench_example').click().run()
    assert app.session_state['active_view']=='Overview'


def test_mocked_execution_is_saved_once_and_opens_same_result_views(monkeypatch,tmp_path):
    import json
    calls=[]
    def mocked(*args,**kwargs):
        calls.append(kwargs)
        record=json.loads((ROOT/'demo/artifacts/sequence_review.replay.json').read_text())
        record['source_mode']='synthetic_fixture'
        record['esm_source_mode']='synthetic_fixture'
        return {'returncode':0,'stage':'review','stdout':json.dumps(record),'stderr':''}
    monkeypatch.setattr('app.session_exec.run_session',mocked)
    app=bench(monkeypatch,tmp_path)
    app.button(key='bench_new').click().run()
    app.button(key='bench_validate').click().run()
    app.checkbox(key='bench_allow').check().run()
    app.checkbox(key='bench_cost_ack').check().run()
    app.button(key='bench_execute').click().run()
    assert not app.exception
    assert len(calls)==1
    assert app.session_state['bench_route']=='result'
    assert app.session_state['active_view']=='Overview'
    app.session_state['active_view']='Structure'
    app.run()
    app.run()
    assert len(calls)==1
    assert any('synthetic' in x.value.lower() for x in app.warning)
    old=app.session_state['bench_record']
    app.button(key='bench_reuse').click().run()
    assert not app.exception
    assert app.session_state['bench_record']!=old
    assert app.session_state['bench_route']=='record'
    assert app.button(key='bench_execute').disabled
    assert len(calls)==1


def test_new_review_tutorial_drives_local_examples_without_dispatch_or_overwriting_draft(monkeypatch,tmp_path):
    def forbidden(*args,**kwargs):
        pytest.fail('The tutorial attempted execution')
    monkeypatch.setattr('app.session_exec.run_session',forbidden)
    app=bench(monkeypatch,tmp_path)
    app.button(key='bench_new').click().run()
    app.text_area(key='bench_message').set_value('Review position 45').run()
    app.button(key='start_new_demo').click().run()
    assert app.session_state['bench_new_tour_active'] is True
    assert app.session_state['bench_new_tour_step']==0
    for expected in range(1,5):
        app.button(key='new_tour_next').click().run()
        assert not app.exception
        assert app.session_state['bench_new_tour_step']==expected
        assert app.text_area(key='bench_message').value=='Review position 45'
    assert any('Protected catalytic site' in x.value for x in app.error)
    assert app.button(key='new_tour_execute_preview').disabled
    app.button(key='new_tour_exit').click().run()
    assert app.session_state['bench_new_tour_active'] is False
    assert app.text_area(key='bench_message').value=='Review position 45'
    from app.bench_store import ReviewStore
    assert ReviewStore(tmp_path/'journal').recent()==[]
