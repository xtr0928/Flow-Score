# -*- coding: utf-8 -*-
"""线上滚动体检：首页无限滚动是否追加（首卡是否被打头重换）/ 状态累计；其他页可否滚到底、横向溢出、控制台错误。
输出：scroll_live_bottom.png 等（cardsite 目录）"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
SITE = "https://pipeline.zufe.com.cn/"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errors = []
    pg.on('console', lambda m: errors.append(m.text[:160]) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: errors.append('PAGEERR ' + str(e)[:160]))

    def state():
        try:
            s = pg.evaluate('({shown: st.shown, total: st.total})')
        except Exception:
            s = {}
        n = pg.locator('.card').count()
        first = pg.eval_on_selector('.c-name', 'el => el.textContent') if n else ''
        meta = pg.inner_text('#meta') if pg.locator('#meta').count() else ''
        y = pg.evaluate('window.scrollY')
        h = pg.evaluate('document.documentElement.scrollHeight')
        return f"cards={n} shown={s.get('shown')} first=[{first[:36]}] Y={y:.0f} H={h} meta={meta[:44]}"

    print('═══ 首页无限滚动 ═══')
    pg.goto(SITE, wait_until='domcontentloaded', timeout=30000)
    pg.wait_for_selector('.card', timeout=20000)
    pg.wait_for_timeout(1000)
    pg.screenshot(path=str(ROOT / 'scroll_live_top.png'))
    print('初始:', state())
    for i in range(4):
        pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
        pg.wait_for_timeout(1200)
        print(f'滚底{i+1}:', state())
    print('more 文案:', pg.inner_text('#more') if pg.locator('#more').count() else '-')
    print('横向溢出:', pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth'))
    wide = pg.evaluate('''() => {
      const out = [];
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.right > window.innerWidth + 2 && r.width > 30) out.push((el.tagName + '.' + String(el.className || '')).slice(0, 60) + ' right=' + Math.round(r.right));
      });
      return out.slice(0, 8);
    }''')
    print('横向越界元素:', wide if wide else '无')
    pg.screenshot(path=str(ROOT / 'scroll_live_bottom.png'))

    print()
    print('═══ 其他页 ═══')
    for path in ['hot.html', 'intro.html', 'agent.html']:
        pg.goto(SITE + path, wait_until='domcontentloaded', timeout=30000)
        pg.wait_for_timeout(1400)
        h = pg.evaluate('document.documentElement.scrollHeight')
        vh = pg.evaluate('window.innerHeight')
        pg.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
        pg.wait_for_timeout(700)
        y = pg.evaluate('window.scrollY')
        ov = pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
        ok = (y + vh) >= (h - 6)
        print(f"{path}: H={h} vh={vh} 滚底Y={y:.0f} 到底={ok} 横向溢出={ov}")

    print()
    print('控制台错误:', errors[:12] if errors else '无')
    b.close()
print('done')
