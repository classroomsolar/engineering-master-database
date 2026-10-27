"""Validate an extracted transfer with Python standard library; does not edit files."""
from pathlib import Path
import hashlib, json, sys, zipfile

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
errors = []
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
expected = {item['path'] for item in manifest['files']}
actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name != 'SHA256_MANIFEST.json'}
for name in sorted(expected - actual): errors.append('Missing: ' + name)
for name in sorted(actual - expected): errors.append('Unmanifested: ' + name)
for item in manifest['files']:
    path = root / item['path']
    if not path.is_file(): continue
    if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']: errors.append('Changed: ' + item['path'])
    if path.suffix.lower() in ('.zip','.xlsx','.xlsm'):
        try:
            with zipfile.ZipFile(path) as z:
                bad = z.testzip()
                if bad: errors.append('Archive CRC failure: ' + item['path'] + ' / ' + bad)
        except zipfile.BadZipFile: errors.append('Invalid ZIP/OOXML: ' + item['path'])
print(json.dumps({'result':'PASS' if not errors else 'FAIL','filesChecked':len(manifest['files']),'failures':errors},indent=2))
sys.exit(1 if errors else 0)
