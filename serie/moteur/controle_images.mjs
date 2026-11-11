#!/usr/bin/env node
/* Contrôle d'images : rejoue index.html seconde par seconde et mesure ce qu'il y a vraiment à l'écran.

Pourquoi : controle_page.mjs dit que la page marche, verifier.py que les ancres tombent bien ; rien ne disait qu'un
spectateur regardait une page blanche pendant deux secondes, ou un cadre rempli seulement dans son tiers haut
(vidéo du 10 novembre 2026 : « Ensuite, » puis « Concrètement, » sur une planche nue).

Usage : node serie/moteur/controle_images.mjs <projet> [--pas 0.5] [--planche] [--detail] [--strict]
  écrit <projet>/images.json : le résumé (occupation, étendue, écrans vides, cadres sous-remplis) et une phrase « bilan »
  --detail  : écrit aussi <projet>/images-detail.json (la mesure de chaque instant)
  --planche : écrit aussi <projet>/pellicule-NN.jpg (une image toutes les 2 s, pour relire le film d'un coup d'œil)
  --strict  : sort en erreur s'il reste un écran vide de plus de VIDE_MAX secondes

Mesure : la scène (au-dessus de la bande des sous-titres, sous l'étiquette de la planche) est découpée en cases de
40 px ; une case compte si un élément réellement visible la touche (texte, trait, aplat ; pas les fonds de papier).
  occupation : part des cases touchées
  étendue    : hauteur entre l'élément le plus haut et le plus bas, rapportée à la scène */
import { execFileSync } from 'node:child_process';
import { createReadStream, existsSync, statSync, writeFileSync, rmSync } from 'node:fs';
import { createServer } from 'node:http';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const args = process.argv.slice(2);
const projet = path.resolve(args.find(a => !a.startsWith('--')) || '.');
const opt = (nom, def) => { const i = args.indexOf(nom); return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? parseFloat(args[i + 1]) : def; };
const PAS = opt('--pas', 0.5);
const PLANCHE = args.includes('--planche');
const DETAIL = args.includes('--detail');
const STRICT = args.includes('--strict');
const VIDE = 0.03;        // en dessous : rien à regarder (une étiquette seule fait 1 à 2 %)
const VIDE_MAX = 2.0;     // secondes d'écran vide tolérées d'affilée (une feuille qui arrive, un pli)
const CREUX = 0.34;       // étendue en dessous de laquelle le cadre est « sous-rempli »
const CREUX_MAX = 4.0;    // secondes tolérées d'affilée
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

