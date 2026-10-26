const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('../pottery.js');

test('defaultProfile', () => {
  const p = P.defaultProfile();
  assert.equal(p.length, 28);
  assert.ok(Math.abs(p[0] - 0.95) < 1e-9);
  assert.ok(Math.abs(p[27] - 0.60) < 1e-9);
});

test('makeShape copies and versions', () => {
  const profile = P.defaultProfile(), notches = [1, 2];
  const s = P.makeShape({ profile, height: 1, notches });
  assert.equal(s.version, 1);
  profile[0] = 9; notches.push(3);
  assert.notEqual(s.profile[0], 9);
  assert.deepEqual(s.notches, [1, 2]);
  assert.equal(s.corners, 'rund');
  assert.deepEqual(s.lump, { size: 'mittel', form: 'kegel' });
});

test('canEdit', () => {
  assert.equal(P.canEdit({ img: 'x', glaze: null, date: 1 }), false);
  assert.equal(P.canEdit({ shape: P.makeShape({ profile: P.defaultProfile(), height: 1 }) }), false);
  assert.equal(P.canEdit({ id: 'a', shape: P.makeShape({ profile: P.defaultProfile(), height: 1 }) }), true);
});

test('upsertEntry', () => {
  const g = [{ id: 'a', img: 1 }, { id: 'b', img: 2 }, { id: 'c', img: 3 }];
  const r = P.upsertEntry(g, { id: 'b', img: 9 }, 'b');
  assert.equal(r.length, 3); assert.equal(r[1].img, 9);
  const r2 = P.upsertEntry(g, { id: 'n', img: 7 }, 'gone');
  assert.equal(r2.length, 4); assert.equal(r2[0].id, 'n');
  const big = Array.from({ length: 30 }, (_, i) => ({ id: 'i' + i }));
  const r3 = P.upsertEntry(big, { id: 'new' }, null);
  assert.equal(r3.length, 30); assert.equal(r3[0].id, 'new');
});

test('newId unique', () => assert.notEqual(P.newId(), P.newId()));

test('rubGain', () => {
  assert.equal(P.rubGain(0), 0);
  assert.equal(P.rubGain(20), 0);
  assert.ok(P.rubGain(300) > 0);
  assert.ok(P.rubGain(300) <= P.rubGain(600));
  assert.equal(P.rubGain(1200), 0.12);
  assert.equal(P.rubGain(5000), 0.12);
  assert.equal(P.rubGain(-50), 0);
  assert.equal(P.rubGain(NaN), 0);
  assert.equal(P.MOTOR_GAIN, 0.045);
});

test('lumpShape', () => {
  const d = P.lumpShape('mittel', 'kegel');
  assert.deepEqual(d, { profile: P.defaultProfile(), height: 1 });
  const s = P.lumpShape('klein', 'kegel'), g = P.lumpShape('gross', 'kegel');
  assert.ok(Math.abs(s.profile[0] - 0.95 * 0.75) < 1e-9 && s.height === 0.7);
  assert.ok(Math.abs(g.profile[0] - 0.95 * 1.25) < 1e-9 && g.height === 1.3);
  for (const size of ['klein', 'mittel', 'gross']) for (const form of ['kugel', 'kegel']) {
    const { profile, height } = P.lumpShape(size, form);
    assert.equal(profile.length, P.RINGS);
    assert.ok(profile.every((r) => r >= 0.2 && r <= P.MAXR), `${size}/${form} radii`);
    assert.ok(height >= P.HMIN && height <= P.HMAX);
    if (form === 'kegel') for (let i = 1; i < profile.length; i++) assert.ok(profile[i] <= profile[i - 1] + 1e-12);
    else {
      const w = profile.indexOf(Math.max(...profile));
      assert.ok(w >= 8 && w <= 20, `${size} widest at ${w}`);
      assert.ok(profile[profile.length - 1] >= 0.35);
    }
  }
});

