# -*- coding: utf-8 -*-
"""v36 本地验收：① /api/search 候选池纳入投稿行（数模管线）② 首页「仅用户投稿」切换 ③ 置信度分面组 ④ 精选池回归。
前置：API v3.6 已跑在 127.0.0.1:61589（FLOWSCORE_AI=0，test_community_v35.db）。"""
import json
import pathlib
import sqlite3
import urllib.request
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
LAPI = 'http://127.0.0.1:61589'


def get(path):
    with urllib.request.urlopen(LAPI + path, timeout=60) as r:
        return json.load(r)


# ── 1) 候选池手工核对（与 API search_candidates 相同 WHERE）──
con = sqlite3.connect(str(ROOT / 'test_community_v35.db'))
rows = con.execute(
    "SELECT full_name FROM items WHERE (verified=1 OR (submission IS NOT NULL AND submission != '')) "
    "AND (full_name LIKE '%管线%' OR summary LIKE '%管线%' OR desc_en LIKE '%管线%' OR topics LIKE '%管线%')"
).fetchall()
hit = [r[0] for r in rows if 'mathematical' in r[0]]
print('① 候选池含数模管线:', bool(hit), hit[:1])
con.close()

# ── 2) /api/search（本地无 AI → 关键词回退，验证不崩 + 结构正常）──
s = get('/api/search?q=' + quote('数模管线') + '&n=10')
print('② search engine:', s['engine'], '· 返回', len(s['items']), '条')

# ── 3) items src=community ──
c = get('/api/items?src=community&limit=36&sort=stars')
print('③ src=community total:', c['total'], '· 首条:', c['items'][0]['full_name'] if c['items'] else None)

# ── 4) facets 含 conf 组 ──
f = get('/api/facets')
print('④ facets conf:', [(x['v'], x['c']) for x in f.get('conf', [])])

# ── 5) 精选池回归 ──
d = get('/api/items?limit=3')
stt = get('/api/stats')
print('⑤ 默认列表 total:', d['total'], '· 首条:', d['items'][0]['full_name'],
      '· stats:', stt['total'], stt['total_all'], stt.get('community'))

# ── 6) 页面行为 ──
src = (ROOT / 'v34_index.html').read_text(encoding='utf-8')
assert "const BASE = '';" in src, 'BASE 锚点缺失'
(ROOT / 'v36_index_test.html').write_text(src.replace("const BASE = '';", f"const BASE = '{LAPI}';"), encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto((ROOT / 'v36_index_test.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_selector('.card', timeout=20000)
    pg.wait_for_timeout(700)
    n0 = pg.locator('.card').count()
    first0 = pg.eval_on_selector('.c-name', 'el => el.textContent').strip()
    confsec = pg.locator('.fg[data-g="conf"]').count()
    confchips = pg.locator('.fg[data-g="conf"] .cat').count()

    pg.select_option('#src', 'community')
    pg.wait_for_timeout(1300)
    n1 = pg.locator('.card').count()
    first1 = pg.eval_on_selector('.c-name', 'el => el.textContent').strip()
    meta1 = pg.inner_text('#meta')
    facets_vis = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")
    subm_chips = pg.locator('.c-sub').count()
    pg.screenshot(path=str(ROOT / 'v36_community_tab.png'))

    pg.select_option('#src', '')
    pg.wait_for_timeout(1300)
    n2 = pg.locator('.card').count()
    facets_vis2 = pg.evaluate("getComputedStyle(document.getElementById('facets')).display")

    print('⑥ 初始 cards=%d first=%s · conf 组 section=%d chips=%d' % (n0, first0[:44], confsec, confchips))
    print('   切「仅用户投稿」: cards=%d first=%s · 📬徽章=%d · facets=%s' % (n1, first1[:44], subm_chips, facets_vis))
    print('   meta:', meta1)
    print('   切回精选池: cards=%d · facets=%s' % (n2, facets_vis2))
    print('pageerror:', errs if errs else '无')

    ok = (bool(hit) and n1 == 10 and 'mathematical' in first1 and confsec == 1 and confchips >= 2
          and facets_vis == 'none' and subm_chips == 10 and n2 == 36 and facets_vis2 != 'none' and not errs)
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
