import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  readZipCentralDirectory,
  readZipEntryBuffer,
  hydrateMissingDistFromZip,
  createZipFallbackMiddleware,
} from '../lib/zip_dist_fallback.mjs';

const ZIP_PATH = path.resolve('exports', 'engineering-equipment-database-website.zip');
const GITHUB_ZIP_PATH = path.resolve('exports', 'engineering-equipment-database-github.zip');

test('readZipCentralDirectory & readZipEntryBuffer extract critical catalog entries cleanly', () => {
  const index = readZipCentralDirectory(ZIP_PATH);
  assert.ok(index.size >= 180);
  for (const name of index.keys()) {
    const low = name.toLowerCase();
    assert.equal(low.endsWith('.xlsx'), false, `ZIP must not bundle raw spreadsheet ${name}`);
    assert.equal(low.includes('/quarantine/') || low.includes('quarantine_bag') || low.includes('quarantine_report'), false, `ZIP must not bundle quarantine ${name}`);
  }

  const ghIndex = readZipCentralDirectory(GITHUB_ZIP_PATH);
  assert.ok(ghIndex.size >= 190);
  for (const name of ghIndex.keys()) {
    const low = name.toLowerCase();
    assert.equal(low.endsWith('.xlsx'), false, `GitHub ZIP must not bundle raw spreadsheet ${name}`);
    assert.equal(low.includes('/quarantine/') || low.includes('quarantine_bag') || low.includes('quarantine_report'), false, `GitHub ZIP must not bundle quarantine ${name}`);
  }

  const collEntry = index.get('dist/collections/index.js');
  assert.ok(collEntry);
  const collBuf = readZipEntryBuffer(ZIP_PATH, collEntry);
  assert.ok(collBuf.toString('utf8').includes('EQUIPMENT_CATALOG'));

  const dbEntry = index.get('dist/data/catalog.js');
  assert.ok(dbEntry);
  const dbBuf = readZipEntryBuffer(ZIP_PATH, dbEntry);
  assert.ok(dbBuf.toString('utf8').includes('DB_CATALOG'));
});

test('hydrateMissingDistFromZip restores missing files without overwriting newer existing files', () => {
  const tmpDist = fs.mkdtempSync(path.join(os.tmpdir(), 'eedb-hydrate-'));
  try {
    fs.writeFileSync(path.join(tmpDist, 'index.html'), 'CUSTOM_NEWER_HTML', 'utf8');
    const res = hydrateMissingDistFromZip(ZIP_PATH, tmpDist);
    assert.ok(res.hydrated >= 180);
    assert.equal(res.failed, 0);
    assert.equal(fs.readFileSync(path.join(tmpDist, 'index.html'), 'utf8'), 'CUSTOM_NEWER_HTML');
    assert.ok(fs.existsSync(path.join(tmpDist, 'collections', 'index.js')));
    assert.ok(fs.existsSync(path.join(tmpDist, 'data', 'catalog.js')));
    assert.ok(fs.existsSync(path.join(tmpDist, 'verification', 'security_governance_audit.json')));
  } finally {
    fs.rmSync(tmpDist, { recursive: true, force: true });
  }
});

test('createZipFallbackMiddleware serves missing static assets cleanly and rejects traversal', () => {
  const mw = createZipFallbackMiddleware(ZIP_PATH);

  let nextCalled = false;
  mw({ method: 'GET', path: '/../package.json' }, {}, () => {
    nextCalled = true;
  });
  assert.equal(nextCalled, true);

  const headers = {};
  let statusCode = 0;
  let sentBody = null;
  mw(
    { method: 'GET', path: '/collections/index.js' },
    {
      setHeader: (k, v) => {
        headers[k.toLowerCase()] = v;
      },
      status: (code) => {
        statusCode = code;
        return {
          send: (buf) => {
            sentBody = buf;
          },
          end: () => {},
        };
      },
    },
    () => {
      throw new Error('Should not fall through');
    }
  );
  assert.equal(statusCode, 200);
  assert.equal(headers['content-type'], 'application/javascript; charset=utf-8');
  assert.ok(sentBody.toString('utf8').includes('EQUIPMENT_CATALOG'));

  for (const blocked of ['/spreadsheets/s001.xlsx', '/verification/security_governance_audit.json', '/anything.xlsx']) {
    let skipped = false;
    mw({ method: 'GET', path: blocked }, {}, () => {
      skipped = true;
    });
    assert.equal(skipped, true, `Blocked path ${blocked} must not be served by zip fallback`);
  }
});
