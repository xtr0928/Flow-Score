# -*- coding: utf-8 -*-
"""v38 移动端验收（file://）：顶部可折叠（默认收起/展开/记忆）+ 桌面不受影响 + agent 页 200 字预检。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    errs = []
    # ── 手机视口 ──
    pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto((ROOT / 'v34_index.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_timeout(600)
    has_ls = pg.evaluate("(function(){try{localStorage.setItem('t_probe','1');localStorage.removeItem('t_probe');return true;}catch(e){return false;}})()")
    col0 = pg.evaluate("document.body.classList.contains('top-collapsed')")
    h0 = pg.evaluate("document.getElementById('top').getBoundingClientRect().height")
    tog = pg.evaluate("getComputedStyle(document.getElementById('top-toggle')).display")
    ctl = pg.evaluate("getComputedStyle(document.getElementById('controls')).display")
    pg.screenshot(path=str(ROOT / 'v38_mobile_collapsed.png'))
    pg.click('#top-toggle')
    pg.wait_for_timeout(400)
    col1 = pg.evaluate("document.body.classList.contains('top-collapsed')")
    h1 = pg.evaluate("document.getElementById('top').getBoundingClientRect().height")
    ls1 = pg.evaluate("localStorage.getItem('fs_top')")
    pg.screenshot(path=str(ROOT / 'v38_mobile_expanded.png'))
    pg.reload(wait_until='domcontentloaded')
    pg.wait_for_timeout(500)
    col2 = pg.evaluate("document.body.classList.contains('top-collapsed')")
    pg.click('#top-toggle')
    pg.wait_for_timeout(300)
    col3 = pg.evaluate("document.body.classList.contains('top-collapsed')")
    # ── 桌面视口（新标签，状态隔离）──
    pg2 = b.new_page(viewport={'width': 1280, 'height': 900})
    pg2.goto((ROOT / 'v34_index.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg2.wait_for_timeout(500)
    col4 = pg2.evaluate("document.body.classList.contains('top-collapsed')")
    tog2 = pg2.evaluate("getComputedStyle(document.getElementById('top-toggle')).display")
    ctl2 = pg2.evaluate("getComputedStyle(document.getElementById('controls')).display")
    # ── agent 页 200 字预检 ──
    pg3 = b.new_page(viewport={'width': 390, 'height': 844})
    pg3.goto((ROOT / 'agent.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg3.fill('#need', '数' * 201)
    pg3.click('#go')
    pg3.wait_for_timeout(400)
    stx = pg3.inner_text('#status')
    print('手机: 默认收起=%s · 顶部高=%.0fpx · 按钮=%s · controls=%s' % (col0, h0, tog, ctl))
    print('点开: 收起=%s · 顶部高=%.0fpx · localStorage=%r（localStorage 可用=%s）' % (col1, h1, ls1, has_ls))
    print('刷新后=%s（期望展开记忆）· 再点收起=%s' % (col2, col3))
    print('桌面: 收起=%s · 按钮=%s · controls=%s' % (col4, tog2, ctl2))
    print('agent 201 字状态: %r' % stx)
    print('pageerror:', errs if errs else '无')
    ok_persist = (col2 is False and col3 is True and ls1 == '0') if has_ls else True
    ok = (col0 is True and h0 < 130 and tog == 'flex' and ctl == 'none'
          and col1 is False and h1 > 260 and ok_persist
          and col4 is False and tog2 == 'none' and ctl2 != 'none'
          and '200' in stx and not errs)
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
