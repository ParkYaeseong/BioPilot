"""Source inventory excludes local credentials, tools, caches and environments."""
from pathlib import Path

EXCLUDED = frozenset({'.git', '.venv', '.runtime', '.cache', '.pytest_cache',
    '.superpowers', '__pycache__', 'BioPilot_Atlas_Local_Start', 'local_artifacts',
    '.ssh', '.ruff_cache', '.mypy_cache', '.tox', '.nox', 'htmlcov',
    'build', 'dist'})
EXCLUDED_FOLDED = frozenset(name.casefold() for name in EXCLUDED)
LOCAL_SUFFIXES = ('.pyc', '.pyo', '.safetensors', '.pt', '.pth',
    '.db', '.db-wal', '.db-shm', '.db-journal', '.pem', '.key', '.ppk', '.p12', '.pfx',
    '.mp4', '.mov', '.mkv', '.webm', '.wav', '.mp3', '.zip', '.7z', '.tar', '.gz', '.log')
EVALUATOR_SCAFFOLDS = frozenset({'assay_protocol.json','dataset_reconciliation.json'})
LOCAL_DOCUMENT_DIRECTORIES = frozenset({'docs/archive', 'docs/superpowers', 'docs/diagrams'})
LOCAL_DOCUMENTS = frozenset({
    'AGENTS.md', 'START_HERE_KO.md', 'MANIFEST.sha256',
    'docs/01_product_spec.md', 'docs/02_system_design.md', 'docs/03_meta_integration.md',
    'docs/05_security_and_budget.md', 'docs/06_ui_and_demo.md',
    'docs/07_decisions_and_risks.md', 'docs/08_review_checklist.md',
    'docs/09_contracts_and_template_usage.md', 'docs/12_biological_readiness.md',
    'docs/13_WORK_handoff.md', 'docs/14_hackathon_rules_and_strategy.md',
    'docs/15_mcp_contract_and_hosts.md', 'docs/16_impact_and_agent_evaluation.md',
    'docs/17_submission_and_demo_checklist.md', 'docs/18_credit_and_model_policy.md',
    'docs/BIOPILOT_ATLAS_KO.md', 'docs/DECISIONS.md', 'docs/OPEN_ISSUES.md',
    'docs/OVERVIEW_REFINEMENT_KO.md', 'docs/POLISHED_REVIEW_KO.md', 'docs/STATUS.md',
    'docs/VALIDATION.md', 'docs/WORKSPACE_REFINEMENT_KO.md',
    'docs/images/biopilot-demo.gif', 'docs/images/final-video-preview.jpg',
    'docs/images/guided-tutorial.png', 'docs/images/live-session-light.png',
    'docs/images/workbench-light.png',
})

def package_files(root: Path):
    # Prune before descent: never read the local secret or model/cache contents.
    for directory, dirs, files in root.walk():
        if directory==root/'evaluation_private':
            # Preserve only the original label-free protocol scaffolding. Local
            # assay imports, frozen predictions and evaluator results stay local.
            dirs[:]=[]
            files=[name for name in files if name in EVALUATOR_SCAFFOLDS]
        else:
            dirs[:] = [d for d in dirs if d.casefold() not in EXCLUDED_FOLDED
                       and (directory/d).relative_to(root).as_posix() not in LOCAL_DOCUMENT_DIRECTORIES
                       and not d.casefold().endswith('.egg-info') and not (directory/d).is_symlink()
                       and (d.casefold()!='evaluation_private' or directory==root)]
        for name in files:
            path = directory/name
            if path.relative_to(root).as_posix() in LOCAL_DOCUMENTS:
                continue
            lower=name.casefold()
            if (lower == '.env' or lower.endswith('.env')
                    or (lower.startswith('.env.') and lower != '.env.example')):
                continue
            if directory == root/'validation' and lower.endswith('.txt'):
                continue
            if (directory == root/'submission' and lower.endswith('.md')
                    and lower.startswith(('form_answers', 'form_draft'))):
                continue
            if (path.is_symlink() or lower.endswith(LOCAL_SUFFIXES)
                    or lower in {'.coverage', 'coverage.xml', '.ds_store', 'thumbs.db'}
                    or '.sqlite' in lower):
                continue
            yield path
