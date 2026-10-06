# -*- coding: utf-8 -*-
"""API v3.8 转换：v3_7 → v3_8。src=all（无限制 = 精选池 ∪ 用户投稿）。"""
import ast
import hashlib
import shutil
import time

ts = time.strftime('%Y%m%d_%H%M%S')
src = open('flowscore_api_v3_7.py', encoding='utf-8', newline='').read()

pairs = [
    ('"""流谱 · 查询服务 v3.7（分面筛选版 · 只服务「有部署实证」的精选；本地部署 + 隔离设计）',
     '"""流谱 · 查询服务 v3.8（分面筛选版 · 默认只服务「有部署实证」的精选；本地部署 + 隔离设计）'),
    ('v3.7 = v3.6 + 社区投稿行「全员优先」入候选池（不再依赖关键词命中——投稿项目任何措辞都能被 qwen 看到）',
     'v3.8 = v3.7 + /api/items & /api/facets 支持 src=all（「无限制」= 精选池 ∪ 用户投稿）\n'
     'v3.7 = v3.6 + 社区投稿行「全员优先」入候选池（不再依赖关键词命中——投稿项目任何措辞都能被 qwen 看到）'),
    ('  GET /api/facets?q=&conf=&use=&cat=&form=&dpl=&model=&ui=   （分面计数；留一法）',
     '  GET /api/facets?q=&conf=&use=&cat=&form=&dpl=&model=&ui=&src=all   （分面计数；留一法；src=all=精选池∪投稿）'),
    ('  GET /api/items?offset=0&limit=36&sort=stars&q=&src=community&use=&cat=&form=&dpl=&model=&ui=&conf=',
     '  GET /api/items?offset=0&limit=36&sort=stars&q=&src=community|all&use=&cat=&form=&dpl=&model=&ui=&conf='),
    ("GROUPS = (('use', 'f_use'), ('cat', 'category'), ('form', 'f_form'), ('dpl', 'f_deploy'),\n"
     "          ('model', 'f_model'), ('ui', 'f_ui'), ('conf', 'confidence'))",
     "GROUPS = (('use', 'f_use'), ('cat', 'category'), ('form', 'f_form'), ('dpl', 'f_deploy'),\n"
     "          ('model', 'f_model'), ('ui', 'f_ui'), ('conf', 'confidence'))\n\n"
     "# 「无限制」范围（src=all）= 精选池 ∪ 用户投稿\n"
     "BASE_ALL = \"(verified = 1 OR (submission IS NOT NULL AND submission != ''))\""),
    ('def base_parts(qs):\n    w, args = [\'verified = 1\'], []',
     'def base_parts(qs):\n'
     "    src = (qs.get('src', [''])[0] or '').strip()[:20]\n"
     "    w, args = [BASE_ALL if src == 'all' else 'verified = 1'], []"),
    ("def where_clause(q, cat, deploy, sel):\n    w, args = ['verified = 1'], []",
     "def where_clause(q, cat, deploy, sel, base='verified = 1'):\n    w, args = [base], []"),
    ("            if sel.get('cat'):\n"
     "                cat = ''\n"
     "            wsql, args = where_clause(q, cat, deploy, sel)\n"
     "            od = SORTS[sort]",
     "            if sel.get('cat'):\n"
     "                cat = ''\n"
     "            base = BASE_ALL if src == 'all' else 'verified = 1'\n"
     "            wsql, args = where_clause(q, cat, deploy, sel, base)\n"
     "            od = SORTS[sort]"),
    ("    print(f'[api] 流谱查询服务 v3.7 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)",
     "    print(f'[api] 流谱查询服务 v3.8 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)"),
]

for i, (o, n) in enumerate(pairs, 1):
    c = src.count(o)
    assert c == 1, 'R%d 命中 %d 次（应为1）\n锚点前 100 字: %s' % (i, c, o[:100])
    src = src.replace(o, n)

ast.parse(src)
shutil.copy2('flowscore_api_v3_7.py', 'flowscore_api_v3_7.py.bak.' + ts)
open('flowscore_api_v3_8.py', 'w', encoding='utf-8', newline='').write(src)
print('v3.8 ok · md5', hashlib.md5(src.encode('utf-8')).hexdigest())
print('  语法 OK · BASE_ALL:', 'BASE_ALL' in src, '· src=all 分支:', "src == 'all'" in src)
