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


def new_page(browser, url, seed=None):
    ctx = browser.new_context(viewport={'width': 1180, 'height': 820}); CTX.append(ctx); page = ctx.new_page()
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
    wait_text(page, 'In die Galerie stellen')
    click(page, 'In die Galerie stellen')
    wait_text(page, 'Entfernen')


def make_work(page, glaze='Kobalt'):
    click(page, 'Ton auf die Scheibe legen')
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
    click(page, 'Ton auf die Scheibe legen')
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
    click(page, '↶ Rückgängig')
    glaze_fire_save(page)
    assert cards(page) == 1 and len(gallery(page)) == 1, f'expected 1 card, got {cards(page)}/{len(gallery(page))}'


BACK = '← Zurück zu meinem Stück'


def back_from_wheel(b, url):
    page = new_page(b, url)
    click(page, 'Ton auf die Scheibe legen')
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
    page.set_viewport_size({'width': 640, 'height': 460})
    page.set_default_timeout(300000)  # software GL: the visible firing canvas can starve the page for minutes
    click(page, 'Ton auf die Scheibe legen')
    click(page, 'Fertig – Glasieren →')
    click(page, 'In den Ofen →')
    click(page, 'Galerie (0)', exact=False)
    wait_text(page, 'Meine Werke')
    page.wait_for_timeout(8000)
    assert page.get_by_role('heading', name='Meine Werke').count() == 1, 'left the gallery on its own'
    page.get_by_role('button', name=BACK).first.click(no_wait_after=True)  # the post-click wait starves on the software-GL canvas
    wait_text(page, 'Fertig gebrannt')
    assert page.get_by_text('Fertig', exact=True).count() >= 1, 'step label not Fertig'


def no_back_after_save(b, url):
    page = new_page(b, url)
    make_work(page)
    assert page.get_by_role('button', name=BACK).count() == 0, 'back button after save'


FLOWS = [edit_replaces, old_entry, undo_keeps_link, back_from_wheel, back_during_firing, no_back_after_save]


def main():
    srv, url = start_server()
    failed = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=ARGS)
            for f in FLOWS:
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
