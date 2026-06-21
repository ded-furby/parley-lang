import * as THREE from 'three';
import gsap from 'gsap';

const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const canvas = document.getElementById('scene');

gsap.defaults({ duration: 0.72, ease: 'power3.out' });

/* ---------- DOM: copy button ---------- */

const copyBtn = document.getElementById('copy-btn');
copyBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(
      document.getElementById('install-cmd').textContent.trim());
    copyBtn.textContent = 'Copied';
    if (!reduceMotion) {
      gsap.fromTo(copyBtn, { scale: 0.96 }, {
        scale: 1,
        duration: 0.42,
        ease: 'back.out(1.7)',
        clearProps: 'transform',
      });
    }
    setTimeout(() => { copyBtn.textContent = 'Copy command'; }, 1800);
  } catch {
    copyBtn.textContent = 'Select and copy';
  }
});

const install = document.querySelector('.install');
if (install && !reduceMotion) {
  const xTo = gsap.quickTo(install, 'x', { duration: 0.45, ease: 'power3' });
  const yTo = gsap.quickTo(install, 'y', { duration: 0.45, ease: 'power3' });
  install.addEventListener('pointermove', (e) => {
    const r = install.getBoundingClientRect();
    xTo((e.clientX - r.left - r.width / 2) * 0.025);
    yTo((e.clientY - r.top - r.height / 2) * 0.08);
  }, { passive: true });
  install.addEventListener('pointerleave', () => {
    xTo(0);
    yTo(0);
  }, { passive: true });
}

/* ---------- DOM: reveals (enhance-only; content is visible by default) ---------- */

if (!reduceMotion && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        gsap.to(e.target, {
          autoAlpha: 1,
          y: 0,
          filter: 'blur(0px)',
          duration: 0.9,
          ease: 'power3.out',
          clearProps: 'transform,filter,visibility',
        });
        io.unobserve(e.target);
      }
    }
  }, { threshold: 0.18 });
  for (const el of document.querySelectorAll('.reveal')) {
    const r = el.getBoundingClientRect();
    if (r.top > innerHeight) {
      el.classList.add('will-reveal');
      gsap.set(el, { autoAlpha: 0, y: 28, filter: 'blur(8px)' });
      io.observe(el);
    }
  }
}

/* ---------- scene setup ---------- */

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
} catch {
  renderer = null; // hero fallback headline stays visible
}

if (renderer) init(renderer);

