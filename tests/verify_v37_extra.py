# -*- coding: utf-8 -*-
"""v3.7 泛化回归：语义搜索质量抽查（投稿入池后，防止无关投稿霸榜）。"""
import json
import urllib.parse
import urllib.request

BASE = 'https://pipeline.zufe.com.cn'

def search(q, n=8):
    url = BASE + '/api/search?q=' + urllib.parse.quote(q) + '&n=' + str(n)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=150) as r:
        return json.load(r)

for q in ('把会议录音变成纪要', '爬取网页数据'):
    d = search(q)
    items = d.get('items', [])
    names = [i['full_name'] for i in items]
    xtr = sum(1 for n in names if n.startswith('xtr0928/'))
    print('需求「%s」· engine=%s · xtr0928 占比 %d/%d' % (q, d.get('engine'), xtr, len(names)))
    for nm in names[:6]:
        print('   -', nm)
    print()
