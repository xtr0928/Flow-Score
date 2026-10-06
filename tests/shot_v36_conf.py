# -*- coding: utf-8 -*-
"""v36/v37 视觉证据：① 顶栏新下拉「范围：精选池/仅用户投稿」② 置信度分面组（已挪到筛选栏）。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
CHROME = r"C:\Users\XXQ0928\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.goto('https://pipeline.zufe.com.cn/', wait_until='domcontentloaded', timeout=45000)
    pg.wait_for_selector('.card', timeout=30000)
    pg.wait_for_timeout(900)
    pg.screenshot(path=str(ROOT / 'v36_top_bar.png'), clip={'x': 0, 'y': 64, 'width': 1440, 'height': 120})
    pg.evaluate("var s=document.querySelector('.fg[data-g=conf]'); s.classList.add('open'); s.scrollIntoView({block:'center'});")
    pg.wait_for_timeout(600)
    pg.locator('.fg[data-g="conf"]').screenshot(path=str(ROOT / 'v36_conf_group.png'))
    print('shots ok')
    b.close()
