"""Owned, hashed JSON artifacts; numerical output is rendered from saved records."""
import hashlib
import json
from pathlib import Path
import re

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class ArtifactStore:
    def __init__(self,root,runs):
        self.root=Path(root).resolve()
        self.runs=runs

    def save(self,run_id,owner_id,content):
        self.runs.get(run_id,owner_id)
        artifact_id=canonical_hash(content)
        directory=self.root/run_id
        if self.root not in directory.resolve().parents:
            raise ValueError('Artifact path escape')
        directory.mkdir(parents=True,exist_ok=True)
        path=directory/(artifact_id+'.json')
        envelope={'run_id':run_id,'artifact_id':artifact_id,'content':content}
        encoded=json.dumps(envelope,indent=2,allow_nan=False)
        if path.exists():
            if json.loads(path.read_text(encoding='utf-8')) != envelope:
                raise ValueError('Artifact collision or corruption')
        else:
            with path.open('x',encoding='utf-8') as handle:
                handle.write(encoded)
        return path

    def load(self,run_id,owner_id,artifact_id):
        self.runs.get(run_id,owner_id)
        if not isinstance(artifact_id,str) or re.fullmatch('[0-9a-f]{64}',artifact_id) is None:
            raise ValueError('Invalid artifact identity')
        path=self.root/run_id/(artifact_id+'.json')
        if self.root not in path.resolve().parents or path.is_symlink():
            raise ValueError('Artifact path escape')
        envelope=json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(envelope,dict) or envelope.get('run_id')!=run_id
                or 'content' not in envelope or canonical_hash(envelope['content'])!=artifact_id):
            raise ValueError('Artifact checksum mismatch')
        return envelope['content']