const TAU = 2 * Math.PI;
test('cornerFactor', () => {
  for (const a of [0, 1, 3, 6]) assert.equal(P.cornerFactor('rund', a), 1);
  const peaks = (m) => { const v = Array.from({ length: 720 }, (_, i) => P.cornerFactor(m, TAU * i / 720)); return v.filter((x, i) => x > v[(i + 719) % 720] + 1e-12 && x >= v[(i + 1) % 720]).length; };
  for (const m of P.CORNERS) {
    const mean = Array.from({ length: 720 }, (_, i) => P.cornerFactor(m, TAU * i / 720)).reduce((a, b) => a + b) / 720;
    assert.ok(Math.abs(mean - 1) < 0.02, m + ' ' + mean);
  }
  assert.equal(peaks('viereckig'), 4);
  assert.equal(peaks('dreieckig'), 3);
});
test('cornerFactor treats unknown modes like rund', () => {
  for (const m of ['constructor', 'toString', '__proto__', 'bogus', undefined, null]) assert.equal(P.cornerFactor(m, 1.2), 1, String(m));
});
test('rimDrop', () => {
  assert.equal(P.rimDrop([], 1), 0);
  assert.ok(Math.abs(P.rimDrop([1], 1) - P.NOTCH_DEPTH) < 1e-9);
  assert.ok(P.rimDrop([0.05], TAU - 0.05) > 0);
  assert.equal(P.rimDrop([1], 2), 0);
});
test('notchBlock', () => {
  assert.equal(P.notchBlock([1], 1.1), 'near'); assert.equal(P.notchBlock([1], 2), null); assert.equal(P.notchBlock([], 0), null);
  assert.equal(P.notchBlock(Array.from({ length: 16 }, (_, i) => i * 0.3), 6), 'full');
  assert.equal(P.notchBlock([0.1], TAU - 0.05), 'near');
});
test('addNotch', () => {
  assert.deepEqual(P.addNotch([1], 1.1), [1]);
  assert.equal(P.addNotch([1], 2).length, 2);
  assert.ok(Math.abs(P.addNotch([], -0.5)[0] - (TAU - 0.5)) < 1e-9);
  let n = []; for (let i = 0; i < 30; i++) n = P.addNotch(n, i * 0.3);
  assert.equal(n.length, P.MAX_NOTCHES); assert.equal(P.MAX_NOTCHES, 16);
});
test('angleOf', () => {
  assert.ok(Math.abs(P.angleOf(1, 0) - Math.PI / 2) < 1e-9);
  assert.equal(P.angleOf(0, 1), 0);
  assert.ok(Math.abs(P.angleOf(0, -1) - Math.PI) < 1e-9);
});
test('buildMesh', () => {
  const profile = P.defaultProfile(), n = P.outline(profile, 1).length;
  const m = P.buildMesh(P.makeShape({ profile, height: 1 }));
  assert.equal(m.positions.length, 73 * n * 3);
  assert.ok(![...m.positions].some(Number.isNaN));
  const top = (mesh, th) => { let mx = -1; for (let i = 0; i < 73; i++) { if (Math.abs(TAU * i / 72 - th) > 1e-9) continue; for (let j = 0; j < n; j++) mx = Math.max(mx, mesh.positions[(i * n + j) * 3 + 1]); } return mx; };
  assert.ok(Math.abs(top(m, 0) - 2) < 1e-6);
  const mn = P.buildMesh(P.makeShape({ profile, height: 1, notches: [0] }));
  assert.ok(Math.abs(top(mn, 0) - (2 - P.NOTCH_DEPTH)) < 1e-6);
  assert.ok(Math.abs(top(mn, Math.PI) - 2) < 1e-6);
  const mv = P.buildMesh(P.makeShape({ profile, height: 1, corners: 'viereckig', notches: [0, 6.2] }));
  assert.ok(![...mv.positions].some(Number.isNaN));
});

test('flowFactor', () => {
  assert.equal(P.FLOW_TAU, 1000);
  assert.equal(P.flowFactor(0), 0);
  assert.equal(P.flowFactor(-5), 0);
  assert.equal(P.flowFactor(NaN), 0);
  assert.ok(P.flowFactor(16) < 0.02);
  assert.ok(P.flowFactor(3000) >= 0.95);
  assert.ok(P.flowFactor(500) < P.flowFactor(1000));
});

test('flowStep', () => {
  const p = P.defaultProfile(), o = p.slice();
  P.flowStep(p, 10, 1.5, 0.5);
  assert.ok(Math.abs(p[10] - (o[10] + (1.5 - o[10]) * 0.5)) < 1e-12);
  assert.ok(Math.abs(p[11] - (o[11] + (1.5 - o[11]) * Math.exp(-0.25) * 0.5)) < 1e-12);
  assert.equal(p[14], o[14]);
  const q = P.defaultProfile();
  P.flowStep(q, 1, 1.5, 0.5);
  assert.equal(q[0], P.defaultProfile()[0]);
  const c = P.defaultProfile();
  P.flowStep(c, 10, 99, 1);
  assert.equal(c[10], P.MAXR);
  for (const i of [0, P.RINGS]) { const z = P.defaultProfile(); P.flowStep(z, i, 1.5, 1); assert.deepEqual(z, P.defaultProfile()); }
  const n = P.defaultProfile();
  P.flowStep(n, 10, 1.5, 0);
  assert.deepEqual(n, P.defaultProfile());
  // returns the largest absolute change applied
  const d = P.defaultProfile();
  assert.ok(Math.abs(P.flowStep(d, 10, 1.5, 0.5) - Math.abs((1.5 - P.defaultProfile()[10]) * 0.5)) < 1e-12);
  for (const i of [0, P.RINGS]) assert.equal(P.flowStep(P.defaultProfile(), i, 1.5, 1), 0);
  assert.equal(P.flowStep(P.defaultProfile(), 10, 1.5, 0), 0);
  const same = P.defaultProfile().map(() => 1.2);
  assert.equal(P.flowStep(same, 10, 1.2, 0.5), 0);
});

