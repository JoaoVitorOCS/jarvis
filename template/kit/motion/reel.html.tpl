<!doctype html>
<!-- Gerado por kit/motion/montar_reel.py (não edite o index.html à mão: edite o reel.json e rode de novo). -->
<html lang="pt-BR" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    __FONTS__
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: __BG__; }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: __BG__; font-family: '__F_TEXTO__', sans-serif; }
      .layer { position: absolute; inset: 0; overflow: hidden; }
      .dark { background: __BG__; color: __INK__; --mk: __ACC__; --mkt: __ACC_INK__; background-image: radial-gradient(rgba(128,128,128,.10) 2px, transparent 2.5px); background-size: 34px 34px; }
      .light { background: __CBG__; color: __CINK__; --mk: __CACC__; --mkt: #FFFFFF; background-image: radial-gradient(rgba(128,128,128,.12) 2px, transparent 2.5px); background-size: 34px 34px; }
      .h { position: absolute; left: 80px; right: 60px; top: 330px; font-family: '__F_TITULO__', sans-serif; font-weight: 700; font-size: 104px; line-height: 1.04; letter-spacing: -0.035em; }
      .wm { display: inline-block; overflow: hidden; vertical-align: top; padding: 0 0 .1em; margin-bottom: -.1em; }
      .wi { display: inline-block; }
      .acc { position: relative; display: inline-block; isolation: isolate; font-family: '__F_DESTAQUE__', serif; font-style: italic; font-weight: 400; font-size: 1.12em; letter-spacing: 0; color: var(--mkt); padding: 0 .12em; }
      .acc .mk { position: absolute; left: 0; right: 0; top: 14%; bottom: 2%; background: var(--mk); z-index: -1; border-radius: 6px; }
      #sub { position: absolute; left: 80px; right: 80px; top: 1200px; font-size: 52px; line-height: 1.2; font-weight: 700; letter-spacing: -0.02em; opacity: .85; }
      #bar1 { position: absolute; left: 80px; top: 1130px; width: 220px; height: 12px; border-radius: 6px; background: var(--mk); transform-origin: 0 50%; }
      #tw { position: absolute; left: 0; top: 0; height: 1920px; }
      .tc { position: absolute; top: 0; width: 1080px; height: 1920px; }
      .eyebrow { position: absolute; left: 80px; top: 260px; font-family: '__F_MONO__', monospace; font-size: 28px; letter-spacing: .12em; text-transform: uppercase; opacity: .8; z-index: 5; }
      #tdots { position: absolute; left: 80px; top: 320px; display: flex; gap: 14px; z-index: 5; }
      #tdots i { width: 60px; height: 10px; border-radius: 5px; background: rgba(128,128,128,.35); display: block; }
      #tdots i.on { background: var(--mk); }
      .repo { position: absolute; top: 700px; width: 920px; border-radius: 34px; padding: 50px 54px 60px; border: 3px solid rgba(128,128,128,.4); }
      .rk { font-family: '__F_MONO__', monospace; font-size: 28px; letter-spacing: .12em; text-transform: uppercase; opacity: .6; }
      .rn { font-family: '__F_TITULO__', sans-serif; font-weight: 700; font-size: 76px; line-height: 1.05; margin-top: 40px; letter-spacing: -0.03em; word-break: break-word; }
      .rd { font-weight: 700; font-size: 50px; line-height: 1.16; letter-spacing: -0.02em; margin-top: 30px; }
      .rs { font-family: '__F_TITULO__', sans-serif; font-weight: 700; font-size: 84px; margin-top: 40px; letter-spacing: -0.03em; }
      .ru { margin-top: 30px; font-family: '__F_MONO__', monospace; font-size: 32px; line-height: 1.35; padding: 18px 22px; border-radius: 14px; background: rgba(128,128,128,.14); }
      #ha { top: 600px; text-align: center; left: 60px; right: 60px; font-size: 100px; }
      #cta { position: absolute; left: 0; top: 1180px; width: 1080px; text-align: center; }
      .btn { display: inline-flex; align-items: center; gap: 18px; font-weight: 700; font-size: 52px; padding: 26px 70px; border-radius: 999px; background: var(--mk); color: var(--mkt); }
      #lockup { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 55; opacity: 0; background: __BG__; color: __INK__; }
      #lname { font-family: '__F_TITULO__', sans-serif; font-weight: 700; font-size: 92px; letter-spacing: -0.03em; display: flex; }
      #lname span { display: inline-block; } #lname .sp { width: 28px; }
      #cursor { position: absolute; left: 0; top: 0; width: 70px; height: 70px; z-index: 60; opacity: 0; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__TOTAL__" data-width="1080" data-height="1920">
      <div id="stage" class="clip" data-start="0" data-duration="__TOTAL__" data-track-index="0">
        <section class="layer dark" id="L1">
          <div class="h" id="h1">__H1__</div>
          <i id="bar1"></i>
          <div id="sub"><span id="subt"></span></div>
        </section>
        <section class="layer dark" id="L2">
          <div id="tw">__CELLS__
__CARDS__
          </div>
          <div class="eyebrow" id="tey"></div>
          <div id="tdots"></div>
        </section>
        <section class="layer light" id="L3">
          <div class="h" id="ha">__HA__</div>
          <div id="cta"><span class="btn" id="btn"><span id="btxt">__BTN__</span></span></div>
        </section>
        <div id="lockup"><div id="lname"></div></div>
        <svg id="cursor" viewBox="0 0 32 32"><path d="M6 3 L6 25 L12 19.5 L16 28 L19.5 26.4 L15.6 18 L23 18 Z" fill="#F5F5F5" stroke="#111111" stroke-width="1.6" stroke-linejoin="round"/></svg>
      </div>
      __AUDIO__
    </div>
    <script src="ed.js"></script>
    <script>
      const T = __T__, N = __N__, THEMES = __THEMES__, SUB = __SUB_JS__, NOME = __NOME__;
      const { $, $$, rise, marker, pop, count, type } = ED;
      const tl = gsap.timeline({ paused: true });
      const LAY = ["#L1", "#L2", "#L3"];
      gsap.set(LAY.slice(1), { visibility: "hidden" });
      const show = (i, at) => { tl.set(LAY, { visibility: "hidden" }, at).set(LAY[i], { visibility: "visible" }, at); };

      // 1 · gancho: legível no frame 0; a câmera empurra e o destaque pulsa
      tl.fromTo("#L1", { scale: 1 }, { scale: 1.07, duration: 3.2, ease: "sine.inOut" }, 0).to("#L1", { scale: 1.03, duration: T.trilho - 3.2, ease: "sine.inOut" }, 3.2);
      tl.fromTo("#h1 .acc", { scale: 1 }, { scale: 1.08, duration: 0.25, yoyo: true, repeat: 1, ease: "sine.inOut", immediateRender: false }, 0.6);
      gsap.set("#bar1", { scaleX: 0 }); tl.to("#bar1", { scaleX: 1, duration: 0.7, ease: "expo.inOut" }, 1.0);
      type($("#subt"), 1.4, 3.6, SUB);

      // 2 · trilho: um card por vez, câmera de lado; pinceladas a cada troca de tema
      const R = ED.smear(tl, T.trilho - 0.55, { main: "__BG__", lead: "__ACC__", from: "__BG__", angle: -9 });
      show(1, R);
      const TW = $("#tw");
      gsap.set(TW, { x: 0, width: N * 1080 });
      for (let i = 0; i < N; i++) $("#tdots").insertAdjacentHTML("beforeend", "<i></i>");
      const dots = $$("#tdots i");
      gsap.set(".repo", { opacity: 0, y: 160, rotation: 4 });
      gsap.set("#L2", { color: "__INK__", "--mk": "__ACC__" });
      const angles = [-78, 102, 171];
      let s = 0;
      for (let i = 0; i < N; i++) {
        const a = T.ca[i], id = "#rp" + i, th = THEMES[Math.floor(i / 2) % 3];
        tl.set("#tey", { textContent: $(id + " .rk").textContent }, a - 0.5);
        if (i && i % 2 === 0) {
          const bg = $$(".tc")[i].style.background;
          const c = ED.smear(tl, T.sw[s] - 0.55, { main: bg, lead: th.mk, from: $$(".tc")[i - 1].style.background, angle: angles[s % 3] });
          s++;
          tl.set(TW, { x: -i * 1080 }, c).set("#L2", { color: th.ink, "--mk": th.mk }, c);
        } else if (i > 0) {
          tl.to(TW, { x: -i * 1080, duration: 0.75, ease: "expo.inOut" }, a - 0.55)
            .fromTo(TW, { filter: "blur(0px)" }, { filter: "blur(6px)", duration: 0.37, yoyo: true, repeat: 1, ease: "sine.inOut", immediateRender: false }, a - 0.55);
        }
        tl.to(id, { opacity: 1, y: 0, rotation: 0, duration: 0.7, ease: "expo.out" }, a - 0.25);
        tl.set(dots[i], { className: "on" }, a - 0.2);
        const rn = $(id + " .rn"), full = rn.textContent; rn.textContent = "";
        type(rn, a + 0.05, a + 0.5, full);
        gsap.set(id + " .rd", { opacity: 0, y: 30 }); tl.to(id + " .rd", { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, a + 0.5);
        const rs = $(id + " .rs");
        if (rs) { const v = parseInt(rs.textContent.replace(/\D/g, "")); count(rs, a + 0.8, a + 1.6, 0, v, (x) => Math.round(x).toLocaleString("pt-BR")); }
        const ru = $(id + " .ru");
        if (ru) { gsap.set(ru, { opacity: 0, x: -30 }); tl.to(ru, { opacity: 1, x: 0, duration: 0.45, ease: "expo.out" }, a + 1.3); }
        tl.to(id, { y: -14, duration: 1.8, ease: "sine.inOut" }, a + 0.8);
      }

      // 3 · fecho: botão clicado, nome, volta ao gancho
      const C = ED.smear(tl, T.cta - 0.55, { main: "__CBG__", lead: "__CACC__", from: "__BG__", angle: 102 });
      show(2, C);
      const A = T.cta;
      gsap.set("#ha .wi", { yPercent: 115 });
      rise(tl, "#ha .wi", A + 0.1, 0.06);
      marker(tl, "#ha .mk", A + 0.2);
      pop(tl, "#btn", A + 1.2, 0);
      gsap.set("#cursor", { x: 900, y: 1700 });
      tl.to("#cursor", { opacity: 1, duration: 0.15 }, A + 1.4)
        .to("#cursor", { x: 560, y: 1230, duration: 0.7, ease: "power3.inOut" }, A + 1.5)
        .to("#cursor", { scale: 0.85, duration: 0.08, yoyo: true, repeat: 1 }, A + 2.5)
        .to("#btn", { scale: 1.06, duration: 0.1, yoyo: true, repeat: 1 }, A + 2.55)
        .set("#btxt", { textContent: __BTN_OK__ }, A + 2.55);
      const LG = A + 3.0;
      for (const ch of NOME) $("#lname").insertAdjacentHTML("beforeend", ch === " " ? '<span class="sp"></span>' : `<span>${ch}</span>`);
      tl.to("#cursor", { opacity: 0, duration: 0.2 }, LG - 0.1).set("#lockup", { opacity: 1 }, LG);
      gsap.set("#lname span", { yPercent: 120, opacity: 0 });
      tl.to("#lname span", { yPercent: 0, opacity: 1, duration: 0.5, ease: "expo.out", stagger: 0.035 }, LG + 0.1)
        .to("#lname", { scale: 1.04, duration: 1.4, ease: "sine.inOut" }, LG + 0.4);
      const Lz = T.total - 0.9;
      tl.to("#lockup", { opacity: 0, duration: 0.25 }, Lz - 0.2);
      show(0, Lz);
      tl.set(["#subt", "#bar1"], { opacity: 0 }, Lz).fromTo("#L1", { scale: 1.08 }, { scale: 1, duration: 0.85, ease: "expo.out", immediateRender: false }, Lz);

      ED.drive(tl, T.total);
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
