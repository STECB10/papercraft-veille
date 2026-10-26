#!/usr/bin/env node
/* Images clés d'un essai (essai.py) : ouvre index.html dans Chromium, met la timeline à chaque moment de moments.json
   et assemble une planche contact (planche.png) avec ffmpeg. Échoue sur une erreur JavaScript ou de bloc du moteur. */
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = await import('playwright')); }

const projet = path.resolve(process.argv[2]);
const moments = JSON.parse(readFileSync(path.join(projet, 'moments.json'), 'utf8'));
const nav = await chromium.launch();
const page = await nav.newPage({ viewport: { width: 1080, height: 1350 } });
const erreurs = [];
page.on('pageerror', e => erreurs.push(e.message));
await page.goto('file://' + path.join(projet, 'index.html'));
await page.waitForFunction(() => !!(window.__timelines && window.__timelines.main), null, { timeout: 30000, polling: 250 });
const blocs = await page.evaluate(() => window.__moteurErreurs || []);
erreurs.push(...blocs);
// les clips HyperFrames (data-start / data-duration) ne sont montrés que dans leur fenêtre : on l'imite ici
await page.evaluate(() => {
  window.__seek = t => {
    document.querySelectorAll('.clip[data-start]').forEach(c => {
      const s = parseFloat(c.dataset.start), d = parseFloat(c.dataset.duration);
      c.style.visibility = t >= s && t < s + d ? 'visible' : 'hidden';
    });
    window.__timelines.main.pause(t, false);
  };
});
const fichiers = [];
for (const [i, [nom, t]] of moments.entries()) {
  await page.evaluate(t => window.__seek(t), t);
  const f = path.join(projet, `m${String(i).padStart(2, '0')}.png`);
  await page.screenshot({ path: f });
  fichiers.push([f, nom, t]);
}
await nav.close();
if (erreurs.length) { console.error('erreurs :\n- ' + erreurs.join('\n- ')); process.exit(1); }
// planche contact : 6 colonnes, chaque image légendée
const cols = 6, w = 360;
const args = ['-v', 'error', '-y'];
fichiers.forEach(([f]) => args.push('-i', f));
const filt = fichiers.map(([f, nom, t], k) =>
  `[${k}]scale=${w}:-1,drawtext=text='${(nom + ' ' + t.toFixed(1) + 's').replace(/[':]/g, ' ')}':x=8:y=h-30:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6[v${k}]`).join(';');
const n = fichiers.length, rows = Math.ceil(n / cols);
let pads = '';
const all = fichiers.map((_, k) => `[v${k}]`);
for (let k = n; k < rows * cols; k++) { pads += `;color=c=white:s=${w}x450:d=1[p${k}]`; all.push(`[p${k}]`); }
const layout = Array.from({ length: rows * cols }, (_, k) => `${(k % cols) * w}_${Math.floor(k / cols) * 450}`).join('|');
execFileSync('ffmpeg', [...args, '-filter_complex', `${filt}${pads};${all.join('')}xstack=inputs=${rows * cols}:layout=${layout}[o]`, '-map', '[o]', '-frames:v', '1', path.join(projet, 'planche.png')]);
console.log(`images : ${n}, planche : ${path.join(projet, 'planche.png')}`);