function init(renderer) {
  const BG = new THREE.Color('#1f1413');
  const EMBER = new THREE.Color('#e25f49');
  const AMBER = new THREE.Color('#e89a64');

  renderer.setClearColor(BG, 1);
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(BG, 9, 16);

  const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 40);
  camera.position.set(0, 0, 7);

  const group = new THREE.Group();
  scene.add(group);

  /* lights (for the slab) */
  scene.add(new THREE.AmbientLight(0xffffff, 0.12));
  const key = new THREE.PointLight(EMBER, 26, 0, 1.8);
  key.position.set(3.2, 2.5, 3.5);
  scene.add(key);
  const rim = new THREE.PointLight(0xffffff, 8, 0, 2);
  rim.position.set(-3.5, -1.5, -2);
  scene.add(rim);

  /* ---------- the slab (the binary) ---------- */

  const SLAB = { w: 1.5, h: 2.3, d: 0.45, y: -0.05 };
  const slabGeo = new THREE.BoxGeometry(SLAB.w, SLAB.h, SLAB.d);
  const slabMat = new THREE.MeshStandardMaterial({
    color: '#16100f', metalness: 0.85, roughness: 0.38,
    transparent: true, opacity: 0,
  });
  const slab = new THREE.Mesh(slabGeo, slabMat);
  slab.position.y = SLAB.y;
  slab.visible = false;
  slab.renderOrder = 1;
  group.add(slab);

  const edgeMat = new THREE.LineBasicMaterial({
    color: EMBER, transparent: true, opacity: 0,
  });
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(slabGeo), edgeMat);
  slab.add(edges);

  /* ---------- particle position sets ---------- */

  const COUNT = (innerWidth < 720 || devicePixelRatio > 2.5) ? 9000 : 15000;

  function sampleTextPositions(n) {
    // Rasterize the headline, then lift lit pixels into world space.
    const lines = innerWidth / innerHeight < 0.9
      ? ['speak', 'plainly.'] : ['speak plainly.'];
    const fs = 220;
    const cv = document.createElement('canvas');
    const cx = cv.getContext('2d', { willReadFrequently: true });
    cx.font = `700 ${fs}px Zodiak, Georgia, serif`;
    const widths = lines.map(l => cx.measureText(l).width);
    const tw = Math.ceil(Math.max(...widths));
    const lh = fs * 1.08;
    cv.width = tw + 40;
    cv.height = Math.ceil(lh * lines.length) + 40;
    cx.fillStyle = '#fff';
    cx.font = `700 ${fs}px Zodiak, Georgia, serif`;
    cx.textBaseline = 'middle';
    lines.forEach((l, i) => {
      cx.fillText(l, (cv.width - widths[i]) / 2, 20 + lh * (i + 0.5));
    });
    const px = cx.getImageData(0, 0, cv.width, cv.height).data;
    const pts = [];
    for (let y = 0; y < cv.height; y += 2) {
      for (let x = 0; x < cv.width; x += 2) {
        if (px[(y * cv.width + x) * 4 + 3] > 140) pts.push(x, y);
      }
    }
    const visW = 2 * camera.position.z * Math.tan(THREE.MathUtils.degToRad(21)) * camera.aspect;
    const worldW = Math.min(7.4, visW * 0.84);
    const s = worldW / cv.width;
    const out = new Float32Array(n * 3);
    const m = pts.length / 2;
    for (let i = 0; i < n; i++) {
      const j = (Math.random() * m) | 0;
      out[i * 3] = (pts[j * 2] - cv.width / 2) * s + (Math.random() - 0.5) * 0.012;
      out[i * 3 + 1] = -(pts[j * 2 + 1] - cv.height / 2) * s + (Math.random() - 0.5) * 0.012 + 0.35;
      out[i * 3 + 2] = (Math.random() - 0.5) * 0.22;
    }
    return out;
  }

  function sampleDustPositions(n) {
    const out = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const r = 1.6 + Math.random() * 1.9;
      out[i * 3] = Math.cos(a) * r;
      out[i * 3 + 1] = (Math.random() - 0.5) * 3.4;
      out[i * 3 + 2] = Math.sin(a) * r * 0.65;
    }
    return out;
  }

  function sampleSlabPositions(n) {
    const { w, h, d, y } = SLAB;
    const areas = [w * h, w * h, h * d, h * d, w * d, w * d]; // ±z, ±x, ±y
    const total = areas.reduce((a, b) => a + b, 0);
    const out = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      let pick = Math.random() * total, f = 0;
      while (pick > areas[f]) { pick -= areas[f]; f++; }
      const u = Math.random() - 0.5, v = Math.random() - 0.5;
      let px, py, pz;
      if (f < 2) { px = u * w; py = v * h; pz = (f ? -1 : 1) * d / 2; }
      else if (f < 4) { px = (f === 2 ? 1 : -1) * w / 2; py = u * h; pz = v * d; }
      else { px = u * w; py = (f === 4 ? 1 : -1) * h / 2; pz = v * d; }
      const j = 0.015;
      out[i * 3] = px + (Math.random() - 0.5) * j;
      out[i * 3 + 1] = py + y + (Math.random() - 0.5) * j;
      out[i * 3 + 2] = pz + (Math.random() - 0.5) * j;
    }
    return out;
  }

  /* ---------- particle material ---------- */

  const uniforms = {
    uTime: { value: 0 },
    uMorph1: { value: 0 },
    uMorph2: { value: 0 },
    uMouse: { value: new THREE.Vector3(99, 99, 0) },
    uForce: { value: reduceMotion ? 0 : 0.6 },
    uPR: { value: Math.min(devicePixelRatio, 2) },
    uEmber: { value: EMBER },
    uAmber: { value: AMBER },
  };

  const particleMat = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexShader: /* glsl */`
      attribute vec3 aDust;
      attribute vec3 aCore;
      attribute float aSeed;
      uniform float uTime, uMorph1, uMorph2, uForce, uPR;
      uniform vec3 uMouse;
      varying float vSeed, vFade;
      void main() {
        float s = aSeed;
        float t1 = smoothstep(0.0, 1.0, clamp(uMorph1 * 1.8 - s * 0.8, 0.0, 1.0));
        float t2 = smoothstep(0.0, 1.0, clamp(uMorph2 * 1.8 - s * 0.8, 0.0, 1.0));
        vec3 p = mix(mix(position, aDust, t1), aCore, t2);
        float drift = mix(0.028, 0.004, t2);
        p += drift * vec3(
          sin(uTime * 0.6 + s * 43.0),
          cos(uTime * 0.5 + s * 17.0),
          sin(uTime * 0.7 + s * 29.0));
        vec3 dm = p - uMouse;
        float dist2 = dot(dm, dm);
        p += normalize(dm + 0.0001) * uForce * exp(-dist2 * 2.4) * (1.0 - 0.55 * t2);
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mv;
        gl_PointSize = (1.5 + s * 2.1) * uPR * (7.0 / -mv.z);
        vSeed = s;
        vFade = 0.6 + 0.4 * sin(uTime * (0.4 + s * 0.8) + s * 90.0);
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 uEmber, uAmber;
      varying float vSeed, vFade;
      void main() {
        vec2 c = gl_PointCoord - 0.5;
        float d = length(c);
        if (d > 0.5) discard;
        float a = smoothstep(0.5, 0.08, d) * vFade;
        vec3 col = mix(uEmber, uAmber, step(0.82, vSeed));
        col = mix(col, vec3(1.0, 0.93, 0.88), step(0.96, vSeed) * 0.6);
        gl_FragColor = vec4(col, a * 0.85);
      }`,
  });

  let points = null;
  function buildParticles() {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(sampleTextPositions(COUNT), 3));
    geo.setAttribute('aDust', new THREE.BufferAttribute(sampleDustPositions(COUNT), 3));
    geo.setAttribute('aCore', new THREE.BufferAttribute(sampleSlabPositions(COUNT), 3));
    const seeds = new Float32Array(COUNT);
    for (let i = 0; i < COUNT; i++) seeds[i] = Math.random();
    geo.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
    if (points) { points.geometry.dispose(); group.remove(points); }
    points = new THREE.Points(geo, particleMat);
    points.renderOrder = 2;
    points.frustumCulled = false;
    group.add(points);
  }

  /* ---------- input ---------- */

  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2(9, 9);
  const mouseTarget = new THREE.Vector3(99, 99, 0);
  let parallaxX = 0, parallaxY = 0;

  function pointTo(clientX, clientY) {
    ndc.set((clientX / innerWidth) * 2 - 1, -(clientY / innerHeight) * 2 + 1);
    raycaster.setFromCamera(ndc, camera);
    const t = -raycaster.ray.origin.z / raycaster.ray.direction.z;
    mouseTarget.copy(raycaster.ray.origin)
      .addScaledVector(raycaster.ray.direction, t)
      .sub(group.position);
  }
  if (!reduceMotion) {
    addEventListener('pointermove', e => pointTo(e.clientX, e.clientY), { passive: true });
    addEventListener('touchmove', e => {
      if (e.touches[0]) pointTo(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
  }

  /* ---------- scroll ---------- */

  let scrollP = 0, smoothP = reduceMotion ? 0 : 0;
  function readScroll() {
    const max = document.documentElement.scrollHeight - innerHeight;
    scrollP = max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 0;
  }
  addEventListener('scroll', readScroll, { passive: true });
  readScroll();

  const ss = (a, b, x) => {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  };

  /* ---------- frame ---------- */

  const clock = new THREE.Clock();

  function applyState(p, time) {
    uniforms.uTime.value = time;
    uniforms.uMorph1.value = ss(0.04, 0.42, p);
    uniforms.uMorph2.value = ss(0.45, 0.84, p);
    uniforms.uMouse.value.lerp(mouseTarget, 0.12);

    const m2 = uniforms.uMorph2.value;
    slab.visible = m2 > 0.25;
    slabMat.opacity = ss(0.62, 0.92, p);
    edgeMat.opacity = ss(0.55, 0.82, p) * (0.85 - 0.35 * ss(0.92, 1, p))
      * (0.8 + 0.2 * Math.sin(time * 1.3));
    slab.rotation.y = -0.35 + m2 * 0.35; // settles square to camera
    group.rotation.y = 0.22 * (ss(0.3, 0.6, p) - ss(0.75, 0.95, p));

    // mid-page the work drifts right, prose owns the left column
    const wide = camera.aspect > 1.1;
    const shift = wide ? (ss(0.14, 0.34, p) - ss(0.8, 0.96, p)) * 1.7 : 0;
    group.position.x += (shift - group.position.x) * 0.07;

    camera.position.x += (parallaxX - camera.position.x) * 0.05;
    camera.position.y += (parallaxY - camera.position.y) * 0.05;
    camera.position.z = 7 - 0.7 * ss(0.85, 1, p);
    camera.lookAt(group.position.x * 0.55, 0, 0);
  }

  function frame() {
    smoothP += (scrollP - smoothP) * 0.06;
    if (!reduceMotion) {
      parallaxX = ndc.x === 9 ? 0 : ndc.x * 0.32;
      parallaxY = ndc.y === 9 ? 0 : ndc.y * 0.2;
    }
    applyState(smoothP, clock.getElapsedTime());
    renderer.render(scene, camera);
  }

  function resize() {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    uniforms.uPR.value = Math.min(devicePixelRatio, 2);
  }
  resize();

  let resizeTimer;
  addEventListener('resize', () => {
    resize();
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      buildParticles();
      if (reduceMotion) frame();
    }, 200);
  });

  /* ---------- boot ---------- */

  // Sample text only after the display font is in, so the particles
  // trace Zodiak letterforms rather than the fallback serif.
  const start = () => {
    buildParticles();
    document.documentElement.classList.remove('no-scene');
    document.documentElement.classList.add('scene-ok');
    if (reduceMotion) {
      // Static composition: the headline holds; scroll morph and cursor
      // force are disabled. Render a couple of frames so fog and lights
      // settle, then stop.
      smoothP = 0; scrollP = 0;
      applyState(0, 0.8);
      renderer.render(scene, camera);
    } else {
      renderer.setAnimationLoop(frame);
    }
  };

  if (document.fonts && document.fonts.ready) {
    Promise.race([
      document.fonts.load('700 220px Zodiak').then(() => document.fonts.ready),
      new Promise(r => setTimeout(r, 2200)),
    ]).then(start);
  } else {
    start();
  }
}
