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
  const api = { MOTOR_GAIN, rubGain, RINGS, MINR, MAXR, HMIN, HMAX, MAX_WORKS, defaultProfile, lumpShape, newId, makeShape, canEdit, upsertEntry };
  if (typeof window !== 'undefined') window.Pottery = api;
  if (typeof module !== 'undefined') module.exports = api;
})();
