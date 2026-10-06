# -*- coding: utf-8 -*-
"""v36 批量转换：flowscore_api_v3_5.py → v3_6；v34_index.html → v36 版（就地改，先备份）。
每条 replace 都断言命中 1 次。"""
import hashlib
import shutil
import time

ts = time.strftime('%Y%m%d_%H%M%S')


def apply(path, pairs, out=None):
    src = open(path, encoding='utf-8', newline='').read()
    for i, (o, n) in enumerate(pairs, 1):
        c = src.count(o)
        assert c == 1, '%s R%d 命中 %d 次（应为1）\n锚点前80字: %s' % (path, i, c, o[:80])
        src = src.replace(o, n)
    shutil.copy2(path, path + '.bak.' + ts)
    open(out or path, 'w', encoding='utf-8', newline='').write(src)
    return src


# ══════════════════ API v3.5 → v3.6 ══════════════════
api_pairs = [
    (
        '"""流谱 · 查询服务 v3.5（分面筛选版 · 只服务「有部署实证」的精选；本地部署 + 隔离设计）',
        '"""流谱 · 查询服务 v3.6（分面筛选版 · 只服务「有部署实证」的精选；本地部署 + 隔离设计）',
    ),
    (
        'v3.5 = v3.4 + 社区投稿通道：/api/community（submission 标记行，独立于主池/搜索/分面）',
        'v3.6 = v3.5 + ①语义搜索候选纳入社区投稿行 ②/api/items 支持 src=community ③置信度改为分面组 conf（原独立参数移除）\n'
        'v3.5 = v3.4 + 社区投稿通道：/api/community（submission 标记行，独立于主池/搜索/分面）',
    ),
    (
        '  GET /api/items?offset=0&limit=36&sort=stars&q=&conf=&use=&cat=&form=&dpl=&model=&ui=',
        '  GET /api/items?offset=0&limit=36&sort=stars&q=&src=community&use=&cat=&form=&dpl=&model=&ui=&conf=',
    ),
    (
        "GROUPS = (('use', 'f_use'), ('cat', 'category'), ('form', 'f_form'), ('dpl', 'f_deploy'),\n"
        "          ('model', 'f_model'), ('ui', 'f_ui'))",
        "GROUPS = (('use', 'f_use'), ('cat', 'category'), ('form', 'f_form'), ('dpl', 'f_deploy'),\n"
        "          ('model', 'f_model'), ('ui', 'f_ui'), ('conf', 'confidence'))",
    ),
    (
        "def base_parts(qs):\n"
        "    w, args = ['verified = 1'], []\n"
        "    conf = (qs.get('conf', [''])[0] or '').strip()[:10]\n"
        "    if conf:\n"
        "        w.append('confidence = ?'); args.append(conf)\n"
        "    q = (qs.get('q', [''])[0] or '').strip()[:120]",
        "def base_parts(qs):\n"
        "    w, args = ['verified = 1'], []\n"
        "    q = (qs.get('q', [''])[0] or '').strip()[:120]",
    ),
    (
        "def where_clause(q, cat, conf, deploy, sel):\n"
        "    w, args = ['verified = 1'], []\n"
        "    if conf:\n"
        "        w.append('confidence = ?'); args.append(conf)\n"
        "    if cat:",
        "def where_clause(q, cat, deploy, sel):\n"
        "    w, args = ['verified = 1'], []\n"
        "    if cat:",
    ),
    (
        "    sql = ('SELECT *, (' + ' + '.join(score_terms) + ') AS kw_hits FROM items WHERE verified=1 AND (' +\n"
        "           ' OR '.join(conds) + ') ORDER BY kw_hits DESC, stars DESC LIMIT 100')",
        "    sql = ('SELECT *, (' + ' + '.join(score_terms) + ') AS kw_hits FROM items WHERE '\n"
        "           \"(verified=1 OR (submission IS NOT NULL AND submission != '')) AND (\" +\n"
        "           ' OR '.join(conds) + ') ORDER BY kw_hits DESC, stars DESC LIMIT 100')",
    ),
    (
        "        offset = gi('offset', 0)\n"
        "        limit = gi('limit', 36, 100)\n"
        "        sort = qs.get('sort', ['stars'])[0]\n"
        "        sort = sort if sort in SORTS else 'stars'\n"
        "        cat = (qs.get('cat', [''])[0] or '').strip()[:40]\n"
        "        conf = (qs.get('conf', [''])[0] or '').strip()[:10]\n"
        "        deploy = (qs.get('deploy', [''])[0] or '').strip()[:20]\n"
        "        q = (qs.get('q', [''])[0] or '').strip()[:120]\n"
        "        sel = sel_lists(qs)\n"
        "        if sel.get('cat'):\n"
        "            cat = ''\n"
        "        w, args = where_clause(q, cat, conf, deploy, sel)\n"
        "        con = db(); cur = con.cursor()\n"
        "        cur.execute(f'SELECT COUNT(*) FROM items {w}', args)\n"
        "        total = cur.fetchone()[0]\n"
        "        cur.execute(f'SELECT * FROM items {w} ORDER BY {SORTS[sort]} LIMIT ? OFFSET ?',\n"
        "                    (*args, limit, offset))\n"
        "        rows = cur.fetchall()",
        "        offset = gi('offset', 0)\n"
        "        limit = gi('limit', 36, 100)\n"
        "        sort = qs.get('sort', ['stars'])[0]\n"
        "        sort = sort if sort in SORTS else 'stars'\n"
        "        src = (qs.get('src', [''])[0] or '').strip()[:20]\n"
        "        q = (qs.get('q', [''])[0] or '').strip()[:120]\n"
        "        sel = sel_lists(qs)\n"
        "        con = db(); cur = con.cursor()\n"
        "        if src == 'community':\n"
        "            w, args = [\"submission IS NOT NULL AND submission != ''\"], []\n"
        "            if q:\n"
        "                like = '%' + q.replace('%', '').replace('_', '') + '%'\n"
        "                w.append('(full_name LIKE ? OR summary LIKE ? OR desc_en LIKE ? OR topics LIKE ? OR tech LIKE ?)')\n"
        "                args += [like] * 5\n"
        "            wsql = 'WHERE ' + ' AND '.join(w)\n"
        "            od = SORTS[sort] + ', id DESC'\n"
        "        else:\n"
        "            cat = (qs.get('cat', [''])[0] or '').strip()[:40]\n"
        "            deploy = (qs.get('deploy', [''])[0] or '').strip()[:20]\n"
        "            if sel.get('cat'):\n"
        "                cat = ''\n"
        "            wsql, args = where_clause(q, cat, deploy, sel)\n"
        "            od = SORTS[sort]\n"
        "        cur.execute(f'SELECT COUNT(*) FROM items {wsql}', args)\n"
        "        total = cur.fetchone()[0]\n"
        "        cur.execute(f'SELECT * FROM items {wsql} ORDER BY {od} LIMIT ? OFFSET ?',\n"
        "                    (*args, limit, offset))\n"
        "        rows = cur.fetchall()",
    ),
    (
        "    print(f'[api] 流谱查询服务 v3.5 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)",
        "    print(f'[api] 流谱查询服务 v3.6 已启动 http://127.0.0.1:{PORT}  db={DB}  ai={ENABLE_AI}', flush=True)",
    ),
]

