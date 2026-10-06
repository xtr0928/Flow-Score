# -*- coding: utf-8 -*-
"""本地滚动回归（修复后）：v34_index.html → 测试副本（BASE=本地 API）→ 无限滚动应为「追加」：
cards 数随 shown 同步增长、首卡稳定、无重复卡；顺带验证点分面正常重置。
前置：本地 API 已跑在 127.0.0.1:61589（FLOWSCORE_AI=0，test_flowscore_full.db）。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"

src = (ROOT / 'v34_index.html').read_text(encoding='utf-8')
assert "const BASE = '';" in src, '找不到 BASE 锚点'
(ROOT / 'v34_index_test.html').write_text(
    src.replace("const BASE = '';", "const BASE = 'http://127.0.0.1:61589';"), encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))

    def state():
        try:
            s = pg.evaluate('({shown: st.shown, total: st.total})')
        except Exception:
            s = {}
        cards = pg.locator('.card').count()
        names = pg.eval_on_selector_all('.c-name', 'els => els.map(e => e.textContent)')
        first = names[0] if names else ''
        return cards, s.get('shown'), first[:42], len(names) - len(set(names))

    pg.goto((ROOT / 'v34_index_test.html').as_uri(), wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_selector('.card', timeout=25000)
    pg.wait_for_timeout(900)
    c, sh, f0, dup = state()
    print(f'初始: cards={c} shown={sh} dup={dup} first={f0}')
    ok = (c == 36 and sh == 36 and dup == 0)

    for i in range(3):
        pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
        pg.wait_for_timeout(1400)
        c, sh, f, dup = state()
        print(f'滚底{i+1}: cards={c} shown={sh} dup={dup} first={f}')
        ok = ok and (c == sh) and (f == f0) and dup == 0

    # 快速连滚两次（并发护栏）
    pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
    pg.wait_for_timeout(120)
    pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
    pg.wait_for_timeout(1600)
    c, sh, f, dup = state()
    print(f'连滚: cards={c} shown={sh} dup={dup} first={f}')
    ok = ok and (c == sh) and (f == f0) and dup == 0

    # 分面点选 → 正常重置
    pg.evaluate('window.scrollTo(0, 0)')
    pg.wait_for_timeout(300)
    pg.locator('.fg-body .cat').first.click()
    pg.wait_for_timeout(1500)
    c, sh, f, dup = state()
    print(f'点分面: cards={c} shown={sh} dup={dup} meta={pg.inner_text("#meta")[:70]}')
    ok = ok and (c == sh) and (c <= 36) and (dup == 0)

    pg.screenshot(path=str(ROOT / 'scroll_local_fixed.png'))
    print('pageerror:', errs if errs else '无')
    print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
    b.close()