const navigateur = await puppeteer.launch({ executablePath: chrome(), headless: true, args: ['--no-sandbox', '--mute-audio'] });
let rapport;
try {
  const page = await navigateur.newPage();
  await page.setViewport({ width: 1080, height: 1350 });
  await page.goto(`http://127.0.0.1:${serveur.address().port}/index.html`, { waitUntil: 'load' });
  await page.waitForFunction(() => !!(window.__timelines && window.__timelines.main), { timeout: 30000 });
  const duree = await page.evaluate(() => {
    // les clips HyperFrames ne sont montrés que dans leur fenêtre : on l'imite, comme essai_images.mjs
    window.__seek = t => {
      document.querySelectorAll('.clip[data-start]').forEach(c => {
        const s = parseFloat(c.dataset.start), d = parseFloat(c.dataset.duration);
        c.style.visibility = t >= s && t < s + d ? 'visible' : 'hidden';
      });
      window.__timelines.main.pause(t, false);
    };
    // ce qui est décor et non contenu : fonds, lumières, plis, grain, fil de progression, sous-titres
    const DECOR = '.pground,.plight,.pcrease,.pdim,.pcorner,.tablebg,.halo,.sheetsh,.nscrim,.cvbg,.cvfold,.pvground,.endbg,.flap,.flapwrap,.streak,.corner,.crease,.grainin,.progb,.progseg,.bandclip,.band,.pvq';
    const X0 = 0, X1 = 1080, Y0 = 135, Y1 = 1090, C = 40;
    const NX = Math.ceil((X1 - X0) / C), NY = Math.ceil((Y1 - Y0) / C);
    window.__mesure = () => {
      const grille = new Uint8Array(NX * NY);
      const opac = new Map();
      const visible = el => {
        // produit des opacités jusqu'à la racine (mémorisé), et aucun ancêtre caché
        if (!el || el === document.documentElement) return 1;
        if (opac.has(el)) return opac.get(el);
        const cs = getComputedStyle(el);
        let o = cs.visibility === 'hidden' || cs.display === 'none' ? 0 : parseFloat(cs.opacity);
        if (o > 0) o *= visible(el.parentElement);
        opac.set(el, o);
        return o;
      };
      let haut = Infinity, bas = -Infinity, n = 0;
      const marquer = r => {
        const a = Math.max(X0, r.left), b = Math.min(X1, r.right), c = Math.max(Y0, r.top), d = Math.min(Y1, r.bottom);
        if (b - a < 2 || d - c < 2) return;
        haut = Math.min(haut, c); bas = Math.max(bas, d); n++;
        for (let gy = Math.floor((c - Y0) / C); gy <= Math.min(NY - 1, Math.floor((d - 1 - Y0) / C)); gy++)
          for (let gx = Math.floor((a - X0) / C); gx <= Math.min(NX - 1, Math.floor((b - 1 - X0) / C)); gx++) grille[gy * NX + gx] = 1;
      };
      const racines = ['#night', '#paper', '#pivot', '#end', '#cover'].map(s => document.querySelector(s)).filter(Boolean);
      for (const racine of racines) {
        if (getComputedStyle(racine).visibility === 'hidden') continue;
        const marche = document.createTreeWalker(racine, NodeFilter.SHOW_ELEMENT);
        for (let el = marche.nextNode(); el; el = marche.nextNode()) {
          if (el.matches(DECOR)) continue;
          const tag = el.tagName.toLowerCase();
          let contenu = false;
          if (['path', 'circle', 'rect', 'line', 'polyline', 'polygon'].includes(tag)) contenu = true;
          else if ([...el.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) contenu = true;
          else if (tag !== 'svg' && !el.matches('.clip,.plate,.pbody,.foldsheet,.sheet,.persp,#nplane,#ncam,#pcam,#coverin,.tearh,.stepg')) {
            // un aplat ou un contour (carte, tuile, horloge), même s'il contient autre chose
            const cs = getComputedStyle(el);
            contenu = cs.backgroundImage !== 'none' || !/rgba\(0, 0, 0, 0\)|transparent/.test(cs.backgroundColor) || parseFloat(cs.borderTopWidth) > 0;
          }
          if (!contenu || visible(el) < 0.3) continue;
          const r = el.getBoundingClientRect();
          // un aplat qui couvre presque tout le cadre est un fond, pas un contenu
          if (r.width * r.height > 0.8 * 1080 * 1350) continue;
          marquer(r);
        }
      }
      const pleines = grille.reduce((s, v) => s + v, 0);
      // une grande typo à l'écran (la question du pivot, la nuance, la phrase à retenir, la promesse) : écran de texte seul, voulu
      const typo = [...document.querySelectorAll('.typo .tw, .typo .tc')].some(w => visible(w) >= 0.3 && w.getBoundingClientRect().width > 1);
      return { occ: +(pleines / grille.length).toFixed(3), et: n ? +((bas - haut) / (Y1 - Y0)).toFixed(3) : 0, typo: typo ? 1 : 0 };
    };
    return window.__timelines.main.duration();
  });
  const film = JSON.parse(await page.evaluate(() => JSON.stringify(window.FILM)));
  const pts = [];
  const images = [];
  for (let t = 0; t < duree - 0.05; t = +(t + PAS).toFixed(3)) {
    await page.evaluate(t => window.__seek(t), t);
    const m = await page.evaluate(() => window.__mesure());
    pts.push({ t, ...m });
    if (PLANCHE && Math.abs(t / 2 - Math.round(t / 2)) < 1e-6) {
      const f = path.join(projet, `_pel${String(images.length).padStart(3, '0')}.jpg`);
      await page.screenshot({ path: f, type: 'jpeg', quality: 80 });
      images.push(f);
    }
  }
  // plages : suites d'instants sous un seuil
  const plages = (test, min) => {
    const out = []; let d = null;
    for (const p of [...pts, { t: duree, occ: 1, et: 1, typo: 1 }]) {
      if (test(p)) { if (d === null) d = p.t; }
      else if (d !== null) { if (p.t - d >= min) out.push([+d.toFixed(2), +p.t.toFixed(2)]); d = null; }
    }
    return out;
  };
  // la couverture (image 0) et la toute fin (logo qui tient) ne comptent pas comme « planches »
  const dans = p => p.t >= (film.cover_out || 0) + 0.7 && p.t < duree - 0.5;
  const vides = plages(p => dans(p) && p.occ < VIDE, 0.75);
  const creux = plages(p => dans(p) && !p.typo && p.occ >= VIDE && p.et < CREUX, CREUX_MAX);
  const utiles = pts.filter(dans);
  const part = f => +(utiles.filter(f).length / Math.max(1, utiles.length) * 100).toFixed(1);
  rapport = {
    duree: +duree.toFixed(2), pas: PAS, edition: film.edition,
    occupation_moyenne: +(utiles.reduce((s, p) => s + p.occ, 0) / Math.max(1, utiles.length) * 100).toFixed(1),
    etendue_moyenne: +(utiles.reduce((s, p) => s + p.et, 0) / Math.max(1, utiles.length) * 100).toFixed(1),
    temps_vide_pct: part(p => p.occ < VIDE), temps_sous_rempli_pct: part(p => !p.typo && p.occ >= VIDE && p.et < CREUX),
    ecrans_vides: vides, cadres_sous_remplis: creux,
    pire_vide: vides.reduce((m, [a, b]) => Math.max(m, b - a), 0),
  };
  // le bilan, en une phrase, pour le message Telegram de validation
  const mmss = t => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
  const longs = vides.filter(([a, b]) => b - a >= VIDE_MAX);
  rapport.bilan = longs.length
    ? `écran vide ${longs.map(([a, b]) => `${(b - a).toFixed(1).replace('.', ',')} s à ${mmss(a)}`).join(', ')}`
    : creux.length ? `cadre peu rempli à ${creux.map(([a]) => mmss(a)).join(', ')}` : 'aucun écran vide, cadres remplis';
  writeFileSync(path.join(projet, 'images.json'), JSON.stringify(rapport, null, 1));
  if (DETAIL) writeFileSync(path.join(projet, 'images-detail.json'), JSON.stringify(pts));
  if (PLANCHE && images.length) {
    // pellicule : 8 images par ligne, 3 lignes par planche
    const par = 24;
    for (let k = 0; k * par < images.length; k++) {
      const lot = images.slice(k * par, (k + 1) * par);
      const liste = path.join(projet, '_pel.txt');
      writeFileSync(liste, lot.map(f => `file '${f}'\nduration 1`).join('\n'));
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', liste, '-vf', `scale=270:338,tile=8x${Math.ceil(lot.length / 8)}`,
        '-frames:v', '1', '-q:v', '3', path.join(projet, `pellicule-${String(k + 1).padStart(2, '0')}.jpg`)]);
      rmSync(liste);
    }
    images.forEach(f => rmSync(f));
  }
} finally {
  await navigateur.close();
  serveur.close();
}

const mmss = t => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
console.log(`images : ${rapport.duree} s, occupation moyenne ${rapport.occupation_moyenne} %, étendue moyenne ${rapport.etendue_moyenne} %, `
  + `écran vide ${rapport.temps_vide_pct} % du temps, cadre sous-rempli ${rapport.temps_sous_rempli_pct} % du temps`);
for (const [a, b] of rapport.ecrans_vides) console.log(`  écran vide ${(b - a).toFixed(1)} s à ${mmss(a)} (${a} → ${b})`);
for (const [a, b] of rapport.cadres_sous_remplis) console.log(`  cadre sous-rempli ${(b - a).toFixed(1)} s à ${mmss(a)} (${a} → ${b})`);
if (STRICT && rapport.pire_vide > VIDE_MAX) {
  console.error(`images refusées : ${rapport.pire_vide.toFixed(1)} s d'écran vide d'affilée (${VIDE_MAX} s au plus)`);
  process.exit(1);
}
