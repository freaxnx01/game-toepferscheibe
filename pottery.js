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
  const api = { RINGS, MINR, MAXR, HMIN, HMAX, MAX_WORKS, defaultProfile, newId, makeShape, canEdit, upsertEntry };
  if (typeof window !== 'undefined') window.Pottery = api;
  if (typeof module !== 'undefined') module.exports = api;
})();
