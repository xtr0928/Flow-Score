# -*- coding: utf-8 -*-
"""v37/v3.8 本地验收：无限制范围 / 项目升池 / 加载反馈 / 滚动回归。
前置：promote 过的测试库 + API v3.8 在 61589（FLOWSCORE_AI=0）。"""
import json
import pathlib
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
LAPI = 'http://127.0.0.1:61589'


def get(path):
    with urllib.request.urlopen(LAPI + path, timeout=30) as r:
        return json.load(r)


print('── 接口层 ──')
st = get('/api/stats')
print('stats: total=%s total_all=%s community=%s（期望 12894 / 18267 / 10）' % (st['total'], st['total_all'], st.get('community')))
d = get('/api/items?limit=3')
print('默认列表 total=%s first=%s（期望 12894 / obra/superpowers）' % (d['total'], d['items'][0]['full_name']))
a = get('/api/items?src=all&limit=3')
print('src=all total=%s（期望 12894）' % a['total'])
c = get('/api/items?src=community&limit=3')
print('src=community total=%s first=%s（期望 10 / mathematical）' % (c['total'], c['items'][0]['full_name']))
f = get('/api/facets')
fa = get('/api/facets?src=all')
print('facets matched=%s（期望 12894）· src=all matched=%s · conf=%s' % (
    f['matched'], fa['matched'], [(x['v'], x['c']) for x in f.get('conf', [])]))

print()
print('── 页面层 ──')
src = (ROOT / 'v34_index.html').read_text(encoding='utf-8')
assert "const BASE = '';" in src
(ROOT / 'v37_index_test.html').write_text(src.replace("const BASE = '';", "const BASE = '%s';" % LAPI), encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto((ROOT / 'v37_index_test.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_selector('.card', timeout=20000)
    pg.wait_for_timeout(700)
    opts = pg.eval_on_selector_all('#src option', 'els => els.map(e => e.value)')
    ver = pg.locator('footer').inner_text()
    # 滚一次：验证追加 + 尝试捕捉加载反馈
    pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
    pg.wait_for_timeout(120)
    mid = pg.inner_text('#more') if pg.locator('#more').count() else ''
    pg.wait_for_timeout(1800)
    n1 = pg.locator('.card').count()
    first1 = pg.eval_on_selector('.c-name', 'el => el.textContent').strip()
    # 切无限制
    pg.select_option('#src', 'all')
    pg.wait_for_timeout(1300)
    n2 = pg.locator('.card').count()
    meta2 = pg.inner_text('#meta')
    fv2 = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")
    pg.screenshot(path=str(ROOT / 'v37_all_mode.png'))
    # 切仅投稿
    pg.select_option('#src', 'community')
    pg.wait_for_timeout(1300)
    fv3 = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")
    n3 = pg.locator('.card').count()
    # 切回
    pg.select_option('#src', '')
    pg.wait_for_timeout(1300)
    n4 = pg.locator('.card').count()
    print('选项: %s（期望 ["", "all", "community"]）' % opts)
    print('页脚含 v37: %s' % ('v37' in ver))
    print('滚动: 加载中提示捕获=%r · 滚后 cards=%d first=%s（期望 72 / obra）' % (mid, n1, first1[:36]))
    print('无限制: cards=%d facets=%s meta=%s' % (n2, fv2, meta2[:56]))
    print('仅投稿: cards=%d facets=%s · 切回 cards=%d' % (n3, fv3, n4))
    print('pageerror:', errs if errs else '无')
    ok = (opts == ['', 'all', 'community'] and st['total'] == 12894 and a['total'] == 12894
          and f['matched'] == 12894 and n1 == 72 and 'obra' in first1 and n2 == 36
          and fv2 != 'none' and '范围：无限制' in meta2 and fv3 == 'none' and n3 == 10
          and n4 == 36 and 'v37' in ver and not errs)
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
