/* Motion editorial (v3, 2026-10-05) · primitivas que prendem: a informação se constrói na tela, uma coisa por vez.
   Tudo depende só do tempo
   da timeline (seek-safe). Regra de ouro: UMA propriedade por elemento por vez (nunca anime scale e x no mesmo elemento ao mesmo tempo). */
(function () {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const ease = { o3: (p) => 1 - (1 - p) ** 3, o5: (p) => 1 - (1 - p) ** 5, io: (p) => (p < .5 ? 4 * p ** 3 : 1 - (-2 * p + 2) ** 3 / 2), lin: (p) => p };
  const prog = (t, a, d, e = ease.o3) => e(clamp((t - a) / Math.max(d, 1e-6)));

  // texto que sobe de dentro de uma máscara, palavra por palavra (o .wm corta, o .wi sobe)
  function rise(tl, sel, at, stagger = 0.06, d = 0.55) {
    const W = $$(sel);
    gsap.set(W, { yPercent: 115, rotation: 4 });
    W.forEach((w, i) => tl.to(w, { yPercent: 0, rotation: 0, duration: d, ease: "expo.out" }, at + i * stagger));
    return at + (W.length - 1) * stagger + d;
  }
  // marca-texto que varre a palavra (barra atrás do texto)
  function marker(tl, sel, at, d = 0.45) {
    gsap.set(sel, { scaleX: 0, transformOrigin: "0% 50%" });
    tl.to(sel, { scaleX: 1, duration: d, ease: "expo.inOut" }, at);
  }
  // colchetes de seleção que se encaixam no alvo (4 cantos vindo de fora)
  function brackets(tl, sel, at) {
    const C = $$(sel + " > .c");
    const off = { tl: [-34, -34], tr: [34, -34], bl: [-34, 34], br: [34, 34] };
    C.forEach((c) => { const k = [...c.classList].find((x) => off[x]); gsap.set(c, { x: off[k][0], y: off[k][1], opacity: 0 }); });
    tl.to(C, { x: 0, y: 0, opacity: 1, duration: 0.42, ease: "back.out(2.2)", stagger: 0.03 }, at);
  }
  // card que entra inclinado e borrado e endireita
  function cardIn(tl, sel, at, from = {}) {
    gsap.set(sel, { opacity: 0, y: 140, rotation: -7, rotationX: 24, scale: 0.9, filter: "blur(10px)", transformPerspective: 1600, ...from });
    tl.to(sel, { opacity: 1, y: 0, rotation: 0, rotationX: 0, scale: 1, filter: "blur(0px)", duration: 0.8, ease: "expo.out" }, at);
  }
  // adesivo/selo que pula torto
  function pop(tl, sel, at, rot = -6) {
    gsap.set(sel, { opacity: 0, scale: 0.2, rotation: rot - 25 });
    tl.to(sel, { opacity: 1, scale: 1, rotation: rot, duration: 0.5, ease: "back.out(3)" }, at);
  }
  // carimbo: cai grande, bate e fica; círculo desenhado em volta
  function stamp(tl, sel, at, circle) {
    gsap.set(sel, { opacity: 0, scale: 2.4, rotation: -14 });
    tl.to(sel, { opacity: 1, scale: 1, rotation: -6, duration: 0.28, ease: "power4.in" }, at);
    if (circle) { gsap.set(circle, { strokeDasharray: 2400, strokeDashoffset: 2400 }); tl.to(circle, { strokeDashoffset: 0, duration: 0.7, ease: "expo.out" }, at + 0.2); }
  }
  // traço SVG desenhado (sublinhado, anel de progresso)
  function draw(tl, sel, at, d = 0.6, len = 1200) {
    gsap.set(sel, { strokeDasharray: len, strokeDashoffset: len });
    tl.to(sel, { strokeDashoffset: 0, duration: d, ease: "expo.inOut" }, at);
  }
  // câmera do "mundo": vai até a célula (col, lin) com blur de movimento no meio do caminho
  function pan(tl, world, at, x, y, s = 1, d = 0.8) {
    tl.to(world, { x, y, scale: s, duration: d, ease: "expo.inOut" }, at)
      .fromTo(world, { filter: "blur(0px)" }, { filter: "blur(7px)", duration: d / 2, yoyo: true, repeat: 1, ease: "sine.inOut", immediateRender: false }, at);
  }
  // transição de pinceladas líquidas . angle define de onde vem: −9 esquerda,
  // 171 direita, −78 de baixo, 102 de cima (varie a cada troca): a cor da cena de destino varre a tela em
  // faixas arredondadas e inclinadas, com traços de ataque finos na frente e respingos; quando cobre tudo, a cena troca por
  // baixo (fundo da cena nova = main) e a camada some. Cores vêm das cenas; o estilo é o que importa.
  let smearN = 0;
  function smear(tl, at, { main, lead, from, dur = 0.55, angle = -9, seed = 7 } = {}) {
    let s = seed + smearN * 101;
    const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    const L = document.createElement("div");
    L.className = "smear";
    L.id = "smear" + smearN++;
    L.style.cssText = `position:absolute;left:-960px;top:-540px;width:3000px;height:3000px;transform:rotate(${angle}deg);z-index:45;pointer-events:none;display:none`;
    const pill = (y, h, w, color) => {
      const p = document.createElement("i");
      p.style.cssText = `position:absolute;left:0;top:${y}px;width:${w}px;height:${h}px;border-radius:${h}px;background:${color};display:block`;
      L.appendChild(p);
      return p;
    };
    const rows = [];
    for (let y = -60; y < 3060; y += 120) rows.push([pill(y, 150 + rnd() * 90, 3700, main), rnd()]);
    const leads = [], drops = [];
    for (let y = 0; y < 3000; y += 170) {
      leads.push([pill(y + rnd() * 80, 26 + rnd() * 50, 500 + rnd() * 700, lead || main), rnd()]);
      if (rnd() > 0.35) drops.push([pill(y + 60 + rnd() * 60, 12 + rnd() * 14, 60 + rnd() * 160, main), rnd()]);
    }
    // respingos da cor anterior saindo pela direita depois da troca 
    const tails = [];
    if (from) {
      const T2 = document.createElement("div");
      T2.style.cssText = L.style.cssText.replace("z-index:45", "z-index:44");
      for (let y = 40; y < 3000; y += 210) if (rnd() > 0.3) { const p = document.createElement("i"); const h = 10 + rnd() * 22;
        p.style.cssText = `position:absolute;left:0;top:${y + rnd() * 90}px;width:${80 + rnd() * 260}px;height:${h}px;border-radius:${h}px;background:${from};display:block`; T2.appendChild(p); tails.push([p, rnd()]); }
      document.getElementById("stage").appendChild(T2);
      tl.set(T2, { display: "block" }, at + dur).set(T2, { display: "none" }, at + dur + 0.5);
      tails.forEach(([p, r]) => { gsap.set(p, { x: 400 + r * 900 }); tl.to(p, { x: 3300, duration: 0.3 + 0.2 * r, ease: "power2.in" }, at + dur); });
    }
    document.getElementById("stage").appendChild(L);
    tl.set(L, { display: "block" }, at).set(L, { display: "none" }, at + dur + 0.04);
    rows.forEach(([p, r]) => { gsap.set(p, { x: -3800 - r * 500 }); tl.to(p, { x: -340, duration: dur * (0.78 + 0.2 * r), ease: "power3.out" }, at + 0.1 * r); });
    leads.forEach(([p, r]) => { gsap.set(p, { x: -1300 }); tl.to(p, { x: 3200, duration: dur * (0.55 + 0.2 * r), ease: "power1.out" }, at - 0.08 + 0.05 * r); });
    drops.forEach(([p, r]) => { gsap.set(p, { x: -700 }); tl.to(p, { x: 3100, duration: dur * (0.7 + 0.3 * r), ease: "power1.in" }, at + 0.08 * r); });
    return at + dur;   // instante em que a tela está coberta: troque a cena aqui
  }
  // relógio único: contadores, digitação, timecode
  const fx = [];
  const count = (el, a, b, from, to, fmt) => fx.push((t) => { el.textContent = fmt(from + (to - from) * prog(t, a, b - a)); });
  const type = (el, a, b, text) => fx.push((t) => { el.textContent = text.slice(0, Math.round(text.length * prog(t, a, b - a, ease.lin))); });
  const every = (fn) => fx.push(fn);
  function drive(tl, total) {
    const d = { t: 0 };
    tl.to(d, { t: total, duration: total, ease: "none", onUpdate: () => fx.forEach((f) => f(tl.time())) }, 0);
    fx.forEach((f) => f(0));
  }
  window.ED = { $, $$, clamp, ease, prog, rise, marker, brackets, cardIn, pop, stamp, draw, pan, smear, count, type, every, drive };
})();
