/* Moteur Papercraft.AI : construit l'unique timeline GSAP (en pause) à partir du DOM statique écrit par build.py.
   Chaque élément porte son apparition (data-a, data-t, data-d, data-o) ou un effet nommé (data-fx).
   Déterministe : aucun hasard, aucune horloge ; tout est placé en temps absolu sur la timeline. */
(function () {
  var F = window.FILM;
  var W = 1080, H = 1350;

  function q(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function num(el, k, d) { var v = el.getAttribute(k); return v === null || v === '' ? d : parseFloat(v); }
  function fr(v, dec) {
    var s = Math.abs(v).toFixed(dec).split('.');
    s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return (v < 0 ? '-' : '') + s.join(',');
  }

  // ------------------------------------------------------------------ pli diagonal (coin haut droit -> bas gauche)
  var L = Math.sqrt(W * W + H * H), VX = -W / L, VY = H / L, ANG = Math.atan2(-VX, VY) * 180 / Math.PI;
  var RECT = [[0, 0], [W, 0], [W, H], [0, H]];
  function dist(p) { return (p[0] - W) * VX + p[1] * VY; }
  function half(poly, s, keepFar) {
    var out = [];
    for (var i = 0; i < poly.length; i++) {
      var a = poly[i], b = poly[(i + 1) % poly.length];
      var da = dist(a) - s, db = dist(b) - s;
      var ia = keepFar ? da >= 0 : da < 0, ib = keepFar ? db >= 0 : db < 0;
      if (ia) out.push(a);
      if (ia !== ib) { var t = da / (da - db); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
    }
    return out;
  }
  function mirror(p, s) { var d = dist(p) - s; return [p[0] - 2 * d * VX, p[1] - 2 * d * VY]; }
  function css(poly) {
    if (poly.length < 3) return 'polygon(0px 0px,0px 0px,0px 0px)';
    return 'polygon(' + poly.map(function (p) { return p[0].toFixed(1) + 'px ' + p[1].toFixed(1) + 'px'; }).join(',') + ')';
  }
  function foldRender(sheet, flap, streak, s) {
    sheet.style.clipPath = css(half(RECT, s, true));
    flap.style.clipPath = css(half(RECT, s, false).map(function (p) { return mirror(p, s); }));
    streak.style.transform = 'translate(' + (W + s * VX).toFixed(1) + 'px,' + (s * VY).toFixed(1) + 'px) rotate(' + ANG.toFixed(2) + 'deg)';
  }
  function fold(tl, sheetSel, flapSel, streakSel, t) {
    var sheet = document.querySelector(sheetSel), flap = document.querySelector(flapSel), streak = document.querySelector(streakSel);
    var o = { s: 0 };
    foldRender(sheet, flap, streak, 0);
    tl.fromTo(o, { s: 0 }, { s: L + 40, duration: F.fold, ease: 'power1.inOut', immediateRender: false,
      onUpdate: function () { foldRender(sheet, flap, streak, o.s); } }, t);
    gsap.set(streak, { opacity: 0 });
    tl.fromTo(streak, { opacity: 0 }, { opacity: 1, duration: 0.12, ease: 'none', immediateRender: false }, t);
    tl.to(streak, { opacity: 0, duration: 0.25, ease: 'power1.in', immediateRender: false }, t + F.fold - 0.25);
  }

  // chaque bloc est isolé : une erreur est journalisée (console + window.__moteurErreurs) sans empêcher les autres blocs
  // ni l'enregistrement de la timeline ; le contrôle d'après build.py échoue si la liste n'est pas vide
  window.__moteurErreurs = [];
  function bloc(nom, fn) {
    try { fn(); } catch (e) {
      window.__moteurErreurs.push(nom + ' : ' + (e && e.message ? e.message : e));
      console.error('[moteur] bloc « ' + nom + ' » en erreur : ' + (e && e.stack ? e.stack : e));
    }
  }

  function build() {
    var tl;
    try { tl = gsap.timeline({ paused: true }); } catch (e) {
      window.__moteurErreurs.push('timeline : ' + e.message);
      console.error('[moteur] timeline impossible à créer : ' + e.stack);
      tl = { paused: true, duration: function () { return F ? F.duration : 0; } };
    }

    // ---------------------------------------------------------------- apparitions
    bloc('apparitions', function () {
      var IN = {
        rise: [{ opacity: 0, y: 26, filter: 'blur(8px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.55, ease: 'power3.out' }],
        big: [{ opacity: 0, scale: 1.3, filter: 'blur(22px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', ease: 'expo.out' }],
        pop: [{ opacity: 0, scale: 0.9, y: 12 }, { opacity: 1, scale: 1, y: 0, duration: 0.45, ease: 'power3.out' }],
        print: [{ opacity: 0, y: 10, filter: 'blur(3px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4, ease: 'power2.out' }],
        up: [{ opacity: 0, scaleY: 0, transformOrigin: '50% 100%' }, { opacity: 1, scaleY: 1, duration: 0.32, ease: 'power2.out' }],
        hingeT: [{ opacity: 0, rotationX: -90, transformPerspective: 900, transformOrigin: '50% 0%' }, { opacity: 1, rotationX: 0, duration: 0.55, ease: 'power3.out' }],
        hingeB: [{ opacity: 0, rotationX: -90, transformPerspective: 900, transformOrigin: '50% 100%' }, { opacity: 1, rotationX: 0, duration: 0.75, ease: 'power3.out' }],
        growc: [{ scaleX: 0, transformOrigin: '50% 50%' }, { scaleX: 1, duration: 0.6, ease: 'power3.out' }],
        fill: [{ scaleX: 0, transformOrigin: '0% 50%' }, { scaleX: 1, duration: 0.9, ease: 'power2.out' }],
        lock: [{ opacity: 0, scale: 1.7, transformOrigin: '50% 50%' }, { opacity: 1, scale: 1, duration: 0.4, ease: 'power3.out' }],
        drop: [{ opacity: 0, y: -60, scaleX: 2.2, transformOrigin: '50% 50%' }, { opacity: 1, y: 0, scaleX: 1, duration: 0.55, ease: 'power3.in' }],
        step: [{ opacity: 0, y: 0 }, { opacity: 1, y: -34, duration: 0.6, ease: 'power3.out' }],
        fade: [{ opacity: 0 }, { opacity: 1, duration: 0.5, ease: 'power1.out' }],
        wipe: [{ scaleX: 0, transformOrigin: '0% 50%' }, { scaleX: 1, duration: 0.7, ease: 'power3.inOut' }],
        grow: [{ scaleY: 0, transformOrigin: '50% 0%' }, { scaleY: 1, duration: 0.45, ease: 'power2.inOut' }],
        growx: [{ scaleX: 0, transformOrigin: '0% 50%' }, { scaleX: 1, duration: 0.5, ease: 'power2.inOut' }],
        growup: [{ scaleY: 0, transformOrigin: '50% 100%' }, { scaleY: 1, duration: 0.9, ease: 'power3.out' }],
        slideL: [{ opacity: 0, x: -170 }, { opacity: 1, x: 0, duration: 0.75, ease: 'power3.out' }],
        slideR: [{ opacity: 0, x: 170 }, { opacity: 1, x: 0, duration: 0.75, ease: 'power3.out' }]
      };
      q('[data-a]').forEach(function (el) {
        var a = el.getAttribute('data-a'), t = num(el, 'data-t', 0);
        if (a === 'draw') {
          // trait révélé par son tiret ; le tiret dépasse la longueur (pas de point d'extrémité visible avant le tracé)
          var dd = num(el, 'data-d', 0.9), stg = num(el, 'data-stg', 0.12), ez = el.getAttribute('data-ease') || 'power2.inOut';
          gsap.set(el, { opacity: 0 });
          tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.1, immediateRender: false }, t);
          q('path,rect,circle,polyline,line', el).forEach(function (sh, i) {
            if (!sh.getAttribute('stroke') && !(el.classList.contains('ico'))) return;
            var len = sh.getTotalLength ? sh.getTotalLength() : 600;
            gsap.set(sh, { strokeDasharray: len + ' ' + (len + 12), strokeDashoffset: len + 6 });
            tl.fromTo(sh, { strokeDashoffset: len + 6 }, { strokeDashoffset: 0, duration: dd, ease: ez, immediateRender: false }, t + i * stg);
          });
          return;
        }
        var spec = IN[a];
        if (!spec) return;
        var from = Object.assign({}, spec[0]), to = Object.assign({}, spec[1], { immediateRender: false });
        if (a === 'big') {
          to.duration = num(el, 'data-d', 0.8);
          from.transformOrigin = el.classList.contains('center') || el.classList.contains('wordmark') ? '50% 60%' : '0% 70%';
        }
        if (a === 'pop' || a === 'step') from.transformOrigin = '50% 100%';
        if (a === 'pop' && el.classList.contains('cipt')) from.transformOrigin = '50% 50%';
        gsap.set(el, from);
        tl.fromTo(el, from, to, t);
        var o = el.getAttribute('data-o');
        if (o !== null) tl.to(el, { opacity: 0, y: -12, duration: 0.3, ease: 'power1.in', immediateRender: false }, parseFloat(o));
      });
    });

    // ---------------------------------------------------------------- effets nommés
    bloc('effets', function () {
      q('[data-fx="count"]').forEach(function (el) {
        var t = num(el, 'data-t', 0), d = num(el, 'data-d', 1), to = num(el, 'data-to', 0), dec = num(el, 'data-dec', 0);
        var pre = el.getAttribute('data-pre') || '';
        var o = { v: 0 };
        el.textContent = pre + fr(0, dec);
        tl.to(o, { v: to, duration: d, ease: 'power2.out', immediateRender: false,
          onUpdate: function () { el.textContent = pre + fr(o.v, dec); } }, t);
      });
      // silhouettes ou points qui se lèvent, puis rejoignent leur groupe ; le groupe IA passe au carbone
      q('[data-fx="split"]').forEach(function (el) {
        var t = num(el, 'data-t', 0), mt = num(el, 'data-mt', -1), ct = num(el, 'data-ct', -1);
        var dot = el.getAttribute('data-in') === 'dot';
        var from = dot ? { opacity: 0, scale: 0, transformOrigin: '50% 50%' } : { opacity: 0, scaleY: 0, transformOrigin: '50% 100%' };
        var to = dot ? { opacity: 1, scale: 1, duration: 0.3, ease: 'power2.out', immediateRender: false } : { opacity: 1, scaleY: 1, duration: 0.32, ease: 'power2.out', immediateRender: false };
        gsap.set(el, from);
        tl.fromTo(el, from, to, t);
        if (mt >= 0) tl.to(el, { x: num(el, 'data-dx', 0), y: num(el, 'data-dy', 0), duration: 0.7, ease: 'power3.inOut', immediateRender: false }, mt);
        if (ct >= 0) tl.to(el, dot ? { backgroundColor: '#5D68FF', duration: 0.3, immediateRender: false } : { color: '#5D68FF', duration: 0.3, immediateRender: false }, ct);
      });
      // points qui arrivent d'un peu partout et se rangent (flux)
      q('[data-fx="flydots"]').forEach(function (svg) {
        var t = num(svg, 'data-t', 0);
        q('circle', svg).forEach(function (c) {
          var from = { x: num(c, 'data-fx0', 0), y: num(c, 'data-fy0', 0), opacity: 0 };
          gsap.set(c, from);
          tl.fromTo(c, from, { x: 0, y: 0, opacity: 1, duration: 0.8, ease: 'power3.out', immediateRender: false }, t + num(c, 'data-ap', 0));
        });
      });
      // bande de balayage (horizontale ou verticale) qui traverse son cadre une fois
      q('[data-fx="band"]').forEach(function (el) {
        var t = num(el, 'data-t', 0), d = num(el, 'data-d', 1);
        var from = { opacity: 0 }, to = { duration: d, ease: 'none', immediateRender: false };
        if (el.hasAttribute('data-y0')) { from.y = num(el, 'data-y0', 0); to.y = num(el, 'data-y1', 0); }
        if (el.hasAttribute('data-x0')) { from.x = num(el, 'data-x0', 0); to.x = num(el, 'data-x1', 0); }
        gsap.set(el, from);
        tl.fromTo(el, from, to, t);
        tl.to(el, { opacity: 1, duration: 0.12, ease: 'none', immediateRender: false }, t);
        tl.to(el, { opacity: 0, duration: 0.2, ease: 'none', immediateRender: false }, t + d - 0.2);
      });
      // onde de la voix : chaque barre suit des images clés tirées d'une graine fixe (build.py)
      q('[data-fx="wave"]').forEach(function (el) {
        var t = num(el, 'data-t', 0), d = num(el, 'data-d', 1), ap = num(el, 'data-ap', t - 0.3);
        var ks = (el.getAttribute('data-k') || '0.1').split(',').map(parseFloat);
        gsap.set(el, { opacity: 0, scaleY: 0.1 });
        tl.to(el, { opacity: 1, duration: 0.2, immediateRender: false }, ap);
        tl.to(el, { keyframes: { scaleY: ks }, duration: d, ease: 'none', immediateRender: false }, t);
      });
      q('[data-fx="pulse"]').forEach(function (el) {
        tl.to(el, { scale: 1.35, duration: 0.3, ease: 'sine.inOut', yoyo: true, repeat: 5, immediateRender: false }, num(el, 'data-fxt', 0));
      });
      q('[data-fx="typing"]').forEach(function (el) {
        tl.to(el, { y: -8, duration: 0.18, ease: 'sine.inOut', yoyo: true, repeat: 3, immediateRender: false }, num(el, 'data-t', 0));
      });
      // changements d'état (grille diagnostique) : [[t, fond, ombre intérieure], ...]
      q('[data-tint]').forEach(function (el) {
        JSON.parse(el.getAttribute('data-tint') || '[]').forEach(function (k) {
          tl.to(el, { backgroundColor: k[1], boxShadow: k[2], duration: 0.2, ease: 'none', immediateRender: false }, k[0]);
        });
      });
      q('[data-fx="popdots"]').forEach(function (svg) {
        var t = num(svg, 'data-t', 0), sp = num(svg, 'data-split', t + 2), acc = num(svg, 'data-acc', sp + 1);
        q('circle', svg).forEach(function (c) {
          var ap = num(c, 'data-ap', 0), dl = num(c, 'data-dl', 0);
          gsap.set(c, { opacity: 0, scale: 0, transformOrigin: '50% 50%' });
          tl.fromTo(c, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'power2.out', immediateRender: false }, t + ap);
          tl.to(c, { x: num(c, 'data-dx', 0), y: num(c, 'data-dy', 0), duration: 0.9, ease: 'power3.inOut', immediateRender: false }, sp + dl);
          if (c.classList.contains('pdR')) tl.to(c, { fill: '#5D68FF', fillOpacity: 1, duration: 0.35, ease: 'none', immediateRender: false }, acc + dl * 0.7);
        });
      });
      q('[data-fx="litdots"]').forEach(function (svg) {
        var t = num(svg, 'data-t', 0), d = num(svg, 'data-d', 1), cs = q('circle', svg), n = cs.length;
        cs.forEach(function (c, i) {
          gsap.set(c, { opacity: 0, scale: 0.2, transformOrigin: '50% 50%' });
          tl.fromTo(c, { opacity: 0, scale: 0.2 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'power2.out', immediateRender: false },
            t + (n > 1 ? i / (n - 1) * d * 0.85 : 0));
        });
      });
      q('[data-fx="ring"]').forEach(function (el) {
        var t = num(el, 'data-t', 0), d = num(el, 'data-d', 1.1), off = num(el, 'data-off', 0);
        tl.to(el, { strokeDashoffset: off, duration: d, ease: 'power2.out', immediateRender: false }, t);
      });
      q('[data-fx="scan"]').forEach(function (el) {
        var t = num(el, 'data-t', 0), d = num(el, 'data-d', 1.5), dy = num(el, 'data-dy', 160);
        gsap.set(el, { opacity: 0, y: 0 });
        tl.to(el, { opacity: 1, duration: 0.15, ease: 'none', immediateRender: false }, t);
        tl.fromTo(el, { y: 0 }, { y: dy, duration: d / 2, ease: 'sine.inOut', yoyo: true, repeat: 1, immediateRender: false }, t);
        tl.to(el, { opacity: 0, duration: 0.25, ease: 'power1.in', immediateRender: false }, t + d);
      });
      q('[data-fx="spin"]').forEach(function (el) {
        tl.fromTo(el, { rotation: 0 }, { rotation: 1080, duration: num(el, 'data-d', 2), ease: 'power1.inOut', transformOrigin: '50% 100%', immediateRender: false }, num(el, 'data-t', 0));
      });
      q('[data-fx="spin2"]').forEach(function (el) {
        tl.fromTo(el, { rotation: 0 }, { rotation: 90, duration: num(el, 'data-d', 2), ease: 'power1.inOut', transformOrigin: '50% 100%', immediateRender: false }, num(el, 'data-t', 0));
      });
      q('[data-fx="buzz"]').forEach(function (el) {
        var t = num(el, 'data-fxt', 0);
        [0, 0.9].forEach(function (k) {
          tl.to(el, { keyframes: { x: [0, -8, 8, -7, 7, -5, 5, -2, 0] }, duration: 0.55, ease: 'none', immediateRender: false }, t + k);
        });
      });
      q('[data-fx="wait"]').forEach(function (el) {
        tl.to(el, { keyframes: { rotation: [0, -4, 0, 4, 0] }, transformOrigin: '50% 100%', duration: 2.2, ease: 'sine.inOut', immediateRender: false }, num(el, 'data-fxt', 0));
      });
      q('[data-fx="walk"]').forEach(function (el) {
        var t = num(el, 'data-fxt', 0), d = num(el, 'data-d', 1.4), dx = num(el, 'data-dx', 600);
        tl.to(el, { x: dx, duration: d, ease: 'power1.inOut', immediateRender: false }, t);
        tl.to(el, { keyframes: { y: [0, -9, 0, -9, 0, -9, 0] }, duration: d, ease: 'none', immediateRender: false }, t);
        tl.to(el, { opacity: 0, duration: 0.3, ease: 'power1.in', immediateRender: false }, t + d - 0.25);
      });
    });

    // ---------------------------------------------------------------- monde nuit : plan incliné, caméra qui descend la feuille
    bloc('caméras (nuit)', function () {
      var nEnd = F.night[1];
      gsap.set('#nplane', { rotationX: 10, rotationZ: -3.2, scale: 0.93 });
      tl.to('#nplane', { rotationX: 6, rotationZ: -1.5, scale: 0.99, duration: nEnd, ease: 'none', immediateRender: false }, 0);
      gsap.set('#ncam', { y: F.ncam[0][1] });
      for (var i = 1; i < F.ncam.length; i++) {
        tl.to('#ncam', { y: F.ncam[i][1], duration: 1.05, ease: 'power3.inOut', immediateRender: false }, F.ncam[i][0]);
      }
      gsap.set('#nhalo', { x: -60, y: 0, scale: 1 });
      tl.to('#nhalo', { x: 80, y: 60, scale: 1.12, duration: F.duration, ease: 'none', immediateRender: false }, 0);
    });

    // ---------------------------------------------------------------- pivot : texte sur le noir, puis pli vers le papier
    bloc('plis (pivot)', function () { fold(tl, '#pvsheet', '#pvflap', '#pvstreak', F.pivot.fold_at); });

    // ---------------------------------------------------------------- monde papier : caméra à crans + dérive lente
    bloc('caméras (papier)', function () {
      var p0 = F.paper[0], p1 = F.paper[1];
      gsap.set('#pworld', { y: F.pcam[0][1] });
      for (var j = 1; j < F.pcam.length; j++) {
        if (F.pcam[j][2] === 'set') tl.set('#pworld', { y: F.pcam[j][1] }, F.pcam[j][0] - 0.02);
        else tl.to('#pworld', { y: F.pcam[j][1], duration: 1.0, ease: 'power3.inOut', immediateRender: false }, F.pcam[j][0]);
      }
      gsap.set('#pcam', { y: 0, scale: 1.0, transformOrigin: '50% 50%' });
      tl.to('#pcam', { y: -10, scale: 1.015, duration: p1 - p0, ease: 'none', immediateRender: false }, p0);
    });

    // ---------------------------------------------------------------- lumière qui glisse sur le papier : le monde respire toujours
    // (sans elle, une planche posée est une image figée que le contrôle de fabrication refuse)
    bloc('lumière', function () {
      [['#plight', F.paper[0], F.paper[1]], ['#vlight', F.paper[0], F.paper[1]], ['#pvlight', F.pivot.start, F.pivot.fold_at + F.fold]].forEach(function (L) {
        if (!document.querySelector(L[0])) return;
        var d = Math.max(1, L[2] - L[1]), per = 6.5, n = Math.max(0, Math.ceil(d / per) - 1);
        gsap.set(L[0], { x: -240, y: -60 });
        tl.fromTo(L[0], { x: -240, y: -60 }, { x: 260, y: 140, duration: per, ease: 'sine.inOut', yoyo: true, repeat: n, immediateRender: false }, L[1]);
      });
    });

    // ---------------------------------------------------------------- déchirure : la planche se déchire et révèle le verso (la nuance)
    bloc('déchirure', function () {
      var T = F.tear;
      if (!T) return;
      var a = T.at;
      gsap.set(['#tearT', '#tearB', '#verso'], { autoAlpha: 0 });
      tl.set(['#tearT', '#tearB', '#verso'], { autoAlpha: 1 }, a);
      tl.fromTo('#tearT', { y: 0, rotation: 0, transformOrigin: '0% 100%' }, { y: -10, rotation: -0.8, duration: 0.25, ease: 'power1.out', immediateRender: false }, a);
      tl.to('#tearT', { y: -1000, rotation: -9, duration: 0.8, ease: 'power3.in', immediateRender: false }, a + 0.25);
      tl.fromTo('#tearB', { y: 0, rotation: 0, transformOrigin: '100% 0%' }, { y: 6, rotation: 0.5, duration: 0.25, ease: 'power1.out', immediateRender: false }, a);
      tl.to('#tearB', { y: 1100, rotation: 6, duration: 0.85, ease: 'power3.in', immediateRender: false }, a + 0.25);
      tl.set(['#tearT', '#tearB'], { autoAlpha: 0 }, a + 1.15);
      if (T.out) tl.to('#verso', { y: -1350, duration: 1.0, ease: 'power3.inOut', immediateRender: false }, T.out);
    });

    // ---------------------------------------------------------------- fin : le papier se replie, la nuit revient, la promesse, le logo, le clic
    bloc('plis (fin)', function () { fold(tl, '#psheet', '#pflap', '#pstreak', F.end.fold_at); });
    bloc('fin', function () {
      var e0 = F.end.start;
      q('#glyph path').forEach(function (p, k) {
        var len = p.getTotalLength();
        gsap.set(p, { strokeDasharray: len, strokeDashoffset: len });
        tl.fromTo(p, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: k === 0 ? 1.0 : 0.5, ease: 'power2.inOut', immediateRender: false },
          e0 + 0.45 + [0, 0.75, 1.05][k]);
      });
      gsap.set('#ehalo', { scale: 0.9, opacity: 0.6 });
      tl.to('#ehalo', { scale: 1.1, opacity: 1, duration: F.duration - e0, ease: 'sine.inOut', immediateRender: false }, e0);

      var btnAt = F.end.button_at, ck = F.end.click_at;
      gsap.set('#cursor', { x: 760, y: 1010, opacity: 0, scale: 1, transformOrigin: '10% 5%' });
      tl.to('#cursor', { opacity: 1, duration: 0.25, immediateRender: false }, btnAt + 0.15);
      tl.to('#cursor', { x: 556, y: 836, duration: ck - btnAt - 0.25, ease: 'power2.inOut', immediateRender: false }, btnAt + 0.2);
      tl.to('#cursor', { keyframes: { scale: [1, 0.82, 1] }, duration: 0.3, ease: 'none', immediateRender: false }, ck - 0.05);
      tl.to('#cursor', { x: 640, y: 930, opacity: 0, duration: 0.6, ease: 'power2.in', immediateRender: false }, ck + 0.9);
      gsap.set('#ripple', { scale: 0.3, opacity: 0 });
      tl.fromTo('#ripple', { scale: 0.3, opacity: 0.9 }, { scale: 1.7, opacity: 0, duration: 0.7, ease: 'power2.out', immediateRender: false }, ck);
      tl.to('#btn', { backgroundColor: '#5D68FF', duration: 0.2, ease: 'none', immediateRender: false }, ck + 0.05);
      tl.to('#btnlabel', { opacity: 0, y: -16, duration: 0.2, immediateRender: false }, ck + 0.05);
      gsap.set('#btnok', { opacity: 0, y: 16 });
      tl.to('#btnok', { opacity: 1, y: 0, duration: 0.3, ease: 'back.out(2)', immediateRender: false }, ck + 0.12);
    });

    // ---------------------------------------------------------------- mots typographiés (pivot, nuance, promesse)
    bloc('mots', function () {
      q('.tw').forEach(function (w) {
        var t = num(w, 'data-t', 0);
        gsap.set(w, { opacity: 0, y: 34, filter: 'blur(10px)' });
        tl.fromTo(w, { opacity: 0, y: 34, filter: 'blur(10px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.5, ease: 'power3.out', immediateRender: false }, t - 0.06);
      });
    });

    // ---------------------------------------------------------------- sous-titres mot à mot, case du mot-clé, trait de pic
    bloc('sous-titres', function () {
      q('.chunk').forEach(function (ch) {
        var tin = num(ch, 'data-in', 0), tout = num(ch, 'data-out', tin + 2);
        gsap.set(ch, { opacity: 0 });
        tl.fromTo(ch, { opacity: 0 }, { opacity: 1, duration: 0.06, ease: 'none', immediateRender: false }, tin - 0.08);
        tl.to(ch, { opacity: 0, duration: 0.12, ease: 'power1.in', immediateRender: false }, tout);
        q('.w', ch).forEach(function (w) {
          var t = num(w, 'data-t', 0);
          gsap.set(w, { opacity: 0, y: 10, filter: 'blur(5px)' });
          tl.fromTo(w, { opacity: 0, y: 10, filter: 'blur(5px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.2, ease: 'power2.out', immediateRender: false }, t - 0.06);
          var bx = w.querySelector('.bx');
          if (bx) {
            gsap.set(bx, { scaleX: 0 });
            tl.to(bx, { scaleX: 1, duration: 0.22, ease: 'power3.out', immediateRender: false }, t - 0.04);
          }
        });
        var pks = q('.pk', ch);
        if (pks.length) {
          var line = ch.querySelector('.pkline'), last = pks[pks.length - 1];
          if (!line) return;
          line.style.width = (last.offsetLeft + last.offsetWidth - pks[0].offsetLeft) + 'px';
          gsap.set(line, { scaleX: 0 });
          tl.to(line, { scaleX: 1, duration: 0.5, ease: 'power3.inOut', immediateRender: false }, num(last, 'data-t', 0));
        }
      });
    });

    // ---------------------------------------------------------------- grain vivant (12 positions par seconde)
    bloc('grain', function () {
      var g = document.querySelector('#grain .grainin');
      if (g) tl.to(g, { backgroundPosition: '173px 97px', duration: F.duration, ease: 'steps(' + Math.floor(F.duration * 12) + ')', immediateRender: false }, 0);
    });

    // toujours enregistrée, même si un bloc a échoué : sinon le rendu attend 45 s puis sort une vidéo sans animation
    window.__timelines = window.__timelines || {};
    window.__timelines['main'] = tl;
    try { if (window.__hfForceTimelineRebind) window.__hfForceTimelineRebind(); } catch (e) { console.error('[moteur] rebind : ' + e.stack); }
  }

  function lancer() {
    try { build(); } catch (e) {
      window.__moteurErreurs.push('build : ' + e.message);
      console.error('[moteur] build en erreur : ' + e.stack);
    }
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(lancer, lancer); else lancer();
})();