src_api = apply('flowscore_api_v3_5.py', api_pairs, out='flowscore_api_v3_6.py')
import ast
ast.parse(src_api)
print('API v3.6 ok · md5', hashlib.md5(src_api.encode('utf-8')).hexdigest())
print('  语法 OK · conf 组:', "('conf', 'confidence')" in src_api,
      '· src 分支:', "if src == 'community':" in src_api,
      '· 候选含投稿:', 'submission IS NOT NULL AND submission != \'\')' in src_api)

# ══════════════════ 页面 v34 → v36 ══════════════════
page_pairs = [
    (
        '    <select id="conf">\n'
        '      <option value="">置信度：全部</option>\n'
        '      <option value="high">仅高置信</option>\n'
        '      <option value="medium">仅中置信</option>\n'
        '    </select>',
        '    <select id="src" title="列表范围：默认=精选池；「仅用户投稿」=社区投稿项目">\n'
        '      <option value="">范围：精选池</option>\n'
        '      <option value="community">仅用户投稿</option>\n'
        '    </select>',
    ),
    (
        "  ['model','模型运行'],\n  ['ui','使用方式']\n];",
        "  ['model','模型运行'],\n  ['ui','使用方式'],\n  ['conf','置信度']\n];",
    ),
    (
        "const st = { q:'', conf:'', sort:'stars', ai:false, shown:0, total:0, seq:0, sel:{}, loading:false };",
        "const st = { q:'', src:'', sort:'stars', ai:false, shown:0, total:0, seq:0, sel:{}, loading:false };",
    ),
    (
        "function confLabel(k){ return k === 'high' ? '高置信' : k === 'medium' ? '中置信' : '低'; }",
        "function confLabel(k){ return k === 'high' ? '高置信' : k === 'medium' ? '中置信' : '低'; }\n"
        "function facetLabel(gid, v){ return gid === 'conf' ? confLabel(v) : v; }",
    ),
    (
        "function buildFilterParams(){\n"
        "  const p = new URLSearchParams();\n"
        "  if (st.q) p.set('q', st.q);\n"
        "  if (st.conf) p.set('conf', st.conf);\n"
        "  GROUPS.forEach(function(g){ st.sel[g[0]].forEach(function(v){ p.append(g[0], v); }); });\n"
        "  return p;\n"
        "}",
        "function buildFilterParams(){\n"
        "  const p = new URLSearchParams();\n"
        "  if (st.q) p.set('q', st.q);\n"
        "  if (st.src){ p.set('src', st.src); return p; }   // 用户投稿范围：只带关键词\n"
        "  GROUPS.forEach(function(g){ st.sel[g[0]].forEach(function(v){ p.append(g[0], v); }); });\n"
        "  return p;\n"
        "}",
    ),
    (
        "      b.innerHTML = esc(o.v) + '<span class=\"cnt\">' + o.c + '</span>';",
        "      b.innerHTML = esc(facetLabel(gid, o.v)) + '<span class=\"cnt\">' + o.c + '</span>';",
    ),
    (
        "  const p2 = reset ? api('/api/facets', buildFilterParams()).catch(() => null) : Promise.resolve(null);",
        "  facetWrap.style.display = st.src ? 'none' : '';\n"
        "  const p2 = (reset && !st.src) ? api('/api/facets', buildFilterParams()).catch(() => null) : Promise.resolve(null);",
    ),
    (
        "    GROUPS.forEach(function(g){ st.sel[g[0]].forEach(function(v){ fl.push(g[1].split(' ')[0] + '「' + v + '」'); }); });",
        "    GROUPS.forEach(function(g){ st.sel[g[0]].forEach(function(v){ fl.push(g[1].split(' ')[0] + '「' + facetLabel(g[0], v) + '」'); }); });",
    ),
    (
        "    metaEl.innerHTML = '已显示 ' + st.shown + ' / ' + st.total + ' 条'\n"
        "      + (st.q ? ' · 关键词「' + esc(st.q) + '」' : '')\n"
        "      + (st.conf ? ' · ' + confLabel(st.conf) : '')\n"
        "      + (fl.length ? ' · ' + esc(fl.join(' ')) : '')",
        "    metaEl.innerHTML = '已显示 ' + st.shown + ' / ' + st.total + ' 条'\n"
        "      + (st.q ? ' · 关键词「' + esc(st.q) + '」' : '')\n"
        "      + (st.src ? ' · 📬 用户投稿' : '')\n"
        "      + (fl.length ? ' · ' + esc(fl.join(' ')) : '')",
    ),
    (
        "    if (!st.shown && reset) grid.innerHTML = '<div class=\"empty\">没有匹配的工作流 · 换个关键词或去掉几个筛选试试</div>';",
        "    if (!st.shown && reset) grid.innerHTML = st.src ? '<div class=\"empty\">暂无用户投稿项目</div>'"
        " : '<div class=\"empty\">没有匹配的工作流 · 换个关键词或去掉几个筛选试试</div>';",
    ),
    (
        "document.getElementById('conf').addEventListener('change', function(e){ st.conf = e.target.value; st.ai = false; load(true); });",
        "document.getElementById('src').addEventListener('change', function(e){ st.src = e.target.value; st.ai = false; load(true); });",
    ),
    (
        ".c-type{font-size:10.5px;padding:2px 8px;background:var(--accent-soft);color:var(--accent);border-radius:2px;white-space:nowrap}",
        ".c-type{font-size:10.5px;padding:2px 8px;background:var(--accent-soft);color:var(--accent);border-radius:2px;white-space:nowrap}\n"
        ".c-sub{font-size:10.5px;padding:2px 8px;background:#eef4ef;color:var(--green);border-radius:2px;white-space:nowrap}",
    ),
    (
        "    (d.category ? '<span class=\"c-type\">' + esc(d.category) + '</span>' : '') + '</div>' +",
        "    (d.category ? '<span class=\"c-type\">' + esc(d.category) + '</span>' : '') +\n"
        "    (d.submission ? '<span class=\"c-sub\">📬 投稿</span>' : '') + '</div>' +",
    ),
]

src_page = apply('v34_index.html', page_pairs)
print('页面 v36 ok · md5', hashlib.md5(src_page.encode('utf-8')).hexdigest())
print('  src 选择器:', src_page.count('id="src"'), '· conf 组:', "'conf','置信度'" in src_page,
      '· facetLabel:', src_page.count('facetLabel'), '· 旧 st.conf 残留:', src_page.count('st.conf'))
