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

  function build() {
    var tl = gsap.timeline({ paused: true });

    // ---------------------------------------------------------------- apparitions
    var IN = {
      rise: [{ opacity: 0, y: 26, filter: 'blur(8px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.55, ease: 'power3.out' }],
      big: [{ opacity: 0, scale: 1.3, filter: 'blur(22px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', ease: 'expo.out' }],
      pop: [{ opacity: 0, scale: 0.55, y: 12 }, { opacity: 1, scale: 1, y: 0, duration: 0.5, ease: 'back.out(1.9)' }],
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
        gsap.set(el, { opacity: 0 });
        tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.1, immediateRender: false }, t);
        q('path,rect,circle', el).forEach(function (sh, i) {
          var len = sh.getTotalLength ? sh.getTotalLength() : 600;
          gsap.set(sh, { strokeDasharray: len, strokeDashoffset: len });
          tl.fromTo(sh, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: 0.9, ease: 'power2.inOut', immediateRender: false }, t + i * 0.12);
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
      gsap.set(el, from);
      tl.fromTo(el, from, to, t);
      var o = el.getAttribute('data-o');
      if (o !== null) tl.to(el, { opacity: 0, y: -12, duration: 0.3, ease: 'power1.in', immediateRender: false }, parseFloat(o));
    });

    // ---------------------------------------------------------------- effets nommés
    q('[data-fx="count"]').forEach(function (el) {
      var t = num(el, 'data-t', 0), d = num(el, 'data-d', 1), to = num(el, 'data-to', 0), dec = num(el, 'data-dec', 0);
      var o = { v: 0 };
      el.textContent = fr(0, dec);
      tl.to(o, { v: to, duration: d, ease: 'power2.out', immediateRender: false,
        onUpdate: function () { el.textContent = fr(o.v, dec); } }, t);
    });
    q('[data-fx="popdots"]').forEach(function (svg) {
      var t = num(svg, 'data-t', 0), sp = num(svg, 'data-split', t + 2), acc = num(svg, 'data-acc', sp + 1);
      q('circle', svg).forEach(function (c) {
        var ap = num(c, 'data-ap', 0), dl = num(c, 'data-dl', 0);
        gsap.set(c, { opacity: 0, scale: 0, transformOrigin: '50% 50%' });
        tl.fromTo(c, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2)', immediateRender: false }, t + ap);
        tl.to(c, { x: num(c, 'data-dx', 0), y: num(c, 'data-dy', 0), duration: 0.9, ease: 'power3.inOut', immediateRender: false }, sp + dl);
        if (c.classList.contains('pdR')) tl.to(c, { fill: '#5D68FF', fillOpacity: 1, duration: 0.35, ease: 'none', immediateRender: false }, acc + dl * 0.7);
      });
    });
    q('[data-fx="litdots"]').forEach(function (svg) {
      var t = num(svg, 'data-t', 0), d = num(svg, 'data-d', 1), cs = q('circle', svg), n = cs.length;
      cs.forEach(function (c, i) {
        gsap.set(c, { opacity: 0, scale: 0.2, transformOrigin: '50% 50%' });
        tl.fromTo(c, { opacity: 0, scale: 0.2 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'back.out(2)', immediateRender: false },
          t + (n > 1 ? i / (n - 1) * d * 0.85 : 0));
      });
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

    // ---------------------------------------------------------------- monde nuit : plan incliné, caméra qui descend la feuille
    var nEnd = F.night[1];
    gsap.set('#nplane', { rotationX: 10, rotationZ: -3.2, scale: 0.93 });
    tl.to('#nplane', { rotationX: 6, rotationZ: -1.5, scale: 0.99, duration: nEnd, ease: 'none', immediateRender: false }, 0);
    gsap.set('#ncam', { y: F.ncam[0][1] });
    for (var i = 1; i < F.ncam.length; i++) {
      tl.to('#ncam', { y: F.ncam[i][1], duration: 1.05, ease: 'power3.inOut', immediateRender: false }, F.ncam[i][0]);
    }
    gsap.set('#nhalo', { x: -60, y: 0, scale: 1 });
    tl.to('#nhalo', { x: 80, y: 60, scale: 1.12, duration: F.duration, ease: 'none', immediateRender: false }, 0);

    // ---------------------------------------------------------------- pivot : texte sur le noir, puis pli vers le papier
    fold(tl, '#pvsheet', '#pvflap', '#pvstreak', F.pivot.fold_at);

    // ---------------------------------------------------------------- monde papier : caméra à crans + dérive lente
    var p0 = F.paper[0], p1 = F.paper[1];
    gsap.set('#pworld', { y: F.pcam[0][1] });
    for (var j = 1; j < F.pcam.length; j++) {
      tl.to('#pworld', { y: F.pcam[j][1], duration: 1.0, ease: 'power3.inOut', immediateRender: false }, F.pcam[j][0]);
    }
    gsap.set('#pcam', { y: 0, scale: 1.0, transformOrigin: '50% 40%' });
    tl.to('#pcam', { y: -36, scale: 1.025, duration: p1 - p0, ease: 'none', immediateRender: false }, p0);

    // ---------------------------------------------------------------- fin : le papier se replie, la nuit revient, la promesse, le logo, le clic
    fold(tl, '#psheet', '#pflap', '#pstreak', F.end.fold_at);
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

    // ---------------------------------------------------------------- mots typographiés (pivot, nuance, promesse)
    q('.tw').forEach(function (w) {
      var t = num(w, 'data-t', 0);
      gsap.set(w, { opacity: 0, y: 34, filter: 'blur(10px)' });
      tl.fromTo(w, { opacity: 0, y: 34, filter: 'blur(10px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.5, ease: 'power3.out', immediateRender: false }, t - 0.06);
    });

    // ---------------------------------------------------------------- sous-titres mot à mot, case du mot-clé, trait de pic
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
        var line = pks[0].querySelector('.pkline'), last = pks[pks.length - 1];
        line.style.width = (last.offsetLeft + last.offsetWidth - pks[0].offsetLeft) + 'px';
        gsap.set(line, { scaleX: 0 });
        tl.to(line, { scaleX: 1, duration: 0.5, ease: 'power3.inOut', immediateRender: false }, num(last, 'data-t', 0));
      }
    });

    // ---------------------------------------------------------------- grain vivant (12 positions par seconde)
    var g = document.querySelector('#grain .grainin');
    if (g) tl.to(g, { backgroundPosition: '173px 97px', duration: F.duration, ease: 'steps(' + Math.floor(F.duration * 12) + ')', immediateRender: false }, 0);

    window.__timelines['main'] = tl;
    if (window.__hfForceTimelineRebind) window.__hfForceTimelineRebind();
  }

  if (document.fonts && document.fonts.ready) document.fonts.ready.then(build); else build();
})();
