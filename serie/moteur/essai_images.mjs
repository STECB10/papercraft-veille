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
  const chev = await page.evaluate(() => {
    // chevauchements visibles : texte sur texte, ou texte sur un dessin (icône, barre, silhouette, point…)
    const vu = el => {
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > 1350 || r.right < 0 || r.left > 1080) return null;
      for (let e = el; e && e !== document.body; e = e.parentElement) {
        const cs = getComputedStyle(e);
        if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.5) return null;
      }
      return r;
    };
    const TXT = '.kick,.ptitle,.idv,.annot,.bval,.cival,.glab,.mlab,.mval,.kpt,.ailab,.oout,.gstep,.typo,.num,.cap,.note,.title,.mono,.chunk';
    const OBJ = '.ico,.bar,.strip,.sil,.pdot,.dd,.msheet,.spot,.sq,.cipt,.wbar,.pers';
    // la table est inclinée (boîtes gonflées) et la déchirure copie volontairement la planche : on les laisse de côté
    const ok = e => !e.closest('.tearh') && !e.closest('#night');
    const txt = [...document.querySelectorAll(TXT)].filter(e => ok(e) && !e.parentElement.closest(TXT)).map(e => [e, vu(e)]).filter(x => x[1]);
    const obj = [...document.querySelectorAll(OBJ)].filter(ok).map(e => [e, vu(e)]).filter(x => x[1]);
    const inter = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
    const nom = e => (e.className.baseVal ?? e.className).split(' ')[0] + ' « ' + (e.textContent || '').trim().slice(0, 30) + ' »';
    const out = [];
    for (let i = 0; i < txt.length; i++) {
      const [a, ra] = txt[i];
      for (let j = i + 1; j < txt.length; j++) {
        const [b, rb] = txt[j];
        if (a.contains(b) || b.contains(a)) continue;
        const s = inter(ra, rb);
        if (s > 0.12 * Math.min(ra.width * ra.height, rb.width * rb.height)) out.push(nom(a) + ' / ' + nom(b));
      }
      for (const [b, rb] of obj) {
        if (a.contains(b) || b.contains(a)) continue;
        const s = inter(ra, rb);
        if (s > 0.12 * Math.min(ra.width * ra.height, rb.width * rb.height)) out.push(nom(a) + ' / ' + nom(b));
      }
    }
    return out;
  });
  if (chev.length) console.log(`chevauchement à ${t.toFixed(2)} s (${nom}) :\n  ` + [...new Set(chev)].join('\n  '));
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
