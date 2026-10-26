"""E2E smoke flows (Playwright). Run: systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 python3 tests/e2e/smoke.py"""
import json, os, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
KEY = 'toepfern.galerie'
ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader']


# --- shared helpers
def start_server():
    if os.environ.get('BASE_URL'):
        return None, os.environ['BASE_URL']
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    p = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(ROOT)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}/index.html'
    for _ in range(50):
        try: socket.create_connection(('127.0.0.1', port), 0.2).close(); break
        except OSError: time.sleep(0.1)
    return p, url


CTX = []


def new_page(browser, url, seed=None, init=None, **ctx_kw):
    ctx = browser.new_context(viewport={'width': 1180, 'height': 820}, **ctx_kw); CTX.append(ctx)
    ctx.route('https://stats.freaxnx01.ch/**', lambda r: r.abort())
    if init: ctx.add_init_script(init)
    page = ctx.new_page()
    page.set_default_timeout(120000)
    page.goto(url, wait_until='domcontentloaded')
    if seed is not None:
        page.evaluate('([k, v]) => localStorage.setItem(k, v)', [KEY, json.dumps(seed)])
        page.reload(wait_until='domcontentloaded')
    return page


def click(page, text, exact=True):
    page.get_by_role('button', name=text, exact=exact).first.click()


def wait_text(page, text):
    page.get_by_text(text, exact=False).first.wait_for(state='visible')


def gallery(page):
    return json.loads(page.evaluate(f"localStorage.getItem('{KEY}')") or '[]')


def cards(page):
    return page.get_by_role('button', name='Entfernen', exact=True).count()


def glaze_fire_save(page, glaze=None):
    click(page, 'Fertig – Glasieren →')
    if glaze: click(page, glaze)
    click(page, 'In den Ofen →')
    click(page, 'Stück herausnehmen →')
    wait_text(page, 'In die Galerie stellen')
    click(page, 'In die Galerie stellen')
    wait_text(page, 'Entfernen')


def start_clay(page):
    click(page, 'Ton auf die Scheibe legen')
    at_hollow(page)
    click(page, 'Für mich aushöhlen')
    wait_text(page, 'An der Scheibe')


def at_hollow(page):
    page.locator('header').get_by_text('Aushöhlen', exact=True).wait_for(state='visible')


def hollow_attrs(page, floor, wall):
    page.wait_for_function("([f, w]) => { const e = document.querySelector('[data-floor]'); return !!e && e.getAttribute('data-floor') === f && e.getAttribute('data-wall') === w; }", arg=[floor, wall])


def make_work(page, glaze='Kobalt'):
    start_clay(page)
    glaze_fire_save(page, glaze)


# --- flows
def edit_replaces(b, url):
    page = new_page(b, url)
    make_work(page)
    assert cards(page) == 1, f'expected 1 card, got {cards(page)}'
    click(page, 'Weiter töpfern')
    wait_text(page, 'An der Scheibe')
    click(page, '▲ Höher ziehen')
    click(page, 'Fertig – Glasieren →')
    border = page.get_by_role('button', name='Kobalt').first.evaluate('e => getComputedStyle(e).borderTopColor')
    assert border == 'rgb(180, 94, 58)', f'Kobalt not preselected: {border}'
    click(page, 'In den Ofen →')
    click(page, 'Stück herausnehmen →')
    wait_text(page, 'In die Galerie stellen')
    click(page, 'In die Galerie stellen')
    wait_text(page, 'Entfernen')
    g = gallery(page)
    assert cards(page) == 1 and len(g) == 1, f'expected 1 card, got {cards(page)}/{len(g)}'
    assert g[0]['shape']['height'] > 1, f"height {g[0]['shape']['height']}"


def old_entry(b, url):
    page = new_page(b, url)
    new = page.evaluate("() => ({id: Pottery.newId(), img: 'data:,', glaze: 'Kobalt', date: '2. Januar 2026', shape: Pottery.makeShape({profile: Pottery.defaultProfile(), height: 1})})")
    page.evaluate('([k, v]) => localStorage.setItem(k, v)', [KEY, json.dumps([{'img': 'data:,', 'glaze': 'Honig', 'date': '1. Januar 2026'}, new])])
    page.reload(wait_until='domcontentloaded')
    start_clay(page)
    click(page, 'Galerie (2)', exact=False)
    wait_text(page, 'Honig')
    assert cards(page) == 2
    assert page.get_by_role('button', name='Weiter töpfern').count() == 1, 'only the new entry may be editable'
    old = page.locator('div', has_text='Honig').filter(has=page.get_by_role('button', name='Entfernen')).last
    old.get_by_role('button', name='Entfernen').click()
    page.get_by_text('Kobalt', exact=True).first.wait_for()
    g = gallery(page)
    assert len(g) == 1 and g[0]['id'] == new['id'], f'wrong entry left: {g}'


