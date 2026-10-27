# Engineering Master Database

This repository contains the public engineering equipment catalog, original spreadsheets and source evidence, and portable verification tools. The catalog presents equipment profiles with links back to their original records. Source data and archived audit evidence remain authoritative; generated views do not establish equipment suitability or replace engineering review.

Clone and serve the public catalog with Python 3.11 or newer:

```bash
git clone https://github.com/classroomsolar/engineering-master-database.git
cd engineering-master-database
python3 01_Engineering_Equipment_Database/website/tools/serve.py --bind 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The released website is static and needs no npm installation or build step. The server serves only `01_Engineering_Equipment_Database/website/dist`. Deploy that directory alone to an HTTPS static host. The separate `03_MarketMind_Financial_Trading` project contains private finance material; keep it outside the public web root. Never serve the repository root.

Run the original-input checks from the repository root:

```bash
python3 06_Verification/verify_transfer.py --mode inputs --allow-output build
python3 -m unittest discover -s 06_Verification/tests -p 'test_*.py' -v
python3 -m unittest discover -s 01_Engineering_Equipment_Database/website/tests -p 'test_*.py' -v
```

The historical `SHA256_MANIFEST.json` retains all original identities. Default `inputs` mode verifies every historical input and archived report, and reports original/current hashes for the six explicitly maintained application-code files. New source files are permitted only in the documented source/test/documentation locations in `verify_transfer.py`; unexpected added data fails. `--mode snapshot` requires every historical hash and rejects new source files, so the maintained checkout is expected to fail that stricter original-snapshot comparison. Both modes ignore Git metadata, local `.venv` environments and Python caches. `--allow-output build` excludes only new generated files there and cannot hide changes to historical files. A checksum manifest records identity; independently authenticate its origin when assessing an untrusted transfer.

The verifier always prints JSON and returns a nonzero status on failure. Add `--output build/new-transfer-report.json` to retain a new report; existing reports are never overwritten. The preserved files in `06_Verification` and `dist/verification` are historical evidence, not claims about the current checkout.

For independent collection verification and reproducible derived outputs:

```bash
mkdir -p build
python3 01_Engineering_Equipment_Database/website/tools/verify_collections.py --source-workbook 02_Engineering_Master_Database/Engineering_Master_Database_Audited.xlsx --report build/released-verification.json
python3 01_Engineering_Equipment_Database/website/tools/build_collections.py --output-dir build/derived
python3 01_Engineering_Equipment_Database/website/tools/verify_collections.py --source-workbook 02_Engineering_Master_Database/Engineering_Master_Database_Audited.xlsx --collections-dist build/derived --report build/rebuilt-verification.json
python3 01_Engineering_Equipment_Database/website/tools/catalog_store.py build --collections-dist build/derived --output build/catalog.sqlite
```

These commands read the released `dist` and explicitly verify the audited master workbook. The builder creates collection and report files under a **new** output directory. The optional SQLite database is a disposable, indexed read model; original JavaScript source chunks, source references and spreadsheets remain the authority. Output paths must be new, outside the source trees, and are intentionally ignored under root `build/`. Choose new output names for another run to retain earlier results. No command above updates the public release automatically.

Browser tests use Python Playwright and Chromium. Install the pinned CI version in a virtual environment, then require browser execution:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install playwright==1.62.0
python -m playwright install chromium
REQUIRE_BROWSER_TESTS=1 python -m unittest discover -s 01_Engineering_Equipment_Database/website/tests -p 'test_*.py' -v
```

Linux may also need Playwright's documented system dependencies (`python -m playwright install --with-deps chromium`). Without Playwright/Chromium, browser tests may skip during local stdlib-only runs; CI requires them and installs Chromium. The GitHub workflow uses read-only repository permissions and checks tooling, real browser behavior, rebuilt collections, a derived SQLite store, and protected original inputs.
