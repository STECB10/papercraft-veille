#!/usr/bin/env node
/* Contrôle de index.html juste après build.py, avant le rendu (qui, lui, attendrait 45 s puis sortirait une vidéo sans animation).

Usage : node serie/moteur/controle_page.mjs <projet>
  sert <projet> en local, ouvre index.html dans Chromium (celui de HyperFrames) et échoue si :
  - une erreur JavaScript remonte (pageerror) ou si un bloc de moteur.js a journalisé une erreur (window.__moteurErreurs) ;
  - window.__timelines.main n'existe pas 10 s après le chargement, ou si sa durée est nulle. */
import { execFileSync } from 'node:child_process';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const projet = path.resolve(process.argv[2] || '.');
const ATTENTE_MS = 10000;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.wav': 'audio/wav', '.mp3': 'audio/mpeg' };

function chrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const out = execFileSync('npx', ['hyperframes', 'browser', 'path'], { encoding: 'utf8', env: { ...process.env, HYPERFRAMES_NO_TELEMETRY: '1' } });
  return out.trim().split('\n').map(l => l.trim()).filter(l => l.startsWith('/')).pop();
}

const serveur = createServer((req, res) => {
  const f = path.join(projet, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!f.startsWith(projet) || !existsSync(f) || !statSync(f).isFile()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
  createReadStream(f).pipe(res);
});
await new Promise(r => serveur.listen(0, '127.0.0.1', r));

const erreurs = [];
const navigateur = await puppeteer.launch({ executablePath: chrome(), headless: true, args: ['--no-sandbox', '--mute-audio'] });
try {
  const page = await navigateur.newPage();
  await page.setViewport({ width: 1080, height: 1350 });
  page.on('pageerror', e => erreurs.push(`erreur JavaScript : ${e.message}`));
  page.on('console', m => { if (m.type() === 'error' && m.text().startsWith('[moteur]')) console.error(m.text()); });
  await page.goto(`http://127.0.0.1:${serveur.address().port}/index.html`, { waitUntil: 'load' });
  const pret = await page.waitForFunction(() => !!(window.__timelines && window.__timelines.main), { timeout: ATTENTE_MS }).then(() => true, () => false);
  if (!pret) erreurs.push(`window.__timelines.main absente ${ATTENTE_MS / 1000} s après le chargement`);
  const etat = await page.evaluate(() => ({
    blocs: window.__moteurErreurs || [],
    duree: window.__timelines && window.__timelines.main && typeof window.__timelines.main.duration === 'function' ? window.__timelines.main.duration() : 0,
  }));
  for (const b of etat.blocs) erreurs.push(`moteur.js, bloc ${b}`);
  if (pret && !(etat.duree > 0)) erreurs.push('timeline main vide (durée nulle)');
  if (!erreurs.length) console.log(`page OK : timeline main enregistrée (${etat.duree.toFixed(1)} s), aucune erreur JavaScript`);
} finally {
  await navigateur.close();
  serveur.close();
}
if (erreurs.length) {
  console.error('page refusée :\n- ' + erreurs.join('\n- '));
  process.exit(1);
}
