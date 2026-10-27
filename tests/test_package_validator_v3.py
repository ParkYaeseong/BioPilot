"""Run the checker against the real package and isolated deliberately broken copies."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class PackageValidatorV3Tests(unittest.TestCase):
    def run_checker(self,root):
        proc=subprocess.run([sys.executable,str(root/'checks/validate_package.py'),'--root',str(root)],
                            text=True,capture_output=True,timeout=30)
        self.assertIn(proc.returncode,(0,1),proc.stderr)
        return proc.returncode,json.loads(proc.stdout)

    def copy_package(self,destination):
        shutil.copytree(ROOT,destination,ignore=shutil.ignore_patterns(
            '__pycache__','MANIFEST.sha256','.git','.venv','.runtime','.cache',
            '.pytest_cache','.superpowers','.env','BioPilot_Atlas_Local_Start','local_artifacts'))

    def test_local_secret_and_environment_are_not_package_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'pack';self.copy_package(root)
            for directory in ('.venv', '.git', 'BioPilot_Atlas_Local_Start'):
                target=root/directory;target.mkdir(exist_ok=True)
                (target/'broken.json').write_text('{invalid local content')
            (root/'.env').write_text('not a package source')
            code,report=self.run_checker(root)
            self.assertEqual(code,0,report['failures'])

    def test_utf8_document_does_not_depend_on_windows_codepage(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'pack';self.copy_package(root)
            (root/'docs'/'utf8_receipt.md').write_text('# UTF-8 \U0001f52c\n',encoding='utf-8')
            code,report=self.run_checker(root)
            self.assertEqual(code,0,report['failures'])

    def test_current_v3_package_is_accepted(self):
        code,report=self.run_checker(ROOT)
        self.assertEqual(code,0,report['failures'])
        self.assertEqual(report['failed_count'],0)

    def test_catalog_schema_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'pack';self.copy_package(root)
            p=root/'schemas/tools.mcp.json';d=json.loads(p.read_text())
            d['tools'][0]['description']='Unreviewed different description';p.write_text(json.dumps(d))
            code,report=self.run_checker(root)
            self.assertEqual(code,1)
            self.assertIn('MCP/native catalog parity',report['failures'])

    def test_wrong_rubric_is_detected(self):
        import yaml
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'pack';self.copy_package(root)
            p=root/'config/hackathon.yaml';d=yaml.safe_load(p.read_text())
            d['rubric_weights']={k:0.25 for k in d['rubric_weights']};p.write_text(yaml.safe_dump(d))
            code,report=self.run_checker(root)
            self.assertEqual(code,1)
            self.assertIn('captured rubric weights match contract',report['failures'])

    def test_runtime_allowlist_cannot_expose_evaluator(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'pack';self.copy_package(root)
            p=root/'config/runtime_bundle.allowlist.json';d=json.loads(p.read_text())
            d['sources'].append('evaluation_private/assay_protocol.json');p.write_text(json.dumps(d))
            code,report=self.run_checker(root)
            self.assertEqual(code,1)
            self.assertIn('runtime source allowlist guarded',report['failures'])

    def test_overlong_recording_plan_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'pack';self.copy_package(root)
            p=root/'demo/storyboard.json';d=json.loads(p.read_text())
            d['segments'][-1]['end_s']=181;p.write_text(json.dumps(d))
            code,report=self.run_checker(root)
            self.assertEqual(code,1)
            self.assertIn('recording plan within 180 seconds',report['failures'])

if __name__=='__main__':unittest.main()
