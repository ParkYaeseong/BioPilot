"""Host-owned local journal; no provider, evaluator, arbitrary file or GPU access.

Only a validated record can be atomically claimed, once. A process interruption
leaves it running/unconfirmed; refreshing never grants another execution.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from app.bench_intake import validate_frozen


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',',':'), allow_nan=False)


def _now():
    return datetime.now(timezone.utc).isoformat()


class ReviewStore:
    def __init__(self, root, *, max_runs=3):
        if type(max_runs) is not int or not 1 <= max_runs <= 10:
            raise ValueError('Local execution cap must be 1–10 runs.')
        self.root=Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db=self.root/'reviews.sqlite'
        with self._connection() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER NOT NULL)')
            conn.execute("INSERT OR IGNORE INTO settings VALUES ('max_runs',?)",(max_runs,))
            conn.execute("UPDATE settings SET value=MIN(value,?) WHERE key='max_runs'",(max_runs,))
            conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY, created TEXT NOT NULL, updated TEXT NOT NULL,
                status TEXT NOT NULL, request TEXT NOT NULL, digest TEXT NOT NULL,
                report_sha256 TEXT, error TEXT)''')

    @contextmanager
    def _connection(self):
        conn=sqlite3.connect(self.db, timeout=15)
        conn.row_factory=sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _id(self, review_id):
        if not isinstance(review_id,str) or not re.fullmatch('[0-9a-f]{32}',review_id):
            raise ValueError('Unknown review identifier.')
        return review_id

    def _decode(self,row):
        if row is None:
            raise ValueError('Review not found in this local journal.')
        item=dict(row)
        if hashlib.sha256(item['request'].encode()).hexdigest()!=item['digest']:
            raise ValueError('Frozen input checksum mismatch; execution refused.')
        item['request']=validate_frozen(json.loads(item['request']))
        return item

    def create(self, request):
        validate_frozen(request)
        review_id=uuid4().hex;stamp=_now();encoded=_json(request)
        with self._connection() as conn:
            conn.execute('INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?)',
                (review_id,stamp,stamp,'validated',encoded,hashlib.sha256(encoded.encode()).hexdigest(),None,None))
        return self.get(review_id)

    def get(self, review_id):
        with self._connection() as conn:
            return self._decode(conn.execute('SELECT * FROM reviews WHERE id=?',(self._id(review_id),)).fetchone())

    def recent(self):
        with self._connection() as conn:
            return [self._decode(r) for r in conn.execute('SELECT * FROM reviews ORDER BY created DESC LIMIT 50')]

    @property
    def remaining_runs(self):
        with self._connection() as conn:
            cap=conn.execute("SELECT value FROM settings WHERE key='max_runs'").fetchone()[0]
            used=conn.execute("SELECT COUNT(*) FROM reviews WHERE status!='validated'").fetchone()[0]
            return max(0,cap-used)

    def claim(self, review_id, *, approved):
        if approved is not True:
            raise ValueError('Explicit execution approval required.')
        with self._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=self._decode(conn.execute('SELECT * FROM reviews WHERE id=?',(self._id(review_id),)).fetchone())
            if row['status']!='validated':
                raise ValueError('This review was already claimed; inspect its record, never retry on refresh.')
            cap=conn.execute("SELECT value FROM settings WHERE key='max_runs'").fetchone()[0]
            used=conn.execute("SELECT COUNT(*) FROM reviews WHERE status!='validated'").fetchone()[0]
            if used>=cap:
                raise ValueError('The durable local run cap is spent; it cannot be reset by refreshing.')
            conn.execute("UPDATE reviews SET status='running',updated=? WHERE id=?",(_now(),review_id))
        return self.get(review_id)

    def workspace(self, review_id):
        self.get(review_id)
        return self.root/'runs'/self._id(review_id)

    def report_path(self, review_id):
        item=self.get(review_id)
        path=self.root/'reports'/(self._id(review_id)+'.json')
        if not item['report_sha256'] or not path.is_file():
            raise ValueError('No saved report is available for this review.')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['report_sha256']:
            raise ValueError('Saved report checksum mismatch; result not opened.')
        return path

    def finish(self, review_id, *, status, report=None, error=None):
        if status not in ('completed','partial','failed'):
            raise ValueError('Execution must retain a terminal or partial status.')
        digest=None
        with self._connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=self._decode(conn.execute('SELECT * FROM reviews WHERE id=?',(self._id(review_id),)).fetchone())
            if row['status']!='running':
                raise ValueError('Only an owned running review can finish, once.')
            if report is not None:
                if not isinstance(report,bytes) or len(report)>8*1024*1024:
                    raise ValueError('Invalid bounded report bytes.')
                payload=json.loads(report)
                from app.review_flow import result_phase
                if result_phase(payload.get('status'))!=status:
                    raise ValueError('Run status and saved report disagree.')
                folder=self.root/'reports';folder.mkdir(exist_ok=True)
                with (folder/(review_id+'.json')).open('xb') as output:
                    output.write(report)
                digest=hashlib.sha256(report).hexdigest()
            elif status in ('completed','partial'):
                raise ValueError('A result requires its actual report.')
            conn.execute('UPDATE reviews SET status=?,updated=?,report_sha256=?,error=? WHERE id=?',
                (status,_now(),digest,str(error)[:800] if error else None,review_id))
        return self.get(review_id)
