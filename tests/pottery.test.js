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
