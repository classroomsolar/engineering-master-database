import fs from 'node:fs';
import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  hydrateMissingDistFromZip,
  createZipFallbackMiddleware,
} from './lib/zip_dist_fallback.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const HOST = '0.0.0.0';
const distDir = path.join(__dirname, '01_Engineering_Equipment_Database', 'website', 'dist');
const exportsDir = path.join(__dirname, 'exports');
const exportZipPath = path.join(exportsDir, 'engineering-equipment-database-website.zip');
const ALLOWED_RELEASE_ZIPS = new Set([
  'engineering-equipment-database-github.zip',
  'engineering-equipment-database-website.zip',
]);

const hydration = hydrateMissingDistFromZip(exportZipPath, distDir);
if (hydration.hydrated > 0 || hydration.failed > 0) {
  console.log(
    `Dist hydration from ZIP: hydrated=${hydration.hydrated}, skipped=${hydration.skipped}, failed=${hydration.failed}`
  );
}

app.use((req, res, next) => {
  const p = (req.path || '').toLowerCase();
  if (
    p.startsWith('/spreadsheets/') ||
    p.startsWith('/verification/') ||
    p.startsWith('/exports/') ||
    p.startsWith('/quarantine/') ||
    p === '/inventory.csv' ||
    p === '/readme.txt' ||
    p === '/verification_report.txt' ||
    p.endsWith('.xlsx')
  ) {
    return res.status(404).end();
  }
  return next();
});

app.get('/download/:filename', (req, res) => {
  const name = String(req.params.filename || '');
  if (!ALLOWED_RELEASE_ZIPS.has(name)) {
    return res.status(404).end();
  }
  const filePath = path.join(exportsDir, name);
  if (!fs.existsSync(filePath)) {
    return res.status(404).end();
  }
  res.setHeader('Content-Type', 'application/zip');
  return res.download(filePath, name);
});

app.use(express.static(distDir));
app.use(createZipFallbackMiddleware(exportZipPath));

app.use((req, res, next) => {
  if (req.method !== 'GET' || req.path.includes('.')) {
    return next();
  }
  res.sendFile(path.join(distDir, 'index.html'));
});

app.listen(PORT, HOST, () => {
  console.log(`Server listening on http://${HOST}:${PORT}`);
});
