# -*- coding: utf-8 -*-
"""公网实测：community.html 渲染 + 从首页侧边栏点击进入。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
SITE = 'https://pipeline.zufe.com.cn'

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))

    # 1) 直接打开社区页
    pg.goto(SITE + '/community.html', wait_until='domcontentloaded', timeout=45000)
    pg.wait_for_selector('.card', timeout=30000)
    pg.wait_for_timeout(800)
    n = pg.locator('.card').count()
    first = pg.eval_on_selector('.c-name', 'el => el.textContent').strip()
    meta = pg.inner_text('#meta')
    stats = pg.inner_text('#brand .stats').replace('\n', ' · ')
    pg.screenshot(path=str(ROOT / 'community_live.png'))

    # 2) 从首页侧边栏点入
    pg.goto(SITE + '/', wait_until='domcontentloaded', timeout=45000)
    pg.wait_for_selector('.card', timeout=30000)
    pg.click('a.side-link[href="community.html"]')
    pg.wait_for_load_state('domcontentloaded')
    pg.wait_for_selector('.card', timeout=30000)
    pg.wait_for_timeout(600)
    n2 = pg.locator('.card').count()

    print('直开社区页: cards=%d · first=%s' % (n, first))
    print('  meta:', meta)
    print('  顶栏:', stats)
    print('从首页点入: cards=%d · url=%s' % (n2, pg.url))
    print('pageerror:', errs if errs else '无')
    ok = (n == 10 and 'Watercooler' in first and n2 == 10 and pg.url.endswith('community.html') and not errs)
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