def undo_keeps_link(b, url):
    page = new_page(b, url)
    make_work(page)
    click(page, 'Weiter töpfern')
    wait_text(page, 'An der Scheibe')
    click(page, 'Neuer Tonklumpen')
    click(page, 'Ton auflegen')
    at_hollow(page)
    click(page, '↶ Rückgängig')
    click(page, 'Weiter zum Formen →')
    glaze_fire_save(page)
    assert cards(page) == 1 and len(gallery(page)) == 1, f'expected 1 card, got {cards(page)}/{len(gallery(page))}'


BACK = '← Zurück zu meinem Stück'


def back_from_wheel(b, url):
    page = new_page(b, url)
    start_clay(page)
    click(page, '▲ Höher ziehen')
    click(page, 'Galerie (0)', exact=False)
    wait_text(page, 'Meine Werke')
    assert page.get_by_role('button', name=BACK).count() == 1, 'back button missing'
    click(page, BACK)
    wait_text(page, 'An der Scheibe')
    glaze_fire_save(page)
    g = gallery(page)
    assert len(g) == 1 and g[0]['shape']['height'] > 1, f'height lost: {g and g[0]["shape"]["height"]}'


def back_during_firing(b, url):
    page = new_page(b, url)
    errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    seed = page.evaluate("() => [{id: Pottery.newId(), img: 'data:,', glaze: 'Kobalt', date: '2. Januar 2026', shape: Pottery.makeShape({profile: Pottery.defaultProfile(), height: 1})}]")
    page.evaluate('([k, v]) => localStorage.setItem(k, v)', [KEY, json.dumps(seed)]); page.reload(wait_until='domcontentloaded')
    page.set_viewport_size({'width': 640, 'height': 460})
    page.set_default_timeout(300000)  # software GL: the visible firing canvas can starve the page for minutes
    start_clay(page)
    click(page, 'Fertig – Glasieren →')
    click(page, 'In den Ofen →')
    click(page, 'Galerie (1)', exact=False)
    wait_text(page, 'Meine Werke')
    page.wait_for_timeout(8000)
    assert page.get_by_role('heading', name='Meine Werke').count() == 1, 'left the gallery on its own'
    page.get_by_role('button', name=BACK).first.click(no_wait_after=True)  # the post-click wait starves on the software-GL canvas
    wait_text(page, 'Stück herausnehmen →')
    # view round trip from firing: header Galerie -> 3D -> back to gallery -> back to my piece
    click(page, 'Galerie (1)', exact=False); wait_text(page, 'Meine Werke')
    page.get_by_role('button', name=VIEW, exact=True).click(no_wait_after=True)
    page.get_by_role('heading', name='Kobalt').wait_for(state='visible')
    page.get_by_role('button', name=BACKG, exact=True).click(no_wait_after=True); wait_text(page, 'Meine Werke')
    page.get_by_role('button', name=BACK).first.click(no_wait_after=True)
    wait_text(page, 'Stück herausnehmen →')
    assert page.get_by_text('Der Ofen heizt langsam auf.', exact=False).count() == 1, 'firing panel gone after view round trip'
    assert not errs, errs[:2]
    for t in ('Der Ofen heizt langsam auf.', 'Der Ofen kühlt ab.'): assert page.get_by_text(t, exact=False).count() == 1, f'step missing: {t}'
    assert page.get_by_text('Fertig gebrannt').count() == 0, 'auto-advanced to done without the button'
    assert page.get_by_text('✓').count() == 2, 'expected two done marks'
    click(page, 'Stück herausnehmen →')
    wait_text(page, 'Fertig gebrannt')
    assert page.get_by_text('Fertig', exact=True).count() >= 1, 'step label Fertig missing'


def no_back_after_save(b, url):
    page = new_page(b, url)
    make_work(page)
    assert page.get_by_role('button', name=BACK).count() == 0, 'back button after save'


def sound_drag(b, url):
    page = new_page(b, url)
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    start_clay(page)
    click(page, '🔇 Klang aus')
    wait_text(page, 'Klang an')
    box = page.locator('canvas').first.bounding_box()
    cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
    page.mouse.move(cx, cy); page.mouse.down()
    for i in range(12): page.mouse.move(cx + (i % 3) * 6, cy - i * 8)
    page.mouse.up()
    click(page, '▶ Scheibe drehen') if page.get_by_role('button', name='▶ Scheibe drehen').count() else click(page, '⏸ Scheibe anhalten')
    click(page, '🔊 Klang an')
    assert not errs, errs[:2]


