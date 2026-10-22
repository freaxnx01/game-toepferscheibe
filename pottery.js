// Pure game logic, shared by index.html (global Pottery) and node --test (module.exports).
(function () {
  const RINGS = 28, MINR = 0.15, MAXR = 1.6, HMIN = 0.35, HMAX = 1.6, MAX_WORKS = 30;
  const defaultProfile = () => Array.from({ length: RINGS }, (_, i) => 0.95 - 0.35 * (i / (RINGS - 1)));
  const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const makeShape = ({ profile, height, notches = [], corners = 'rund', lump = { size: 'mittel', form: 'kegel' } }) =>
    ({ version: 1, profile: [...profile], height, notches: [...notches], corners, lump: { ...lump } });
  const canEdit = (e) => !!(e && e.id && e.shape && e.shape.version >= 1 && e.shape.profile && e.shape.profile.length === RINGS);
  const upsertEntry = (gallery, entry, editId) => {
    const i = editId ? gallery.findIndex((e) => e.id === editId) : -1;
    const out = i >= 0 ? gallery.map((e, j) => (j === i ? entry : e)) : [entry, ...gallery];
    return out.slice(0, MAX_WORKS);
  };
  const SIZE_R = { klein: 0.75, mittel: 1, gross: 1.25 }, SIZE_H = { klein: 0.7, mittel: 1, gross: 1.3 };
  const lumpShape = (size, form) => {
    const k = SIZE_R[size] || 1, hk = SIZE_H[size] || 1;
    const base = form === 'kugel' ? defaultProfile().map((_, i) => 0.5 + 0.45 * Math.sin(Math.PI * (0.1 + 0.8 * i / (RINGS - 1)))) : defaultProfile();
    return { profile: base.map((r) => Math.min(MAXR, Math.max(0.2, r * k))), height: Math.min(HMAX, Math.max(HMIN, hk)) };
  };
  const MOTOR_GAIN = 0.045;
  const rubGain = (v) => { if (!(v > 20)) return 0; const x = Math.min(1, (v - 20) / 1180); return 0.12 * x * x * (3 - 2 * x); };
  const TAU = 2 * Math.PI;
  const CORNERS = ['rund', 'oval', 'dreieckig', 'viereckig'], NOTCH_DEPTH = 0.18, NOTCH_HALF_WIDTH = 0.22, NOTCH_MIN_GAP = 0.25, MAX_NOTCHES = 8;
  const poly = (n, a) => Math.cos(Math.PI / n) / Math.cos((((a % (TAU / n)) + TAU / n) % (TAU / n)) - Math.PI / n);
  const polyMean = Object.create(null); for (const [m, n] of [['dreieckig', 3], ['viereckig', 4]]) { let s = 0; for (let i = 0; i < 720; i++) s += 0.4 + 0.6 * poly(n, TAU * i / 720); polyMean[m] = s / 720; }
  const cornerFactor = (mode, a) => mode === 'oval' ? 1 + 0.18 * Math.cos(2 * a) : polyMean[mode] ? (0.4 + 0.6 * poly(mode === 'dreieckig' ? 3 : 4, a)) / polyMean[mode] : 1;
  const rimDrop = (notches, a) => { let m = 0; for (const n of notches) { let d = Math.abs(a - n) % TAU; if (d > Math.PI) d = TAU - d; if (d < NOTCH_HALF_WIDTH) m = Math.max(m, NOTCH_DEPTH * (1 + Math.cos(Math.PI * d / NOTCH_HALF_WIDTH)) / 2); } return m; };
  const addNotch = (notches, a) => {
    const t = ((a % TAU) + TAU) % TAU;
    if (notches.length >= MAX_NOTCHES) return [...notches];
    for (const n of notches) { let d = Math.abs(t - n) % TAU; if (d > Math.PI) d = TAU - d; if (d < NOTCH_MIN_GAP) return [...notches]; }
    return [...notches, t];
  };
  const angleOf = (x, z) => ((Math.atan2(x, z) % TAU) + TAU) % TAU;
  const outline = (profile, height) => {
    const pts = [[0, 0]];
    for (let i = 0; i < RINGS; i++) pts.push([profile[i], (i / (RINGS - 1)) * 2 * height]);
    const wall = 0.13, floorY = 0.14, h = 2 * height;
    for (let i = RINGS - 1; i >= 0; i--) { const y = (i / (RINGS - 1)) * h; if (y < floorY + 0.05) break; pts.push([Math.max(profile[i] - wall, 0.03), y]); }
    pts.push([0.03, floorY], [0, floorY]);
    return pts;
  };
  const buildMesh = (shape, segments = 72) => {
    const pts = outline(shape.profile, shape.height), n = pts.length, H = 2 * shape.height, band = 0.35, y0 = H - band;
    const positions = new Float32Array((segments + 1) * n * 3), uvs = new Float32Array((segments + 1) * n * 2), indices = [];
    for (let i = 0; i <= segments; i++) {
      const th = TAU * i / segments, sn = Math.sin(th), cs = Math.cos(th), k = cornerFactor(shape.corners, th), drop = rimDrop(shape.notches, th);
      for (let j = 0; j < n; j++) {
        const [r, y] = pts[j], o = i * n + j, yy = y > y0 ? y0 + (y - y0) * (band - drop) / band : y;
        positions[o * 3] = r * k * sn; positions[o * 3 + 1] = yy; positions[o * 3 + 2] = r * k * cs;
        uvs[o * 2] = i / segments; uvs[o * 2 + 1] = j / (n - 1);
      }
    }
    for (let i = 0; i < segments; i++) for (let j = 0; j < n - 1; j++) { const a = i * n + j, b = a + n, c = b + 1, d = a + 1; indices.push(a, b, d, c, d, b); }
    return { positions, uvs, indices };
  };
  const FLOW_TAU = 1000;
  const flowFactor = (dtMs) => (Number.isFinite(dtMs) && dtMs > 0 ? 1 - Math.exp(-dtMs / FLOW_TAU) : 0);
  const flowStep = (profile, idx, radius, f) => {
    if (idx < 1 || idx >= RINGS) return 0;
    const r = Math.min(MAXR, Math.max(0.2, radius));
    let max = 0;
    for (let k = -3; k <= 3; k++) { const j = idx + k; if (j < 1 || j >= RINGS) continue; const d = (r - profile[j]) * Math.exp(-k * k / 4) * f; profile[j] += d; max = Math.max(max, Math.abs(d)); }
    return max;
  };
  const api = { FLOW_TAU, flowFactor, flowStep, CORNERS, NOTCH_DEPTH, NOTCH_HALF_WIDTH, NOTCH_MIN_GAP, MAX_NOTCHES, cornerFactor, rimDrop, addNotch, angleOf, outline, buildMesh, MOTOR_GAIN, rubGain, RINGS, MINR, MAXR, HMIN, HMAX, MAX_WORKS, defaultProfile, lumpShape, newId, makeShape, canEdit, upsertEntry };
  if (typeof window !== 'undefined') window.Pottery = api;
  if (typeof module !== 'undefined') module.exports = api;
})();
