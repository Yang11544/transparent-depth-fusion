"""Public-package CPU file I/O helpers, selected from the existing timing utilities.
No live model, GPU, subprocess or input-image functions are included.
"""
from __future__ import annotations
import csv, hashlib, json, os
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]

class ProtocolError(RuntimeError):
    pass

def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def dump(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def write_csv(path, rows):
    if not rows: raise ProtocolError('Refusing to write an empty completed table')
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def read_csv(path):
    with Path(path).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def checked_file(path, digest, expected_bytes=None):
    p = Path(path)
    if not p.is_file(): raise ProtocolError(f'Missing actual file: {p}')
    st = p.stat(); actual = sha(p)
    if expected_bytes is not None and st.st_size != expected_bytes:
        raise ProtocolError(f'Length mismatch: {p}')
    if actual != digest: raise ProtocolError(f'SHA256 mismatch: {p}; do not change pinned identities')
    return dict(path=str(p), resolved_path=str(p.resolve()), bytes=st.st_size, sha256=actual)
