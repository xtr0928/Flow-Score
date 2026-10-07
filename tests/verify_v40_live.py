# -*- coding: utf-8 -*-
"""v40 公网实测：200 上限 / 1 秒 1 次（并发捕捉 429）/ 语义回归 / 移动端折叠 / 页脚 v38。"""
import json
import pathlib
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
SITE = 'https://pipeline.zufe.com.cn'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


def get(path, headers=None):
    h = dict(UA)
    h.update(headers or {})
    req = urllib.request.Request(SITE + path, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


Q = urllib.parse.quote
print('── 接口层 ──')
s1, d1 = get('/api/search?q=' + Q('数' * 201))
print('201 字 → %s %r' % (s1, d1.get('message')))
s2, d2 = get('/api/search?q=' + Q('数模') + '&n=6')
names = [i['full_name'] for i in d2.get('items', [])]
print('数模 → %s · %s' % (s2, names[:6]))
mixed = any(not n.startswith('xtr0928/') for n in names)
print('含非本人项目:', mixed)

# 并发捕捉 1 秒节流：第一路在途时，第二路 0.25s 后发出 → 应 429
res = {}


def bg():
    try:
        res['a'] = get('/api/search?q=' + Q('数模管线') + '&n=6')
    except Exception as e:
        res['a'] = (0, {'error': str(e)[:80]})


t = threading.Thread(target=bg)
t.start()
time.sleep(0.25)
s3, d3 = get('/api/search?q=' + Q('数模管线') + '&n=6')
t.join()
print('并发: 第一路 %s → %s' % (res['a'][0], [i['full_name'] for i in res['a'][1].get('items', [])][:4]))
print('并发: 第二路(0.25s) → %s %r（期望 429）' % (s3, d3.get('message') if s3 != 200 else '放行'))
first_hit = bool(res['a'][1].get('items')) and res['a'][1]['items'][0].get('full_name') == 'xtr0928/Multi-agent-mathematical-modeling'

print()
print('── 页面层（手机视口 390×844）──')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto(SITE + '/', wait_until='domcontentloaded', timeout=45000)
    pg.wait_for_timeout(1200)
    col0 = pg.evaluate("document.body.classList.contains('top-collapsed')")
    h0 = pg.evaluate("document.getElementById('top').getBoundingClientRect().height")
    pg.screenshot(path=str(ROOT / 'v40_live_mobile_collapsed.png'))
    pg.click('#top-toggle')
    pg.wait_for_timeout(1500)
    col1 = pg.evaluate("document.body.classList.contains('top-collapsed')")
    h1 = pg.evaluate("document.getElementById('top').getBoundingClientRect().height")
    pg.screenshot(path=str(ROOT / 'v40_live_mobile_expanded.png'))
    ver = pg.inner_text('footer')
    # 桌面复核（新标签）
    pg2 = b.new_page(viewport={'width': 1280, 'height': 900})
    pg2.goto(SITE + '/', wait_until='domcontentloaded', timeout=45000)
    pg2.wait_for_timeout(800)
    col2 = pg2.evaluate("document.body.classList.contains('top-collapsed')")
    tog2 = pg2.evaluate("getComputedStyle(document.getElementById('top-toggle')).display")
    ver2 = pg2.inner_text('footer')
    # agent 页 200 字预检
    pg3 = b.new_page(viewport={'width': 390, 'height': 844})
    pg3.goto(SITE + '/agent.html', wait_until='domcontentloaded', timeout=45000)
    pg3.fill('#need', '数' * 201)
    pg3.click('#go')
    pg3.wait_for_timeout(400)
    stx = pg3.inner_text('#status')
    print('手机: 默认收起=%s · 顶部高=%.0fpx' % (col0, h0))
    print('点开: 收起=%s · 顶部高=%.0fpx' % (col1, h1))
    print('页脚含 v38: %s' % ('v38' in ver))
    print('桌面: 收起=%s · 按钮=%s · 页脚含 v38: %s' % (col2, tog2, 'v38' in ver2))
    print('agent 201 字状态: %r' % stx)
    print('pageerror:', errs if errs else '无')
    ok_page = (col0 is True and h0 < 140 and col1 is False and h1 > 260
               and 'v38' in ver and col2 is False and tog2 == 'none' and 'v38' in ver2
               and '200' in stx and not errs)
    b.close()

ok = (s1 == 400 and '200' in d1.get('message', '') and s2 == 200 and mixed
      and s3 == 429 and d3.get('error') == 'too_frequent' and first_hit and ok_page)
print()
print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
