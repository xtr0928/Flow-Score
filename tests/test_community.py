# -*- coding: utf-8 -*-
"""社区投稿本地验收：community.html 渲染 + 侧边栏新项 + 首页回归（数字不变、滚动追加正常）。
前置：API v3.5 已跑在 127.0.0.1:61589（FLOWSCORE_AI=0，test_community_v35.db）。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
LAPI = 'http://127.0.0.1:61589'

cm = (ROOT / 'community.html').read_text(encoding='utf-8')
assert "const BASE = '';" in cm, 'community BASE 锚点缺失'
(ROOT / 'community_test.html').write_text(cm.replace("const BASE = '';", f"const BASE = '{LAPI}';"), encoding='utf-8')
ix = (ROOT / 'v34_index.html').read_text(encoding='utf-8')
assert "const BASE = '';" in ix, 'index BASE 锚点缺失'
(ROOT / 'v34_index_test.html').write_text(ix.replace("const BASE = '';", f"const BASE = '{LAPI}';"), encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))

    # ── 社区投稿页 ──
    pg.goto((ROOT / 'community_test.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_selector('.card', timeout=20000)
    pg.wait_for_timeout(700)
    n = pg.locator('.card').count()
    first = pg.eval_on_selector('.c-name', 'el => el.textContent')
    subm = pg.locator('.c-sub').count()
    side = pg.eval_on_selector_all('.side-link .lbl', 'els => els.map(e => e.textContent)')
    print('社区页: cards=%d · 投稿人徽章=%d · 首卡=%s' % (n, subm, first.strip()[:46]))
    print('  meta:', pg.inner_text('#meta'))
    print('  侧边栏:', ' | '.join(side))
    ok_cm = (n == 10 and subm == 10 and '社区投稿' in side and 'xtr0928' in first)
    pg.screenshot(path=str(ROOT / 'community_local.png'))

    # ── 首页回归 ──
    pg.goto((ROOT / 'v34_index_test.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_selector('.card', timeout=20000)
    pg.wait_for_timeout(800)
    n0 = pg.locator('.card').count()
    f0 = pg.eval_on_selector('.c-name', 'el => el.textContent')
    stats_txt = pg.inner_text('#brand .stats')
    side_ix = pg.eval_on_selector_all('.side-link .lbl', 'els => els.map(e => e.textContent)')
    print('首页: cards=%d · 首卡=%s' % (n0, f0.strip()[:46]))
    print('  顶部数字:', stats_txt.replace('\n', ' · '))
    pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
    pg.wait_for_timeout(1300)
    n1 = pg.locator('.card').count()
    print('  滚底后 cards=%d（应 %d）' % (n1, n0 + 36))
    ok_ix = (n0 == 36 and n1 == 72 and '18,267' in stats_txt and '18,277' not in stats_txt and '社区投稿' in side_ix)

    print('pageerror:', errs if errs else '无')
    print('判定:', 'PASS ✓' if (ok_cm and ok_ix) else 'FAIL ✗ cm=%s ix=%s' % (ok_cm, ok_ix))
    b.close()
