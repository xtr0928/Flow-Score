# -*- coding: utf-8 -*-
"""v37 公网实测：无限制范围 / 加载反馈捕捉 / 滚动追加 / 投稿切换 / 头部统计 12,894。"""
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
    stats = pg.inner_text('#stats')
    pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
    pg.wait_for_timeout(100)
    mid = pg.inner_text('#more')
    pg.wait_for_timeout(2000)
    n1 = pg.locator('.card').count()
    first1 = pg.eval_on_selector('.c-name', 'el => el.textContent').strip()
    pg.select_option('#src', 'all')
    pg.wait_for_timeout(1400)
    n2 = pg.locator('.card').count()
    meta2 = pg.inner_text('#meta')
    fv2 = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")
    pg.screenshot(path=str(ROOT / 'v38_live_all.png'))
    pg.select_option('#src', 'community')
    pg.wait_for_timeout(1400)
    n3 = pg.locator('.card').count()
    fv3 = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")
    pg.screenshot(path=str(ROOT / 'v38_live_community.png'))
    pg.select_option('#src', '')
    pg.wait_for_timeout(1400)
    n4 = pg.locator('.card').count()
    print('初始: cards=%d · 头部统计=%s' % (n0, stats[:64]))
    print('滚动: 加载中捕获=%r · cards=%d first=%s' % (mid, n1, first1[:40]))
    print('无限制: cards=%d facets=%s meta=%s' % (n2, fv2, meta2[:58]))
    print('仅投稿: cards=%d facets=%s · 切回: cards=%d' % (n3, fv3, n4))
    print('pageerror:', errs if errs else '无')
    ok = (n0 == 36 and n1 == 72 and 'obra' in first1 and n2 == 36 and fv2 != 'none'
          and '范围：无限制' in meta2 and n3 == 10 and fv3 == 'none' and n4 == 36
          and '12,894' in stats and not errs)
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
