"""Exercise the workbench without dispatching a provider or scientific worker.

Run with only requirements/workbench.txt installed. This checks rendered AppTest
elements and saved data, not browser JavaScript, an independent PC, or live inference.
"""
import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from streamlit.testing.v1 import AppTest
    from app.viewer_data import load_run_view
    from app import bench_execution, session_exec

    def forbidden(*args, **kwargs):
        raise AssertionError('Offline reproduction must never dispatch work')

    original_execute = bench_execution.execute_review
    original_run = session_exec.run_session
    original_argv = sys.argv[:]
    bench_execution.execute_review = forbidden
    session_exec.run_session = forbidden
    try:
        with TemporaryDirectory(prefix='biopilot-reproduction-') as temporary:
            sys.argv = ['bench.py', '--state-dir', temporary,
                        '--esm-env', str(Path(temporary) / 'absent.env')]
            app = AppTest.from_file(str(root / 'app/bench.py'), default_timeout=60).run()
            assert not app.exception, [str(x.value) for x in app.exception]
            assert app.session_state['active_view'] == 'Overview'
            for view in ('Candidates', 'Structure', 'Agent Trace', 'Evidence', 'Overview'):
                app.session_state['active_view'] = view
                app.run()
                assert not app.exception, [str(x.value) for x in app.exception]
            app.button(key='bench_new').click().run()
            assert not app.exception, [str(x.value) for x in app.exception]
            app.text_area(key='bench_message').set_value('Review S108A').run()
            app.button(key='bench_validate').click().run()
            assert any('Protected catalytic site' in x.value for x in app.error)
            app.text_area(key='bench_message').set_value('Review A32V').run()
            app.button(key='bench_validate').click().run()
            assert not app.exception
            assert app.session_state['bench_pending']
            assert app.button(key='bench_execute').disabled
            view = load_run_view(root / 'examples/artifacts/unified_review_20261029.replay.json')
            assert view['candidate_count'] == 19
            assert view['integrity_status'] == 'locally_consistent'
    finally:
        bench_execution.execute_review = original_execute
        session_exec.run_session = original_run
        sys.argv = original_argv
    receipt = {
        'status': 'PASS', 'python': sys.version.split()[0],
        'scope': 'offline Streamlit AppTest and saved data; not browser JS or live inference',
        'views': 5, 'saved_candidates': 19, 'guard_S108A': 'blocked',
        'guard_A32V': 'accepted', 'execute_disabled_without_configuration': True,
        'live_execution_verified': False, 'provider_calls': 0, 'gpu_calls': 0,
    }
    if options.output:
        options.output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
