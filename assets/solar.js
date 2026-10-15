/* Banner 3D "Universo MyTickets": sistema solar com bolas de esporte. Código original do portal, sem alterações. */
(function () {
  /* ---------- Utilidades de textura ---------- */
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function hash(x, y, z) {
    let h = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
    return h - Math.floor(h);
  }
  function ruido(x, y, z) {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    const xf = x - xi, yf = y - yi, zf = z - zi;
    const s = t => t * t * (3 - 2 * t);
    const u = s(xf), v = s(yf), w = s(zf);
    const L = (a, b, t) => a + (b - a) * t;
    return L(
      L(L(hash(xi, yi, zi), hash(xi+1, yi, zi), u), L(hash(xi, yi+1, zi), hash(xi+1, yi+1, zi), u), v),
      L(L(hash(xi, yi, zi+1), hash(xi+1, yi, zi+1), u), L(hash(xi, yi+1, zi+1), hash(xi+1, yi+1, zi+1), u), v),
      w);
  }
  // Gera textura equiretangular a partir de uma função da direção (x,y,z) na esfera
  function texturaEsfera(W, H, fn) {
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const ctx = c.getContext('2d');
    const img = ctx.createImageData(W, H), d = img.data;
    for (let j = 0; j < H; j++) {
      const th = (j + 0.5) / H * Math.PI, st = Math.sin(th), ct = Math.cos(th);
      for (let i = 0; i < W; i++) {
        const ph = (i + 0.5) / W * Math.PI * 2;
        const x = -Math.cos(ph) * st, y = ct, z = Math.sin(ph) * st;
        const col = fn(x, y, z);
        const k = (j * W + i) * 4;
        d[k] = clamp(col[0], 0, 1) * 255; d[k+1] = clamp(col[1], 0, 1) * 255; d[k+2] = clamp(col[2], 0, 1) * 255; d[k+3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    const t = new THREE.CanvasTexture(c);
    t.encoding = THREE.sRGBEncoding;
    t.anisotropy = 4;
    return t;
  }
  const hex = h => [(h >> 16 & 255) / 255, (h >> 8 & 255) / 255, (h & 255) / 255];
  const mix = (a, b, t) => [a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t, a[2] + (b[2]-a[2])*t];
  const mul = (a, k) => [a[0]*k, a[1]*k, a[2]*k];

  // Curva de costura de tênis/beisebol: latitude alvo em função da longitude
  function costura(x, y, z, amp) {
    const lon = Math.atan2(z, x), lat = Math.asin(clamp(y, -1, 1));
    return { d: lat - amp * Math.sin(2 * lon), lon };
  }

  /* ---------- Bolas ---------- */
  const PHI = (1 + Math.sqrt(5)) / 2;
  const normal = v => { const l = Math.hypot(v[0], v[1], v[2]); return [v[0]/l, v[1]/l, v[2]/l]; };
  const pent = [], hexa = [];
  [[0,1,PHI],[1,PHI,0],[PHI,0,1]].forEach(([a,b,c]) => {
    for (const s1 of [-1,1]) for (const s2 of [-1,1]) {
      const v = [a, b*s1, c*s2]; if (a === 0) { v[1] = s1; v[2] = PHI*s2; }
      pent.push(normal(v));
    }
  });
  // 12 vértices do icosaedro (corrigidos para todas as permutações cíclicas)
  pent.length = 0;
  for (const s1 of [-1,1]) for (const s2 of [-1,1]) {
    pent.push(normal([0, s1, s2*PHI]), normal([s1, s2*PHI, 0]), normal([s2*PHI, 0, s1]));
  }
  // 20 centros de face (vértices do dodecaedro)
  const iP = 1 / PHI;
  for (const a of [-1,1]) for (const b of [-1,1]) for (const c of [-1,1]) hexa.push(normal([a,b,c]));
  for (const s1 of [-1,1]) for (const s2 of [-1,1]) {
    hexa.push(normal([0, s1*iP, s2*PHI]), normal([s1*iP, s2*PHI, 0]), normal([s2*PHI, 0, s1*iP]));
  }
  const centrosFutebol = pent.map(p => ({ p, preto: true })).concat(hexa.map(p => ({ p, preto: false })));

  const bolas = {
    golfe() {
      // Pontos de Fibonacci como covinhas
      const N = 330, pts = [];
      for (let i = 0; i < N; i++) {
        const y = 1 - (i + 0.5) / N * 2, r = Math.sqrt(1 - y*y), t = i * Math.PI * (3 - Math.sqrt(5));
        pts.push([Math.cos(t) * r, y, Math.sin(t) * r]);
      }
      return texturaEsfera(512, 256, (x, y, z) => {
        let b1 = -2, b2 = -2;
        for (const p of pts) {
          const d = p[0]*x + p[1]*y + p[2]*z;
          if (d > b1) { b2 = b1; b1 = d; } else if (d > b2) b2 = d;
        }
        const k = 0.8 + 0.2 * clamp((b1 - b2) * 60, 0, 1);
        return mul([0.97, 0.97, 0.95], k);
      });
    },
    tenis() {
      return texturaEsfera(1024, 512, (x, y, z) => {
        const n = ruido(x*40, y*40, z*40);
        const base = mix(hex(0xc9dc2a), hex(0xe2f05a), n);
        const { d } = costura(x, y, z, 0.85);
        const a = Math.abs(d);
        if (a < 0.035) return mix([0.97, 0.97, 0.92], base, clamp((a - 0.025) / 0.01, 0, 1));
        return base;
      });
    },
    futebol() {
      return texturaEsfera(1024, 512, (x, y, z) => {
        let b1 = -2, b2 = -2, preto = false;
        for (const c of centrosFutebol) {
          const d = c.p[0]*x + c.p[1]*y + c.p[2]*z + (c.preto ? -0.012 : 0);
          if (d > b1) { b2 = b1; b1 = d; preto = c.preto; } else if (d > b2) b2 = d;
        }
        if (b1 - b2 < 0.006) return [0.35, 0.35, 0.36];
        return preto ? [0.08, 0.08, 0.09] : [0.96, 0.96, 0.95];
      });
    },
    basquete() {
      return texturaEsfera(1024, 512, (x, y, z) => {
        const n = ruido(x*90, y*90, z*90);
        const base = mul(hex(0xd8661e), 0.86 + 0.14 * n);
        const w = 0.016;
        if (Math.abs(x) < w || Math.abs(y) < w || Math.abs(Math.abs(z) - 0.7) < w) return [0.07, 0.05, 0.04];
        return base;
      });
    },
    volei() {
      const cores = [hex(0xf2c230), hex(0x1d4fa8), hex(0xf3f1ea)];
      return texturaEsfera(1024, 512, (x, y, z) => {
        const ax = Math.abs(x), ay = Math.abs(y), az = Math.abs(z);
        let face, s, m, seg;
        if (ax >= ay && ax >= az) { face = 0; m = ax; s = y / ax; seg = Math.max(ay, az); }
        else if (ay >= az) { face = 1; m = ay; s = z / ay; seg = Math.max(ax, az); }
        else { face = 2; m = az; s = x / az; seg = Math.max(ax, ay); }
        if (m - seg < 0.012) return [0.25, 0.25, 0.28];
        if (Math.abs(Math.abs(s) - 1/3) < 0.02) return [0.25, 0.25, 0.28];
        const faixa = clamp(Math.floor((s + 1) / 2 * 3), 0, 2);
        const n = ruido(x*50, y*50, z*50);
        return mul(cores[(face + faixa) % 3], 0.92 + 0.08 * n);
      });
    },
    beisebol() {
      return texturaEsfera(1024, 512, (x, y, z) => {
        const n = ruido(x*60, y*60, z*60);
        const base = mul([0.96, 0.94, 0.88], 0.93 + 0.07 * n);
        const { d, lon } = costura(x, y, z, 0.85);
        const a = Math.abs(d);
        const vermelho = [0.8, 0.12, 0.12];
        if (a < 0.006) return mul(base, 0.8);
        if (a > 0.014 && a < 0.05) {
          const f = (lon * 34 / Math.PI + Math.sign(d) * d * 18) % 1;
          if ((f + 1) % 1 < 0.28) return vermelho;
        }
        return base;
      });
    },
    boliche() {
      const furos = [normal([0.12, 0.3, 1]), normal([-0.12, 0.3, 1]), normal([0, -0.05, 1])];
      return texturaEsfera(1024, 512, (x, y, z) => {
        for (const f of furos) {
          const d = f[0]*x + f[1]*y + f[2]*z;
          if (d > 0.9935) return [0.02, 0.02, 0.03];
          if (d > 0.992) return [0.55, 0.6, 0.7];
        }
        const n = ruido(x*2.5 + 3, y*2.5, z*2.5) * 2 + ruido(x*7, y*7, z*7) * 0.6;
        const v = 0.5 + 0.5 * Math.sin(8 * (x + y * 0.4) + n * 5);
        return mix(hex(0x0d1e6b), hex(0x37b4d8), Math.pow(v, 3));
      });
    },
    americano() {
      // Direção antes de achatar: as pontas ficam no eixo x
      return texturaEsfera(1024, 512, (x, y, z) => {
        const n = ruido(x*80, y*80, z*80);
        const base = mul(hex(0x7a3a17), 0.82 + 0.18 * n);
        const branco = [0.95, 0.94, 0.9];
        if (Math.abs(Math.abs(x) - 0.62) < 0.035 && y < 0.85) return branco;
        if (y > 0 && Math.abs(x) < 0.33) {
          if (Math.abs(z) < 0.02) return branco;
          if (Math.abs(z) < 0.085 && ((x + 0.33) / 0.066) % 1 < 0.35) return branco;
        }
        if (Math.abs(y) < 0.008 || Math.abs(z) < 0.008) return mul(base, 0.55);
        return base;
      });
    },
    pingue() {
      return texturaEsfera(256, 128, (x, y, z) => mul([1, 0.98, 0.95], 0.95 + 0.05 * ruido(x*20, y*20, z*20)));
    }
  };

  /* ---------- Cena ---------- */
  const canvas = document.getElementById('cena3d');
  const caixa = document.getElementById('banner3d');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x05060d, 1);
  renderer.outputEncoding = THREE.sRGBEncoding;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05060d, 0.0025);
  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 3000);
  camera.position.set(0, 46, 112);

  const controls = new THREE.OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.enableRotate = matchMedia('(pointer: fine)').matches;
  controls.minDistance = 10;
  controls.maxDistance = 380;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.3;
  controls.enableZoom = false; // não rouba a rolagem da página

  (function estrelas() {
    const n = 3000, pos = new Float32Array(n * 3), cor = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const r = 600 + Math.random() * 600;
      const t = Math.random() * Math.PI * 2, p = Math.acos(2 * Math.random() - 1);
      pos[i*3] = r * Math.sin(p) * Math.cos(t); pos[i*3+1] = r * Math.cos(p); pos[i*3+2] = r * Math.sin(p) * Math.sin(t);
      const k = 0.55 + Math.random() * 0.45, q = Math.random() < 0.2;
      cor[i*3] = k; cor[i*3+1] = k * (q ? 0.85 : 0.95); cor[i*3+2] = k * (q ? 0.7 : 1);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(cor, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ size: 2, vertexColors: true, fog: false })));
  })();

  function texturaBrilho(r, g, b) {
    const c = document.createElement('canvas'); c.width = c.height = 128;
    const x = c.getContext('2d');
    const gr = x.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, `rgba(${r},${g},${b},1)`); gr.addColorStop(0.25, `rgba(${r},${g},${b},0.45)`); gr.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  }

  // Sol com superfície turbulenta
  const texSol = texturaEsfera(512, 256, (x, y, z) => {
    const n = ruido(x*6, y*6, z*6) * 0.6 + ruido(x*18, y*18, z*18) * 0.4;
    return mix(hex(0xff8a1f), hex(0xfff0a8), n);
  });
  const sol = new THREE.Mesh(new THREE.SphereGeometry(5, 64, 64), new THREE.MeshBasicMaterial({ map: texSol }));
  scene.add(sol);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: texturaBrilho(255, 170, 70), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  halo.scale.set(32, 32, 1);
  sol.add(halo);

  scene.add(new THREE.PointLight(0xfff2dc, 1.9));
  scene.add(new THREE.AmbientLight(0x3a4070, 0.6));

  const defs = [
    { nome: 'Mercúrio', bola: 'Golfe',            tex: 'golfe',     a: 10, r: 0.6,  periodo: 88,    e: 0.205, rug: 0.5, lento: 0.125 },
    { nome: 'Vênus',    bola: 'Tênis',            tex: 'tenis',     a: 15, r: 0.95, periodo: 225,   e: 0.007, rug: 1, lento: 0.25 },
    { nome: 'Terra',    bola: 'Boliche',          tex: 'boliche',   a: 21, r: 1.7,  periodo: 365,   e: 0.017, rug: 0.15, met: 0.2, lento: 0.5 },
    { nome: 'Marte',    bola: 'Vôlei',            tex: 'volei',     a: 28, r: 1.3,  periodo: 687,   e: 0.093, rug: 0.6, lento: 0.5 },
    { nome: 'Júpiter',  bola: 'Basquete',         tex: 'basquete',  a: 41, r: 2.7, periodo: 4333,  e: 0.049, rug: 0.8 },
    { nome: 'Saturno',  bola: 'Beisebol',         tex: 'beisebol',  a: 55, r: 2.2,  periodo: 10759, e: 0.057, rug: 0.75, aneis: true },
    { nome: 'Urano',    bola: 'Futebol',          tex: 'futebol',   a: 68, r: 1.8,  periodo: 30687, e: 0.046, rug: 0.45, lento: 20 },
    { nome: 'Netuno',   bola: 'Futebol americano',tex: 'americano', a: 80, r: 1.6,  periodo: 60190, e: 0.010, rug: 0.7, oval: true, lento: 25 }
  ];

  const camadaRotulos = document.getElementById('rotulos3d');
  const planetas = defs.map((d, i) => {
    d.e = 0; // órbitas circulares e concêntricas, todas centradas no Sol
    const plano = new THREE.Group();
    plano.rotation.y = 0;
    scene.add(plano);

    const b = d.a * Math.sqrt(1 - d.e * d.e), c = d.a * d.e;
    const pts = [];
    for (let k = 0; k <= 256; k++) { const t = k / 256 * Math.PI * 2; pts.push(new THREE.Vector3(d.a * Math.cos(t) - c, 0, b * Math.sin(t))); }
    const linha = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: 0x8c9cff, transparent: true, opacity: 0.2 }));
    plano.add(linha);

    const mat = new THREE.MeshStandardMaterial({ map: bolas[d.tex](), roughness: d.rug, metalness: d.met || 0 });
    if (d.tex === 'golfe') { mat.bumpMap = mat.map; mat.bumpScale = 0.04; }
    const corpo = new THREE.Mesh(new THREE.SphereGeometry(d.r, 64, 48), mat);
    if (d.oval) corpo.scale.set(1.55, 0.95, 0.95);
    // Eixo de giro com leve inclinação
    const pivo = new THREE.Group();
    pivo.rotation.z = 0.35;
    pivo.add(corpo);
    plano.add(pivo);

    if (d.aneis) {
      const anel = new THREE.Mesh(new THREE.RingGeometry(d.r * 1.4, d.r * 2.4, 96),
        new THREE.MeshBasicMaterial({ color: 0xcdb98a, side: THREE.DoubleSide, transparent: true, opacity: 0.5 }));
      anel.rotation.x = Math.PI / 2;
      pivo.add(anel);
    }

    let lua = null;
    if (d.lua) {
      lua = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 24),
        new THREE.MeshStandardMaterial({ map: bolas.pingue(), roughness: 0.35 }));
      plano.add(lua);
    }

    const N = 110;
    const rPos = new Float32Array(N * 3), rCor = new Float32Array(N * 3);
    const rGeo = new THREE.BufferGeometry();
    rGeo.setAttribute('position', new THREE.BufferAttribute(rPos, 3));
    rGeo.setAttribute('color', new THREE.BufferAttribute(rCor, 3));
    for (let k = 0; k < N; k++) { const f = 0.7 * (1 - k / N); rCor[k*3] = f; rCor[k*3+1] = f * 0.8; rCor[k*3+2] = f * 0.5; }
    const rastro = new THREE.Line(rGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    rastro.frustumCulled = false;
    plano.add(rastro);

    const rot = document.createElement('div');
    rot.className = 'rotulo';
    rot.innerHTML = `${d.nome}<small>${d.bola.toLowerCase()}</small>`;
    camadaRotulos.appendChild(rot);

    return { d, plano, pivo, corpo, lua, linha, rastro, rPos, N, b, c, rot, M0: Math.random() * Math.PI * 2, iniciado: false };
  });

  const fatores = [0.9, 0.4, 0, 0.3, 0.2, 0.35, 0.15, 0.25];
  function aplicarInclinacao(graus) {
    planetas.forEach((p, i) => {
      p.plano.rotation.x = THREE.MathUtils.degToRad(graus * fatores[i]);
      p.plano.rotation.z = THREE.MathUtils.degToRad(graus * fatores[i] * 0.4 * (i % 2 ? 1 : -1));
    });
  }
  function posicaoKepler(p, dias) {
    const M = p.M0 + 2 * Math.PI / p.d.periodo * dias * (p.d.lento || 1);
    let E = M;
    for (let k = 0; k < 6; k++) E -= (E - p.d.e * Math.sin(E) - M) / (1 - p.d.e * Math.cos(E));
    return [p.d.a * Math.cos(E) - p.c, p.b * Math.sin(E)];
  }

  /* ---------- Interface ---------- */
  let velocidade = 1, pausado = false, mostrarRastro = true, mostrarNomes = true, dias = 0;
  const DIAS_POR_SEGUNDO = 45;
  velocidade = 1;
  controls.autoRotateSpeed = 0.4;
  aplicarInclinacao(0);

  let W = 1, H = 1;
  /* Celular (tela em pé): planetas maiores, câmera mais alta e afastada na medida certa para
     as órbitas caberem na largura, e a cena empurrada para cima da caixa de texto do rodapé. */
  const DIR_DESKTOP = new THREE.Vector3(0, 46, 112), DIR_CELULAR = new THREE.Vector3(0, 0.8, 0.6).normalize();
  let modoCelular = null;
  function redimensionar() {
    W = caixa.clientWidth; H = caixa.clientHeight;
    renderer.setSize(W, H, false);
    camera.aspect = W / H;
    const celular = W < 640;
    if (celular) {
      camera.fov = 50;
      const meiaH = Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect);
      const dist = THREE.MathUtils.clamp(60 / Math.tan(meiaH), 90, 260);  // órbita de Saturno inteira na largura
      if (modoCelular !== true) { camera.position.copy(DIR_CELULAR).multiplyScalar(dist); }
      else { camera.position.setLength(dist); }
      const caixaTexto = document.querySelector('#banner3d .solar-box');
      const deslocar = caixaTexto ? Math.round(caixaTexto.offsetHeight * 0.45) : 0;
      camera.setViewOffset(W, H, 0, deslocar, W, H);
    } else {
      camera.fov = W/H > 4 ? 30 : 40;
      if (modoCelular === true) camera.position.copy(DIR_DESKTOP);
      camera.clearViewOffset();
    }
    if (celular !== modoCelular) {
      planetas.forEach(p => p.pivo.scale.setScalar(celular ? 2.1 : 1));
      sol.scale.setScalar(celular ? 1.35 : 1);
      modoCelular = celular;
    }
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', redimensionar);
  let visivelBanner = true;
  if ('IntersectionObserver' in window) new IntersectionObserver(es => { visivelBanner = es[0].isIntersecting; }).observe(caixa);
  redimensionar();

  /* ---------- Animação ---------- */
  const relogio = new THREE.Clock();
  const tmp = new THREE.Vector3();
  let ultimoTexto = 0;
  function animar() {
    requestAnimationFrame(animar);
    if (!visivelBanner) { relogio.getDelta(); return; }
    const dt = Math.min(relogio.getDelta(), 0.05);
    const passo = pausado ? 0 : dt * DIAS_POR_SEGUNDO * velocidade;
    dias += passo;
    sol.rotation.y += dt * 0.06;

    planetas.forEach(p => {
      const [x, z] = posicaoKepler(p, dias);
      p.pivo.position.set(x, 0, z);
      p.corpo.rotation.y += passo * 0.0125 + dt * 0.15;
      if (p.d.oval) p.corpo.rotation.x += dt * 2.5; // espiral do futebol americano
      if (p.lua) {
        const t = dias / 27.3 * Math.PI * 2;
        p.lua.position.set(x + Math.cos(t) * 2.3, Math.sin(t) * 0.4, z + Math.sin(t) * 2.3);
      }
      if (!p.iniciado) { for (let k = 0; k < p.N; k++) { p.rPos[k*3] = x; p.rPos[k*3+1] = 0; p.rPos[k*3+2] = z; } p.iniciado = true; }
      if (passo > 0 && mostrarRastro) {
        p.rPos.copyWithin(3, 0, (p.N - 1) * 3);
        p.rPos[0] = x; p.rPos[1] = 0; p.rPos[2] = z;
        p.rastro.geometry.attributes.position.needsUpdate = true;
      }
    });

    controls.update();
    renderer.render(scene, camera);

    if (mostrarNomes) {
      planetas.forEach(p => {
        p.pivo.getWorldPosition(tmp);
        tmp.y += p.d.r + 0.6;
        tmp.project(camera);
        const visivel = tmp.z < 1 && Math.abs(tmp.x) < 1.1 && Math.abs(tmp.y) < 1.1;
        p.rot.hidden = !visivel;
        if (visivel) p.rot.style.transform = `translate(${(tmp.x * 0.5 + 0.5) * W}px, ${(-tmp.y * 0.5 + 0.5) * H}px) translate(-50%, -100%)`;
      });
    }
  }
  animar();
})();
