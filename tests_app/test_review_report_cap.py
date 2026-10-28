"""The reserved sequence-review report may use its own explicit 1024-token cap.

Tool-stage requests keep the verified 512-token contract. Nothing here is real
Meta evidence; every response is a synthetic fixture.
"""
import asyncio
import json

import pytest

from app.host.meta_client import MAX_OUTPUT_TOKENS, REPORT_TOKEN_CAP, MetaHost
from tests_app.test_meta_loop import Client, ReviewBridge, response, score_tool, setup_review, tool


class WideClient(Client):
    """A fixture client explicitly built for the 1024-token report cap."""
    max_output_tokens=REPORT_TOKEN_CAP


def test_report_cap_constant_is_separate_from_the_tool_stage_contract():
    assert MAX_OUTPUT_TOKENS==512
    assert REPORT_TOKEN_CAP==1024


def test_only_the_reserved_final_report_uses_the_wider_cap(tmp_path):
    client=WideClient([response(call=[tool()]),response(call=[score_tool()]),
                       response(text='Sequence preferences only; T50 and activity remain unknown.')])
    host,runs,rid,bridge=setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    result=asyncio.run(host.run())
    assert result['status']=='sequence_review_complete'
    assert result['meta_request_attempts']==3
    assert [payload['max_completion_tokens'] for payload in client.payloads]==[
        MAX_OUTPUT_TOKENS,MAX_OUTPUT_TOKENS,REPORT_TOKEN_CAP]
    assert client.payloads[2].get('tools') is None
    assert result['final_report_max_tokens']==REPORT_TOKEN_CAP


def test_default_sequence_review_still_sends_the_unchanged512_contract(tmp_path):
    client=Client([response(call=[tool()]),response(call=[score_tool()]),
                   response(text='Sequence preferences only; T50 and activity remain unknown.')])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='sequence_review_complete'
    assert {payload['max_completion_tokens'] for payload in client.payloads}=={MAX_OUTPUT_TOKENS}
    assert result['final_report_max_tokens']==MAX_OUTPUT_TOKENS


def test_a_wider_report_cap_is_refused_when_the_client_cannot_send_it(tmp_path):
    """No silent downgrade to 512: an incapable client must fail loudly."""
    client=Client([])
    with pytest.raises(ValueError,match='cap|client|report'):
        setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    assert client.payloads==[]


@pytest.mark.parametrize('invalid',[256,513,2048,0,True])
def test_only_the_two_reviewed_report_caps_are_accepted(tmp_path,invalid):
    with pytest.raises(ValueError):
        setup_review(tmp_path,WideClient([]),final_report_tokens=invalid)


def test_validation_smoke_cannot_be_widened(tmp_path):
    from app.core.runs import RunService
    from app.core.targets import registered_profile, validate_target
    runs=RunService(tmp_path/'smoke.sqlite')
    target=validate_target(registered_profile(),'sequence_plausibility_review')
    rid=runs.create({**target.summary(),'objective_profile_id':target.objective_id,
        'requested_budget':{'usd_micros':100000,'max_meta_requests':2}},'local')
    with pytest.raises(ValueError,match='validation smoke|smoke|512'):
        MetaHost(WideClient([]),ReviewBridge(),runs,rid,'local',
                 workflow='validation_smoke',final_report_tokens=REPORT_TOKEN_CAP)


def test_wider_report_never_leaks_secrets_or_labels(tmp_path):
    client=WideClient([response(call=[tool()]),response(call=[score_tool()]),
                       response(text='Sequence preferences only; T50 and activity remain unknown.')])
    host,runs,rid,bridge=setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    asyncio.run(host.run())
    body=json.dumps(client.payloads)
    from app.core.targets import registered_profile
    for forbidden in ('evaluation_private','DMS_score',registered_profile()['reference_sequence'],
                      'ESM_BACKEND','MODEL_API_KEY','META_API_KEY'):
        assert forbidden not in body


def test_final_turn_adds_an_explicit_sentence_budget_only_to_the_report(tmp_path):
    """The reserved report turn must bound its own length; tool turns must not see it."""
    client=WideClient([response(call=[tool()]),response(call=[score_tool()]),
                       response(text='Sequence preferences only; T50 and activity remain unknown.')])
    host,runs,rid,bridge=setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    result=asyncio.run(host.run())
    assert result['status']=='sequence_review_complete'
    final=client.payloads[2]['messages'][-1]
    assert final['role']=='developer'
    assert 'concise sentences' in final['content']
    assert 'no tools' in final['content'].lower()
    for earlier in client.payloads[:2]:
        assert not any('concise sentences' in str(m.get('content')) for m in earlier['messages'])
    assert result['final_instruction_sha256']==result['final_instruction_sha256']
    assert len(result['final_instruction_sha256'])==64


def test_truncated_report_is_reported_as_length_not_complete(tmp_path):
    """A model that still overruns must stay partial, never a fabricated success."""
    long_reply=response(text='x'*200)
    long_reply['choices'][0]['finish_reason']='length'
    client=WideClient([response(call=[tool()]),response(call=[score_tool()]),long_reply])
    host,runs,rid,bridge=setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['stop_reason']=='invalid_or_forbidden_model_output'
    assert len(result['score_artifacts'])==1
    assert len(result['candidates'])==19


def test_every_review_request_sets_the_designed_reasoning_effort(tmp_path):
    """examples/meta_*_request.json specify execute=medium and report=low.

    Omitting the field lets reasoning tokens consume the whole completion budget,
    which returned finish_reason=length with no content on two live attempts.
    """
    client=WideClient([response(call=[tool()]),response(call=[score_tool()]),
                       response(text='Sequence preferences only; T50 and activity remain unknown.')])
    host,runs,rid,bridge=setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    result=asyncio.run(host.run())
    assert result['status']=='sequence_review_complete'
    assert [payload['reasoning_effort'] for payload in client.payloads]==['medium','medium','low']
    assert result['reasoning_effort']=={'tool_stage':'medium','final_report':'low'}


def test_empty_content_is_diagnosable_from_the_saved_trace(tmp_path):
    """A length stop with no content must be distinguishable from a truncated sentence."""
    empty=response(text=None)
    empty['choices'][0]['finish_reason']='length'
    client=WideClient([response(call=[tool()]),response(call=[score_tool()]),empty])
    host,runs,rid,bridge=setup_review(tmp_path,client,final_report_tokens=REPORT_TOKEN_CAP)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    last=[e for e in result['trace'] if e['event']=='meta_response'][-1]
    assert last['finish_reason']=='length'
    assert last['content_chars']==0
    assert 'reasoning_content' not in json.dumps(result)
