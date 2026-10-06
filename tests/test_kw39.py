# -*- coding: utf-8 -*-
"""v3.9 本地验证：简称扩展后候选池是否带到「数学建模」仓库。"""
import os
import sys
import sqlite3

os.environ['FLOWSCORE_DB'] = r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite/test_community_v38.db"
sys.path.insert(0, r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
import flowscore_api_v3_9 as api

con = sqlite3.connect(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite/test_community_v38.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

print("extract_keywords('数模')      =", api.extract_keywords('数模'))
print("extract_keywords('数模管线')  =", api.extract_keywords('数模管线'))
print()

for need in ('数模', '数模管线'):
    pool = api.search_candidates(cur, need)
    names = [d['full_name'] for _, d in pool]
    xtr = sum(1 for n in names if n.startswith('xtr0928/'))
    math = [n for n in names if any(t in n.lower() for t in ('mathmodel', 'math-model', 'automm', 'cumcm'))]
    seed = [d for _, d in pool if d['full_name'] == 'xtr0928/Multi-agent-mathematical-modeling']
    print('需求「%s」· pool=%d · xtr0928=%d · 建模相关=%d' % (need, len(pool), xtr, len(math)))
    print('  建模相关入池:', math[:6])
    if seed:
        print('  数模管线入池 ✓ · kw_hits=%s' % seed[0].get('kw_hits', '-'))
    print()

# 泛化回归：普通需求不崩、不霸榜
for need in ('把会议录音变成纪要', '爬取网页数据'):
    pool = api.search_candidates(cur, need)
    xtr = sum(1 for _, d in pool if d['full_name'].startswith('xtr0928/'))
    print('回归「%s」· pool=%d · xtr0928 仅 %d 条' % (need, len(pool), xtr))
con.close()