def lump_choice(b, url):
    page = new_page(b, url)
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    click(page, 'Gross'); click(page, 'Kugel')
    start_clay(page)
    wait_text(page, 'An der Scheibe')
    click(page, 'Neuer Tonklumpen')
    assert page.get_by_role('button', name='▲ Höher ziehen').count() == 0, 'shaping panel still visible while picking'
    b_gross = page.get_by_role('button', name='Gross', exact=True).first.evaluate('e => getComputedStyle(e).borderTopColor')
    assert b_gross == 'rgb(180, 94, 58)', f'current lump not preselected: {b_gross}'
    click(page, 'Klein')
    click(page, 'Ton auflegen')
    at_hollow(page)
    assert page.get_by_role('button', name='Neuer Tonklumpen').count() == 0 and page.get_by_role('button', name='▲ Höher ziehen').count() == 0, 'shaping buttons visible while hollowing'
    click(page, 'Für mich aushöhlen')
    click(page, '▲ Höher ziehen')
    click(page, '↶ Rückgängig')
    click(page, '↶ Rückgängig')  # back to solid: the game returns to Aushöhlen
    at_hollow(page)
    click(page, '↶ Rückgängig')
    click(page, 'Weiter zum Formen →')
    click(page, 'Neuer Tonklumpen')
    assert page.get_by_role('button', name='Gross', exact=True).first.evaluate('e => getComputedStyle(e).borderTopColor') == 'rgb(180, 94, 58)', 'undo did not restore lump'
    click(page, 'Abbrechen')
    glaze_fire_save(page)
    s = gallery(page)[0]['shape']
    assert s['lump'] == {'size': 'gross', 'form': 'kugel'}, s['lump']
    assert abs(s['height'] - 1.3) < 1e-6, s['height']
    assert not errs, errs[:2]
    click(page, 'Neues Stück beginnen')
    wait_text(page, 'Ton auf die Scheibe legen')


def rim_point(page, a=0.0):
    """Canvas point on the front rim of the default pot (camera theta 0, phi 1.25, dist 5.4, fov 32), rotated by a around the axis."""
    import math
    sh = page.evaluate("() => { const l = Pottery.lumpShape('mittel', 'kegel'); return { h: l.height, r: l.profile[l.profile.length - 1] }; }")
    box = page.locator('canvas').first.bounding_box()
    h, r = sh['h'], sh['r'] * 0.97
    P = (r * math.sin(a), 2 * h - 0.1, r * math.cos(a)); T = (0, 0.9 * h, 0); d, phi = 5.4, 1.25
    C = (0, T[1] + d * math.cos(phi), d * math.sin(phi))
    f = [T[i] - C[i] for i in range(3)]; n = math.sqrt(sum(x * x for x in f)); f = [x / n for x in f]
    rt = [f[2] * 0 - f[1] * 0, 0, 0]; rt = [-f[2], 0, f[0]]; n = math.hypot(rt[0], rt[2]); rt = [x / n for x in rt]  # right = f x up
    up = [rt[1] * f[2] - rt[2] * f[1], rt[2] * f[0] - rt[0] * f[2], rt[0] * f[1] - rt[1] * f[0]]
    v = [P[i] - C[i] for i in range(3)]; dep = sum(v[i] * f[i] for i in range(3))
    t = math.tan(math.radians(32) / 2)
    nx = sum(v[i] * rt[i] for i in range(3)) / dep / t / (box['width'] / box['height'])
    ny = sum(v[i] * up[i] for i in range(3)) / dep / t
    return box['x'] + (nx + 1) / 2 * box['width'], box['y'] + (1 - ny) / 2 * box['height']


def drag_pot(page):
    box = page.locator('canvas').first.bounding_box()
    cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] * 0.55
    page.mouse.move(cx, cy); page.mouse.down()
    for i in range(10): page.mouse.move(cx + 40 + i * 6, cy - i * 6)
    page.mouse.up()


