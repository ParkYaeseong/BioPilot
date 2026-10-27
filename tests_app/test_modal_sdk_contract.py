"""Optional installed-SDK signature check; no authentication or remote operations."""
import importlib.metadata
import inspect
import pytest

def test_installed_modal_sdk_has_required_offline_api_shape():
    modal=pytest.importorskip('modal')
    assert importlib.metadata.version('modal')=='1.6.2'
    requirements=[
        (modal.App,{'include_source'}),
        (modal.App.function,{'timeout','block_network','include_source','serialized','retries','max_containers','min_containers'}),
        (modal.Volume.from_name,{'create_if_missing'}),
        (modal.Volume.with_mount_options,{'read_only'}),
        (modal.Function.from_name,{'environment_name'}),
        (modal.FunctionCall.get,{'timeout'}),
        (modal.Image.add_local_file,{'copy'}),
    ]
    for function,required in requirements:
        assert required <= set(inspect.signature(function).parameters)
