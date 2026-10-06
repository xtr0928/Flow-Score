# -*- coding: utf-8 -*-
"""v36 公网实测：首页「仅用户投稿」切换 + 置信度分面组 + 切回精选池。"""
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
    pg.goto(SITE + '/', wait_until='domcontentloaded', timeout=45000)
    pg.wait_for_selector('.card', timeout=30000)
    pg.wait_for_timeout(800)
    n0 = pg.locator('.card').count()
    confsec = pg.locator('.fg[data-g="conf"]').count()

    pg.select_option('#src', 'community')
    pg.wait_for_timeout(1500)
    n1 = pg.locator('.card').count()
    f1 = pg.eval_on_selector('.c-name', 'el => el.textContent').strip()
    meta1 = pg.inner_text('#meta')
    fv = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")
    subm = pg.locator('.c-sub').count()
    pg.screenshot(path=str(ROOT / 'v36_live_community_tab.png'))

    pg.select_option('#src', '')
    pg.wait_for_timeout(1500)
    n2 = pg.locator('.card').count()

    print('公网首页: 初始 cards=%d · conf 组=%d' % (n0, confsec))
    print('切「仅用户投稿」: cards=%d first=%s · 📬=%d · facets=%s' % (n1, f1[:46], subm, fv))
    print('  meta:', meta1)
    print('切回精选池: cards=%d' % n2)
    print('pageerror:', errs if errs else '无')
    ok = (n0 == 36 and n1 == 10 and 'mathematical' in f1 and fv == 'none' and n2 == 36
          and confsec == 1 and subm == 10 and not errs)
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