def tools(b, url):
    page = new_page(b, url)
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    start_clay(page)
    wait_text(page, 'An der Scheibe')
    base = page.evaluate("() => Pottery.lumpShape('mittel', 'kegel').profile")
    click(page, 'Neuer Tonklumpen'); drag_pot(page); click(page, 'Abbrechen')  # no shaping while the lump picker is open
    assert page.get_by_role('button', name='⏸ Scheibe anhalten').count() == 1
    click(page, 'Werkzeug')
    wait_text(page, '▶ Scheibe drehen')
    for c in ['Rund', 'Oval', 'Dreieckig', 'Viereckig']: assert page.get_by_role('button', name=c, exact=True).count() == 1, c
    assert page.get_by_role('button', name='▲ Höher ziehen').count() == 0 and page.get_by_role('button', name='↶ Rückgängig').count() == 1
    assert page.get_by_role('button', name='▶ Scheibe drehen').count() == 1 and page.get_by_role('button', name='🔇 Klang aus').count() == 1, 'spin/sound row must stay'
    wait_text(page, 'Tippen Sie auf den Rand, um eine Kerbe zu machen.')
    click(page, 'Viereckig')
    x, y = rim_point(page, 0.0); page.mouse.click(x, y)
    x, y = rim_point(page, 0.9); page.mouse.click(x, y)
    click(page, 'Formen')
    wait_text(page, '⏸ Scheibe anhalten')
    glaze_fire_save(page)
    s = gallery(page)[0]['shape']
    assert s['corners'] == 'viereckig', s['corners']
    assert len(s['notches']) == 2, f"notches {s['notches']}"
    assert all(abs(a - b) < 1e-9 for a, b in zip(s['profile'], base)), 'profile changed'
    click(page, 'Weiter töpfern')
    wait_text(page, 'An der Scheibe')
    click(page, '↶ Rückgängig')  # empty history: harmless
    click(page, 'Werkzeug'); click(page, 'Rund'); click(page, 'Dreieckig'); drag_pot(page)  # drag in tool mode must not shape
    click(page, '↶ Rückgängig')
    click(page, 'Formen')
    glaze_fire_save(page)
    s = gallery(page)[0]['shape']
    assert s['corners'] == 'rund', f"undo did not restore rund: {s['corners']}"
    assert len(s['notches']) == 2 and len(gallery(page)) == 1
    assert all(abs(a - b) < 1e-9 for a, b in zip(s['profile'], base)), 'drag in tool mode shaped the pot'
    assert not errs, errs[:2]


def done_then_start(b, url):
    page = new_page(b, url)
    make_work(page)
    click(page, 'Weiter töpfern')
    wait_text(page, 'An der Scheibe')
    click(page, 'Fertig – Glasieren →')
    click(page, 'In den Ofen →')
    click(page, 'Stück herausnehmen →')
    wait_text(page, 'In die Galerie stellen')
    click(page, 'Neues Stück beginnen')
    wait_text(page, 'Ton auf die Scheibe legen')
    assert page.get_by_role('button', name=BACK).count() == 1, 'back button missing on start'
    click(page, 'Meine Werke ansehen')
    wait_text(page, 'Meine Werke')
    assert page.get_by_role('button', name=BACK).count() == 1, 'back button missing in gallery'
    click(page, BACK)
    wait_text(page, 'In die Galerie stellen')


def glaze_not_preselected(b, url):
    page = new_page(b, url)
    make_work(page, 'Kobalt')
    click(page, 'Weiter töpfern')
    wait_text(page, 'An der Scheibe')
    click(page, 'Neuer Tonklumpen')
    click(page, 'Ton auflegen')
    click(page, 'Für mich aushöhlen')
    click(page, 'Fertig – Glasieren →')
    sel = lambda: page.evaluate("() => [...document.querySelectorAll('button')].filter(b => b.textContent.includes('Kobalt') && getComputedStyle(b).borderTopColor === 'rgb(180, 94, 58)').length")
    assert sel() == 0, 'glaze preselected after Ton auflegen'
    click(page, '← Zurück zur Scheibe')
    click(page, '↶ Rückgängig')
    at_hollow(page)
    click(page, '↶ Rückgängig')
    click(page, 'Weiter zum Formen →')
    click(page, 'Fertig – Glasieren →')
    assert sel() == 1, 'undo did not restore preferred glaze'


VCLOCK = """(() => { let t = 0; window.__budget = 0; performance.now = () => t;
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = cb => raf(() => { if (window.__budget > 0) { window.__budget--; t += 50; } cb(t); }); })()"""


def frames(page, n):
    """Let exactly n frames of 50 ms pass on the virtual clock (time stands still otherwise)."""
    page.evaluate(f'window.__budget = {n}')
    page.wait_for_function('window.__budget === 0')


def sluggish(b, url):
    page = new_page(b, url)
    page.context.add_init_script(VCLOCK); page.reload(wait_until='domcontentloaded')  # virtual clock: every frame is exactly 50 ms, independent of the slow software renderer
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    start_clay(page)
    wait_text(page, 'An der Scheibe')
    base = page.evaluate("() => Pottery.lumpShape('mittel', 'kegel').profile")
    box = page.locator('canvas').first.bounding_box()
    cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] * 0.55

    def dmax(): return max(abs(a - c) for a, c in zip(gallery(page)[0]['shape']['profile'], base))

    page.mouse.move(cx, cy); page.mouse.down()  # quick swipe: 3 frames = 150 ms, aimed at the axis
    page.mouse.move(cx + 2, cy - 4); frames(page, 3)
    page.mouse.up()
    glaze_fire_save(page)
    swipe = dmax()
    click(page, 'Weiter töpfern'); wait_text(page, 'An der Scheibe')
    page.mouse.move(cx, cy); page.mouse.down()  # hold still for 70 frames = 3.5 s: clay keeps flowing to the finger
    frames(page, 70)
    page.mouse.up()
    glaze_fire_save(page)
    hold = dmax()
    assert hold >= 0.15, f'hold barely moved the clay: {hold:.3f}'
    assert 0 < swipe < 0.25 * hold, f'swipe {swipe:.3f} vs hold {hold:.3f}'
    assert not errs, errs[:2]