test('fireSteps', () => {
  const T1 = 'Der Ofen heizt langsam auf. Die Glasur schmilzt und wird glänzend.', T2 = 'Der Ofen kühlt ab. Gleich können Sie Ihr Stück herausnehmen.';
  const st = (p) => P.fireSteps(p).map(s => s.state);
  assert.deepEqual(P.fireSteps(0).map(s => s.text), [T1, T2]);
  assert.deepEqual(st(0), ['active', 'todo']);
  assert.deepEqual(st(59), ['active', 'todo']);
  assert.deepEqual(st(60), ['done', 'active']);
  assert.deepEqual(st(99), ['done', 'active']);
  assert.deepEqual(st(100), ['done', 'done']);
});

test('wetStep wets a ring and its neighbours', () => {
  const w = new Array(P.RINGS).fill(0);
  assert.equal(P.wetStep(w, 10, 250), true);
  assert.equal(w[10], 1);
  assert.ok(Math.abs(w[9] - 0.6) < 0.01 && Math.abs(w[11] - 0.6) < 0.01);
  assert.ok(Math.abs(w[12] - 0.25) < 0.01 && Math.abs(w[8] - 0.25) < 0.01);
  assert.equal(w[13], 0);
});

test('wetStep dries over time', () => {
  const w = new Array(P.RINGS).fill(0); w[5] = 1;
  assert.equal(P.wetStep(w, null, 3250), true);
  assert.ok(Math.abs(w[5] - 0.5) < 0.01);
  P.wetStep(w, null, 4000);
  assert.equal(w[5], 0);
  assert.equal(P.wetStep(w, null, 100), false);
});

test('wetStep edges and bad dt', () => {
  const w = new Array(P.RINGS).fill(0);
  P.wetStep(w, 0, 100); P.wetStep(w, P.RINGS - 1, 100);
  assert.equal(w.length, P.RINGS);
  assert.ok(w.every(Number.isFinite));
  const c = w.slice();
  for (const dt of [0, NaN, -5, Infinity]) { assert.equal(P.wetStep(w, 3, dt), false); assert.deepEqual(w, c); }
});

test('wetRoughness', () => {
  assert.equal(P.wetRoughness(0), 0.95);
  assert.ok(Math.abs(P.wetRoughness(1) - 0.38) < 1e-9);
  assert.ok(Math.abs(P.wetRoughness(2) - 0.38) < 1e-9);
});

test('outlineRings maps outline points to rings', () => {
  for (const h of [0.35, 1, 1.6]) {
    const p = P.defaultProfile(), o = P.outline(p, h), r = P.outlineRings(p, h);
    assert.equal(r.length, o.length);
    assert.ok(r.every(v => Number.isInteger(v) && v >= 0 && v < P.RINGS));
    assert.equal(r[1], 0);
    assert.equal(r[P.RINGS], P.RINGS - 1);
  }
});

test('needsHomeHint', () => {
  const IPAD = 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
  const MAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';
  const CRIOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0 Mobile/15E148 Safari/604.1';
  const CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36';
  assert.equal(P.needsHomeHint({ ua: IPAD, maxTouchPoints: 5 }), true);
  assert.equal(P.needsHomeHint({ ua: MAC, maxTouchPoints: 5 }), true);
  assert.equal(P.needsHomeHint({ ua: MAC, maxTouchPoints: 0 }), false);
  assert.equal(P.needsHomeHint({ ua: CRIOS, maxTouchPoints: 5 }), false);
  assert.equal(P.needsHomeHint({ ua: IPAD, maxTouchPoints: 5, standalone: true }), false);
  assert.equal(P.needsHomeHint({ ua: IPAD, maxTouchPoints: 5, displayStandalone: true }), false);
  assert.equal(P.needsHomeHint({ ua: CHROME, maxTouchPoints: 0 }), false);
});

