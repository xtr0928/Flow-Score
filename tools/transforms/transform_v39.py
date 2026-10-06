# -*- coding: utf-8 -*-
"""API v3.9 转换：v3_8 → v3_9。领域简称扩展 KW_EXPAND（数模 → 数学建模）。"""
import ast
import hashlib
import shutil
import time

ts = time.strftime('%Y%m%d_%H%M%S')
src = open('flowscore_api_v3_8.py', encoding='utf-8', newline='').read()

pairs = [
    ('"""流谱 · 查询服务 v3.8（分面筛选版 · 默认只服务「有部署实证」的精选；本地部署 + 隔离设计）',
     '"""流谱 · 查询服务 v3.9（分面筛选版 · 默认只服务「有部署实证」的精选；本地部署 + 隔离设计）'),
    ('v3.8 = v3.7 + /api/items & /api/facets 支持 src=all（「无限制」= 精选池 ∪ 用户投稿）',
     'v3.9 = v3.8 + 领域简称扩展表 KW_EXPAND（「数模」→「数学建模」等；短词召回补强）\n'
     'v3.8 = v3.7 + /api/items & /api/facets 支持 src=all（「无限制」= 精选池 ∪ 用户投稿）'),
    ("def extract_keywords(need):\n"
     "    \"\"\"把混合中英文需求拆成检索片段：中文取 2 字滑窗，英文取 ≥3 字母单词。\"\"\"\n"
     "    frags = []",
     "# 领域简称扩展（中文缩写无法靠 2-gram 穷举；按需增补——键出现在需求里就追加对应全称）\n"
     "KW_EXPAND = {\n"
     "    '数模': ['数学建模'],\n"
     "}\n\n"
     "def extract_keywords(need):\n"
     "    \"\"\"把混合中英文需求拆成检索片段：中文取 2 字滑窗，英文取 ≥3 字母单词；含简称扩展。\"\"\"\n"
     "    frags = []"),
    ("        elif len(p) >= 3:\n"
     "            frags.append(p.lower())\n"
     "    seen, out = set(), []",
     "        elif len(p) >= 3:\n"
     "            frags.append(p.lower())\n"
     "    for k, vs in KW_EXPAND.items():\n"
     "        if k in need:\n"
     "            frags += vs\n"
     "    seen, out = set(), []"),
    ("    print(f'[api] 流谱查询服务 v3.8 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)",
     "    print(f'[api] 流谱查询服务 v3.9 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)"),
]

for i, (o, n) in enumerate(pairs, 1):
    c = src.count(o)
    assert c == 1, 'R%d 命中 %d 次（应为1）\n锚点前 100 字: %s' % (i, c, o[:100])
    src = src.replace(o, n)

ast.parse(src)
shutil.copy2('flowscore_api_v3_8.py', 'flowscore_api_v3_8.py.bak.' + ts)
open('flowscore_api_v3_9.py', 'w', encoding='utf-8', newline='').write(src)
print('v3.9 ok · md5', hashlib.md5(src.encode('utf-8')).hexdigest())
print('  语法 OK · KW_EXPAND:', 'KW_EXPAND' in src, '· 扩展应用:', 'frags += vs' in src)