def wet_max(page):
    return float(page.evaluate("() => document.querySelector('[data-wet]').getAttribute('data-wet')"))


def wet_shine(b, url):
    page = new_page(b, url)
    page.context.add_init_script(VCLOCK); page.reload(wait_until='domcontentloaded')  # virtual clock: 50 ms per frame
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    start_clay(page)
    wait_text(page, 'An der Scheibe')
    assert wet_max(page) == 0, 'wet at start'
    box = page.locator('canvas').first.bounding_box()
    cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] * 0.55
    page.mouse.move(cx, cy); page.mouse.down()
    page.mouse.move(cx + 2, cy - 2); frames(page, 10)  # 0.5 s
    w = wet_max(page)
    page.mouse.up()
    assert w >= 0.8, f'not wet while shaping: {w}'
    frames(page, 160)  # 8 s
    assert wet_max(page) == 0, f'still wet after 8 s: {wet_max(page)}'
    page.mouse.move(box['x'] + 15, cy); page.mouse.down()  # next to the pot: orbit, no wetting
    page.mouse.move(box['x'] + 40, cy); frames(page, 10)
    page.mouse.up()
    assert wet_max(page) == 0, 'orbit drag wetted the clay'
    for label, pre in (('undo', ['↶ Rückgängig']), ('reset', ['Neuer Tonklumpen', 'Ton auflegen', 'Für mich aushöhlen'])):
        page.mouse.move(cx, cy); page.mouse.down()
        page.mouse.move(cx + 2, cy - 2); frames(page, 4)
        assert wet_max(page) > 0, f'not wet before {label}'
        page.mouse.up()
        for t in pre: click(page, t)
        assert wet_max(page) == 0, f'still wet after {label}'
    page.mouse.move(cx, cy); page.mouse.down()
    page.mouse.move(cx + 2, cy - 2); frames(page, 10)
    assert wet_max(page) > 0
    page.mouse.up()
    click(page, 'Fertig – Glasieren →')
    assert wet_max(page) == 0, 'wet on glaze screen'
    click(page, 'In den Ofen →'); click(page, 'Stück herausnehmen →')
    click(page, 'Neues Stück beginnen'); start_clay(page)
    wait_text(page, 'An der Scheibe')
    assert wet_max(page) == 0, 'wet after new piece'
    assert not errs, errs[:2]


def spin_and_padding(b, url):
    page = new_page(b, url)
    start_clay(page)
    click(page, 'Werkzeug')
    click(page, '▶ Scheibe drehen')
    click(page, 'Formen')
    wait_text(page, '⏸ Scheibe anhalten')
    click(page, 'Neuer Tonklumpen')
    bg = page.get_by_role('button', name='Mittel', exact=True).first.evaluate('e => getComputedStyle(e).backgroundColor')
    assert bg == 'rgb(180, 94, 58)', f'selected lump not filled: {bg}'
    pad = page.locator('aside').first.evaluate('e => getComputedStyle(e).paddingBottom')
    assert pad == '96px', pad


def notch_hint(b, url):
    page = new_page(b, url)
    start_clay(page); wait_text(page, 'An der Scheibe')
    click(page, 'Werkzeug'); wait_text(page, '▶ Scheibe drehen')
    x, y = rim_point(page, 0.0); page.mouse.click(x, y)
    page.mouse.click(x, y)  # exactly the same spot: the ray now passes through the cut-out
    wait_text(page, 'Zu nah an einer Kerbe')


def wheel_px(page, src):
    # bands are in the 480px square crop of a 640x460 viewport (caller sets it); the pot fills the middle, the wheel would show in the sides
    # draw src (data URL, or None = the live canvas) on #E8DAC2 like saveToGallery; return permille of pixels in the bands beside/below the pot that are not the plain backdrop (tolerance < 5 = 0.5 %)
    return page.evaluate("""async (src) => {
        const im = new Image(); im.src = src || document.querySelector('canvas').toDataURL('image/png'); await im.decode();
        const n = Math.min(im.width, im.height), c = document.createElement('canvas'); c.width = c.height = 480; const x = c.getContext('2d');
        x.fillStyle = '#E8DAC2'; x.fillRect(0, 0, 480, 480); x.drawImage(im, (im.width - n) / 2, (im.height - n) / 2, n, n, 0, 0, 480, 480);
        let bad = 0, tot = 0;  // side bands (the pot fills the middle); tolerance 80 lets the faint floor shadow pass, the wheel (#6b4a33) is ~125 off
        for (const [x0, w] of [[0, 90], [390, 90]]) { const d = x.getImageData(x0, 300, w, 150).data;
          for (let i = 0; i < d.length; i += 4) { tot++; if (Math.abs(d[i] - 0xE8) > 80 || Math.abs(d[i + 1] - 0xDA) > 80 || Math.abs(d[i + 2] - 0xC2) > 80) bad++; } }
        return Math.round(bad * 1000 / tot); }""", src)