// --- Aushöhlen (#8): wall/floor thickness and hollowing math ---
const oldOutline = (profile, height) => {
  const pts = [[0, 0]];
  for (let i = 0; i < 28; i++) pts.push([profile[i], (i / 27) * 2 * height]);
  const wall = 0.13, floorY = 0.14, h = 2 * height;
  for (let i = 27; i >= 0; i--) { const y = (i / 27) * h; if (y < floorY + 0.05) break; pts.push([Math.max(profile[i] - wall, 0.03), y]); }
  pts.push([0.03, floorY], [0, floorY]);
  return pts;
};
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} !~ ${b}`);

test('outline defaults unchanged', () => {
  const p = P.defaultProfile();
  for (const h of [1, 0.35]) {
    assert.deepEqual(P.outline(p, h), oldOutline(p, h));
    assert.deepEqual(P.outline(p, h, 0.13, 0.14), oldOutline(p, h));
  }
});

test('outline custom wall/floor', () => {
  const p = P.defaultProfile(), o = P.outline(p, 1, 0.3, 0.5);
  const inner = o.slice(P.RINGS + 1, -2);
  assert.ok(inner.length > 0);
  inner.forEach(([r], k) => near(r, Math.max(p[P.RINGS - 1 - k] - 0.3, 0.03)));
  near(o[o.length - 1][1], 0.5);
  near(o[o.length - 2][1], 0.5);
});

test('outline floor clamped', () => {
  const o = P.outline(P.defaultProfile(), 0.4, 0.13, 0.7);
  near(o[o.length - 1][1], 0.6);
});

test('outline solid', () => {
  const p = P.defaultProfile(), o = P.outline(p, 1, 0.13, null);
  assert.equal(o.length, P.RINGS + 2);
  assert.deepEqual(o[o.length - 1], [0, 2]);
  assert.deepEqual(o[0], [0, 0]);
});

test('outlineRings mirrors outline', () => {
  const p = P.defaultProfile();
  for (const [h, w, f] of [[1, undefined, undefined], [1, 0.3, 0.5], [0.4, 0.13, 0.7], [1, 0.13, null]]) {
    const r = P.outlineRings(p, h, w, f);
    assert.equal(r.length, P.outline(p, h, w, f).length);
    if (f === null) assert.equal(r[r.length - 1], P.RINGS - 1);
  }
});

test('buildMesh solid vs default', () => {
  const p = P.defaultProfile(), seg = 12;
  const a = P.buildMesh(P.makeShape({ profile: p, height: 1 }), seg);
  const b = P.buildMesh({ ...P.makeShape({ profile: p, height: 1 }), floor: null }, seg);
  const c = P.buildMesh({ profile: p, height: 1, notches: [], corners: 'rund' }, seg);
  assert.equal(a.positions.length, (seg + 1) * P.outline(p, 1).length * 3);
  assert.equal(b.positions.length, (seg + 1) * (P.RINGS + 2) * 3);
  assert.equal(c.positions.length, a.positions.length);
  assert.ok([...b.positions].every(Number.isFinite));
});

test('makeShape wall/floor', () => {
  const p = P.defaultProfile();
  const s = P.makeShape({ profile: p, height: 1, wall: 0.4, floor: 0.9 });
  assert.equal(s.wall, 0.4); assert.equal(s.floor, 0.9);
  const d = P.makeShape({ profile: p, height: 1 });
  assert.equal(d.wall, 0.13); assert.equal(d.floor, 0.14); assert.equal(d.version, 1);
  assert.equal(P.makeShape({ profile: p, height: 1, floor: null }).floor, null);
});

test('wallFor/holeFor', () => {
  const p = P.defaultProfile().map(() => 1);
  near(P.holeFor(p, P.wallFor(p, 0.6)), 0.6);
  near(P.wallFor(p, 0.99), P.WALL_MIN);
  near(P.wallFor(p, -0.5), P.WALL_MAX);
  near(P.holeFor(p, 5), 0.03);
});

test('hollowStep press', () => {
  const p = P.defaultProfile();
  let s = P.hollowStep({ floor: null, holeR: null }, p, 1, 0, 0.5);
  near(s.floor, 2 + (0.08 - 2) * 0.5); near(s.holeR, 0.15);
  for (let i = 0; i < 60; i++) s = P.hollowStep(s, p, 1, 0, 0.5);
  assert.ok(s.floor >= P.FLOOR_MIN && s.floor < 0.081);
  const t = { floor: 0.5, holeR: 0.15 };
  assert.deepEqual(P.hollowStep(t, p, 1, 0, 0), t);
  assert.notEqual(P.hollowStep(t, p, 1, 0, 0), t);
  assert.equal(P.hollowStep({ floor: null, holeR: null }, p, 1, 0, 0).floor, 2);
});

test('hollowStep pull', () => {
  const p = P.defaultProfile().map(() => 1);
  let s = P.hollowStep({ floor: 0.5, holeR: 0.15 }, p, 1, 0.6, 0.5);
  near(s.holeR, 0.375); assert.equal(s.floor, 0.5);
  for (let i = 0; i < 80; i++) s = P.hollowStep(s, p, 1, 5, 0.5);
  near(P.wallFor(p, s.holeR), P.WALL_MIN);
  const keep = P.hollowStep(s, p, 1, 0.5, 0.5);
  assert.equal(keep.holeR, s.holeR);
});
