import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const EOCD_SIG = 0x06054b50;
const CD_SIG = 0x02014b50;
const LFH_SIG = 0x04034b50;

const MIME_BY_EXT = {
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
};

export function readZipCentralDirectory(zipPath) {
  const entries = new Map();
  if (!zipPath || !fs.existsSync(zipPath)) return entries;

  const fd = fs.openSync(zipPath, 'r');
  try {
    const fileSize = fs.fstatSync(fd).size;
    if (fileSize < 22) return entries;

    const tailLen = Math.min(fileSize, 65557);
    const tailStart = fileSize - tailLen;
    const tail = Buffer.allocUnsafe(tailLen);
    fs.readSync(fd, tail, 0, tailLen, tailStart);

    let eocdPos = -1;
    for (let i = tailLen - 22; i >= 0; i -= 1) {
      if (tail.readUInt32LE(i) === EOCD_SIG) {
        const commentLen = tail.readUInt16LE(i + 20);
        if (i + 22 + commentLen === tailLen) {
          eocdPos = i;
          break;
        }
      }
    }
    if (eocdPos < 0) return entries;

    const cdSize = tail.readUInt32LE(eocdPos + 12);
    const cdOffset = tail.readUInt32LE(eocdPos + 16);
    if (cdOffset + cdSize > fileSize) return entries;

    const cdBuf = Buffer.allocUnsafe(cdSize);
    fs.readSync(fd, cdBuf, 0, cdSize, cdOffset);

    let ptr = 0;
    while (ptr + 46 <= cdBuf.length) {
      if (cdBuf.readUInt32LE(ptr) !== CD_SIG) break;
      const compressionMethod = cdBuf.readUInt16LE(ptr + 10);
      const compressedSize = cdBuf.readUInt32LE(ptr + 20);
      const uncompressedSize = cdBuf.readUInt32LE(ptr + 24);
      const nameLen = cdBuf.readUInt16LE(ptr + 28);
      const extraLen = cdBuf.readUInt16LE(ptr + 30);
      const commentLen = cdBuf.readUInt16LE(ptr + 32);
      const localHeaderOffset = cdBuf.readUInt32LE(ptr + 42);
      const name = cdBuf.toString('utf8', ptr + 46, ptr + 46 + nameLen);

      if (name && !name.endsWith('/')) {
        entries.set(name, {
          name,
          compressionMethod,
          compressedSize,
          uncompressedSize,
          localHeaderOffset,
        });
      }
      ptr += 46 + nameLen + extraLen + commentLen;
    }
  } finally {
    fs.closeSync(fd);
  }
  return entries;
}

export function readZipEntryBuffer(zipPath, entry) {
  if (!entry) return null;
  const fd = fs.openSync(zipPath, 'r');
  try {
    const lfh = Buffer.allocUnsafe(30);
    fs.readSync(fd, lfh, 0, 30, entry.localHeaderOffset);
    if (lfh.readUInt32LE(0) !== LFH_SIG) {
      throw new Error(`Invalid ZIP local file header for ${entry.name}`);
    }
    const nameLen = lfh.readUInt16LE(26);
    const extraLen = lfh.readUInt16LE(28);
    const dataOffset = entry.localHeaderOffset + 30 + nameLen + extraLen;
    const raw = Buffer.allocUnsafe(entry.compressedSize);
    fs.readSync(fd, raw, 0, entry.compressedSize, dataOffset);

    if (entry.compressionMethod === 0) return raw;
    if (entry.compressionMethod === 8) return zlib.inflateRawSync(raw);
    throw new Error(`Unsupported ZIP compression method ${entry.compressionMethod} for ${entry.name}`);
  } finally {
    fs.closeSync(fd);
  }
}

export function hydrateMissingDistFromZip(zipPath, distDir) {
  const entries = readZipCentralDirectory(zipPath);
  let hydrated = 0;
  let skipped = 0;
  let failed = 0;
  if (!entries.size) return { hydrated, skipped, failed };

  const resolvedDist = path.resolve(distDir);
  for (const [entryName, entry] of entries.entries()) {
    if (!entryName.startsWith('dist/')) continue;
    const rel = entryName.slice('dist/'.length);
    if (!rel || rel.includes('..') || rel.includes('\0')) continue;
    const target = path.resolve(resolvedDist, rel);
    if (!target.startsWith(resolvedDist + path.sep)) continue;

    if (fs.existsSync(target)) {
      skipped += 1;
      continue;
    }
    try {
      const buf = readZipEntryBuffer(zipPath, entry);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, buf);
      hydrated += 1;
    } catch (_err) {
      failed += 1;
    }
  }
  return { hydrated, skipped, failed };
}

export function createZipFallbackMiddleware(zipPath) {
  let cachedIndex = null;
  const getIndex = () => {
    if (!cachedIndex) {
      cachedIndex = readZipCentralDirectory(zipPath);
    }
    return cachedIndex;
  };

  return function zipDistFallback(req, res, next) {
    if (req.method !== 'GET' && req.method !== 'HEAD') return next();
    const rawPath = (req.path || '/').replace(/^\/+/, '');
    if (!rawPath || rawPath.includes('..') || rawPath.includes('\0') || rawPath.includes('\\')) {
      return next();
    }
    const lower = rawPath.toLowerCase();
    if (lower.startsWith('spreadsheets/') || lower.startsWith('verification/') || lower.startsWith('quarantine/') || lower.endsWith('.xlsx')) {
      return next();
    }
    const zipKey = `dist/${rawPath}`;
    const index = getIndex();
    const entry = index.get(zipKey);
    if (!entry) return next();

    try {
      const buf = readZipEntryBuffer(zipPath, entry);
      const ext = path.extname(rawPath).toLowerCase();
      res.setHeader('Content-Type', MIME_BY_EXT[ext] || 'application/octet-stream');
      res.setHeader('Content-Length', String(buf.length));
      if (req.method === 'HEAD') return res.status(200).end();
      return res.status(200).send(buf);
    } catch (err) {
      return next(err);
    }
  };
}