def portrait_takeout_visible(b, url):
    page = new_page(b, url)
    page.set_viewport_size({'width': 800, 'height': 900}); page.set_default_timeout(300000)  # portrait iPad: sidebar wraps below the canvas
    start_clay(page); click(page, 'Fertig – Glasieren →'); click(page, 'Kobalt'); click(page, 'In den Ofen →')
    page.evaluate('window.scrollTo(0, 0)')  # the click above scrolled the sidebar into view
    btn = page.get_by_role('button', name='Stück herausnehmen →'); btn.wait_for(state='visible')
    page.wait_for_timeout(1500)  # smooth scroll
    bb = btn.bounding_box(); assert bb and bb['y'] >= 0 and bb['y'] + bb['height'] <= 900, f'button below the fold: {bb}'
    page.evaluate('window.scrollTo(0, 0)'); click(page, 'Galerie (0)', exact=False); wait_text(page, 'Meine Werke')
    page.get_by_role('button', name=BACK).first.click(no_wait_after=True)
    btn.wait_for(state='visible'); page.wait_for_timeout(1500)
    bb = btn.bounding_box(); assert bb and bb['y'] >= 0 and bb['y'] + bb['height'] <= 900, f'button below the fold after back: {bb}'


def gallery_no_wheel(b, url):
    page = new_page(b, url)
    page.set_viewport_size({'width': 640, 'height': 460}); page.set_default_timeout(300000)
    start_clay(page)
    assert wheel_px(page, None) > 0, 'sanity: wheel visible at the wheel'
    click(page, 'Fertig – Glasieren →'); click(page, 'Kobalt'); click(page, 'In den Ofen →')
    wait_text(page, 'Stück herausnehmen →')
    assert wheel_px(page, None) < 5, 'wheel visible while firing'
    click(page, 'Stück herausnehmen →'); wait_text(page, 'In die Galerie stellen')
    assert wheel_px(page, None) < 5, 'wheel visible on done'
    click(page, 'Galerie (0)', exact=False); wait_text(page, 'Meine Werke')
    page.get_by_role('button', name=BACK).first.click(no_wait_after=True); wait_text(page, 'In die Galerie stellen')
    assert wheel_px(page, None) < 5, 'wheel visible on done after returning from gallery'
    click(page, 'In die Galerie stellen'); wait_text(page, 'Entfernen')
    assert wheel_px(page, gallery(page)[0]['img']) < 5, 'wheel in gallery photo'
    click(page, 'Weiter töpfern'); wait_text(page, 'An der Scheibe')
    assert wheel_px(page, None) > 0, 'wheel not back at the wheel'


STUB = "window.umami = {track: (n, d) => (window.__ev = window.__ev || []).push([n, d])}"
PRIVACY = 'https://github.com/freaxnx01/game-toepferscheibe#datenschutz--privacy'


def analytics(b, url):
    page = new_page(b, url, init=STUB)
    ev = lambda: page.evaluate('window.__ev || []')
    page.reload(wait_until='domcontentloaded'); wait_text(page, 'Ton auf die Scheibe legen')
    assert ev() == [], ev()
    a = page.get_by_role('link', name='Datenschutz', exact=True)
    assert a.count() == 1 and a.get_attribute('href') == PRIVACY and a.get_attribute('target') == '_blank' and 'noopener' in a.get_attribute('rel'), 'privacy link'
    start_clay(page)
    assert ev() == [['game_start', {'game': 'toepferscheibe'}]], ev()
    glaze_fire_save(page, 'Kobalt')
    click(page, 'Weiter töpfern'); wait_text(page, 'An der Scheibe')
    assert len(ev()) == 1, ev()
    click(page, 'Fertig – Glasieren →'); click(page, 'In den Ofen →'); click(page, 'Stück herausnehmen →')
    wait_text(page, 'In die Galerie stellen'); click(page, 'Neues Stück beginnen')
    wait_text(page, 'Ton auf die Scheibe legen')
    assert len(ev()) == 1, ev()
    start_clay(page); wait_text(page, 'An der Scheibe')
    assert ev() == [['game_start', {'game': 'toepferscheibe'}]] * 2, ev()
    p2 = new_page(b, url, init="Object.defineProperty(window, 'gameAnalytics', {get: () => undefined, set: () => {}, configurable: true})")
    errs = []; p2.on('pageerror', lambda e: errs.append(str(e)))
    p2.reload(wait_until='domcontentloaded'); wait_text(p2, 'Ton auf die Scheibe legen')
    start_clay(p2); wait_text(p2, 'An der Scheibe')
    assert not errs, errs[:2]


