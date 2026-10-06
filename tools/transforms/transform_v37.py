# -*- coding: utf-8 -*-
"""v3.7 转换：v3_6 → v3_7。投稿行全员优先入候选池。"""
import ast
import hashlib
import shutil
import time

ts = time.strftime('%Y%m%d_%H%M%S')
src = open('flowscore_api_v3_6.py', encoding='utf-8', newline='').read()

pairs = [
    (
        '"""流谱 · 查询服务 v3.6（分面筛选版 · 只服务「有部署实证」的精选；本地部署 + 隔离设计）',
        '"""流谱 · 查询服务 v3.7（分面筛选版 · 只服务「有部署实证」的精选；本地部署 + 隔离设计）',
    ),
    (
        'v3.6 = v3.5 + ①语义搜索候选纳入社区投稿行 ②/api/items 支持 src=community ③置信度改为分面组 conf（原独立参数移除）',
        'v3.7 = v3.6 + 社区投稿行「全员优先」入候选池（不再依赖关键词命中——投稿项目任何措辞都能被 qwen 看到）\n'
        'v3.6 = v3.5 + ①语义搜索候选纳入社区投稿行 ②/api/items 支持 src=community ③置信度改为分面组 conf（原独立参数移除）',
    ),
    (
        "    rows = cur.execute(sql, score_args + args).fetchall()\n"
        "    pool = [(r['id'], dict(r)) for r in rows]\n"
        "    if len(pool) < 30:",
        "    rows = cur.execute(sql, score_args + args).fetchall()\n"
        "    pool = [(r['id'], dict(r)) for r in rows]\n"
        "    # 社区投稿行全员优先入池（当前量级 ≤50；保证投稿项目无论何种措辞都能被 qwen 看到）\n"
        "    seen = {i for i, _ in pool}\n"
        "    subs = []\n"
        "    for r in cur.execute(\"SELECT * FROM items WHERE submission IS NOT NULL AND submission != '' ORDER BY id DESC LIMIT 50\"):\n"
        "        if r['id'] not in seen:\n"
        "            subs.append((r['id'], dict(r)))\n"
        "            seen.add(r['id'])\n"
        "    pool = subs + pool\n"
        "    if len(pool) < 30:",
    ),
    (
        "    print(f'[api] 流谱查询服务 v3.6 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)",
        "    print(f'[api] 流谱查询服务 v3.7 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)",
    ),
]

for i, (o, n) in enumerate(pairs, 1):
    c = src.count(o)
    assert c == 1, 'R%d 命中 %d 次（应为1）\n锚点前80字: %s' % (i, c, o[:80])
    src = src.replace(o, n)

ast.parse(src)
shutil.copy2('flowscore_api_v3_6.py', 'flowscore_api_v3_6.py.bak.' + ts)
open('flowscore_api_v3_7.py', 'w', encoding='utf-8', newline='').write(src)
print('v3.7 ok · md5', hashlib.md5(src.encode('utf-8')).hexdigest())
print('语法 OK · subs 优先入池:', 'pool = subs + pool' in src)