SHOT_DIR = os.environ.get('E2E_SHOT_DIR')
VIEW = 'In 3D anschauen'
BACKG = '← Zurück zur Galerie'


def gallery_view(b, url):
    import hashlib
    page = new_page(b, url)
    errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    new = page.evaluate("() => ({id: Pottery.newId(), img: 'data:,', glaze: 'Kobalt', date: '2. Januar 2026', shape: Pottery.makeShape({profile: Pottery.defaultProfile(), height: 1})})")
    page.evaluate('([k, v]) => localStorage.setItem(k, v)', [KEY, json.dumps([{'img': 'data:,', 'glaze': 'Honig', 'date': '1. Januar 2026'}, new])])
    page.reload(wait_until='domcontentloaded')
    start_clay(page)
    click(page, '▲ Höher ziehen')
    click(page, '⏸ Scheibe anhalten')
    page.wait_for_timeout(500)
    h0 = hashlib.md5(page.locator('canvas').first.screenshot()).hexdigest()
    click(page, 'Galerie (2)', exact=False); wait_text(page, 'Meine Werke')
    assert page.get_by_role('button', name=VIEW, exact=True).count() == 1, 'exactly the new card needs a 3D button'
    badge = page.get_by_role('button', name=VIEW, exact=True).get_by_text(VIEW).first.bounding_box()
    assert badge and badge['height'] >= 20, f'badge too small: {badge}'
    before = gallery(page)
    page.get_by_role('button', name=VIEW, exact=True).click()
    page.get_by_role('heading', name='Kobalt').wait_for(state='visible')
    assert page.get_by_role('button', name=BACKG, exact=True).is_visible()
    page.wait_for_timeout(300)
    bb = page.get_by_role('button', name=BACKG, exact=True).bounding_box(); assert bb and bb['y'] >= 0 and bb['y'] + bb['height'] <= 820, f'back button below the fold: {bb}'
    assert page.locator('canvas').first.is_visible(), 'canvas hidden in view'
    page.wait_for_timeout(800)
    if SHOT_DIR:
        Path(SHOT_DIR).mkdir(parents=True, exist_ok=True); page.locator('canvas').first.screenshot(path=str(Path(SHOT_DIR) / 'view.png'))
    drag_pot(page)
    assert gallery(page) == before, 'drag changed the gallery'
    click(page, BACKG); wait_text(page, 'Meine Werke')
    assert page.get_by_role('button', name=BACK).count() == 1, 'back to my piece missing after view'
    page.get_by_role('button', name=VIEW, exact=True).click()
    page.get_by_role('heading', name='Kobalt').wait_for(state='visible')
    click(page, BACKG); click(page, BACK)
    wait_text(page, 'An der Scheibe'); page.wait_for_timeout(500)
    h1 = hashlib.md5(page.locator('canvas').first.screenshot()).hexdigest()
    assert h0 == h1, 'work piece changed by viewing'
    click(page, 'Galerie (2)', exact=False)
    page.get_by_role('button', name=VIEW, exact=True).click()
    page.get_by_role('heading', name='Kobalt').wait_for(state='visible')
    click(page, 'Galerie (2)', exact=False); wait_text(page, 'Meine Werke')
    assert page.get_by_role('button', name=BACK).count() == 1, 'back to my piece missing after header exit'
    page.get_by_role('button', name=VIEW, exact=True).click()
    page.get_by_role('heading', name='Kobalt').wait_for(state='visible')
    click(page, 'Weiter töpfern'); wait_text(page, 'An der Scheibe')
    assert page.get_by_role('button', name='Fertig – Glasieren →').is_visible()
    assert not errs, errs[:2]


def home_hint(b, url):
    IPAD = 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    d = new_page(b, url); d.wait_for_timeout(500)
    assert d.get_by_text('Tipp:', exact=False).count() == 0, 'desktop must not show the tip'
    page = new_page(b, url, user_agent=IPAD, has_touch=True, init="Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5})")
    wait_text(page, 'Tipp:')
    btn = page.get_by_role('button', name='Verstanden', exact=True)
    assert btn.bounding_box()['height'] >= 64, 'Verstanden too small'
    btn.click()
    page.get_by_text('Tipp:', exact=False).wait_for(state='hidden')
    page.reload(wait_until='domcontentloaded'); wait_text(page, 'Schön, dass Sie da sind')
    page.wait_for_timeout(500)
    assert page.get_by_text('Tipp:', exact=False).count() == 0, 'tip back after reload'


def hollow_steps(b, url):
    page = new_page(b, url)
    errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    click(page, 'Ton auf die Scheibe legen')
    at_hollow(page)
    assert page.locator('header').get_by_text('Aushöhlen', exact=True).count() == 1, 'step label missing'
    hollow_attrs(page, 'solid', '0.130')
    assert page.get_by_role('button', name='Weiter zum Formen →').is_disabled(), 'Weiter must be disabled while solid'
    for t in ('Neuer Tonklumpen', 'Fertig – Glasieren →', '🎲 Zufällige Form', '▲ Höher ziehen', 'Werkzeug'): assert page.get_by_role('button', name=t, exact=True).count() == 0, f'{t} visible while hollowing'
    for t in ('Für mich aushöhlen', '↶ Rückgängig'): assert page.get_by_role('button', name=t, exact=True).count() == 1, f'{t} missing'
    click(page, 'Für mich aushöhlen')
    wait_text(page, 'An der Scheibe')
    hollow_attrs(page, '0.140', '0.130')
    click(page, '← Zurück zum Aushöhlen')
    at_hollow(page)
    hollow_attrs(page, '0.140', '0.130')
    assert page.get_by_role('button', name='Weiter zum Formen →').is_enabled(), 'Weiter must be enabled with a hole'
    click(page, 'Galerie (0)', exact=False); wait_text(page, 'Meine Werke')
    click(page, BACK)
    at_hollow(page)
    click(page, 'Weiter zum Formen →'); wait_text(page, 'An der Scheibe')
    glaze_fire_save(page, 'Kobalt')
    click(page, 'Weiter töpfern'); wait_text(page, 'An der Scheibe')
    hollow_attrs(page, '0.140', '0.130')
    s = gallery(page)[0]['shape']
    assert s['wall'] == 0.13 and s['floor'] == 0.14, (s.get('wall'), s.get('floor'))
    assert not errs, errs[:2]


def hollow_old_entry(b, url):
    page = new_page(b, url)
    errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    new = page.evaluate("() => { const s = Pottery.makeShape({profile: Pottery.defaultProfile(), height: 1}); delete s.wall; delete s.floor; return {id: Pottery.newId(), img: 'data:,', glaze: 'Kobalt', date: '2. Januar 2026', shape: s}; }")
    assert 'wall' not in new['shape'] and 'floor' not in new['shape']
    page.evaluate('([k, v]) => localStorage.setItem(k, v)', [KEY, json.dumps([new])])
    page.reload(wait_until='domcontentloaded')
    click(page, 'Meine Werke ansehen'); wait_text(page, 'Meine Werke')
    page.get_by_role('button', name=VIEW, exact=True).click()
    page.get_by_role('heading', name='Kobalt').wait_for(state='visible')
    page.wait_for_timeout(500)
    click(page, BACKG); wait_text(page, 'Meine Werke')
    click(page, 'Weiter töpfern'); wait_text(page, 'An der Scheibe')
    hollow_attrs(page, '0.140', '0.130')
    assert not errs, errs[:2]


def undo_to_solid(b, url):
    page = new_page(b, url)
    errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    start_clay(page)
    click(page, '↶ Rückgängig')
    at_hollow(page)
    hollow_attrs(page, 'solid', '0.130')
    assert page.get_by_role('button', name='Weiter zum Formen →').is_disabled(), 'Weiter must be disabled when solid again'
    assert page.get_by_role('button', name='Fertig – Glasieren →').count() == 0, 'glazing reachable while solid'
    assert not errs, errs[:2]


FLOWS = [undo_to_solid, hollow_steps, hollow_old_entry, wet_shine, analytics, portrait_takeout_visible, gallery_no_wheel, sluggish, done_then_start, glaze_not_preselected, spin_and_padding, tools, notch_hint, lump_choice, sound_drag, edit_replaces, old_entry, undo_keeps_link, back_from_wheel, back_during_firing, no_back_after_save, gallery_view, home_hint]


def main():
    srv, url = start_server()
    failed = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=ARGS)
            only = os.environ.get('FLOW')
            for f in [f for f in FLOWS if not only or f.__name__ == only]:
                try: f(browser, url); print('PASS', f.__name__, flush=True)
                except Exception as e: failed += 1; print(f'FAIL {f.__name__}: {str(e).splitlines()[0] if str(e) else repr(e)}', flush=True)
                finally:
                    while CTX: CTX.pop().close()
            browser.close()
    finally:
        if srv: srv.terminate(); srv.wait()
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
