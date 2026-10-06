# -*- coding: utf-8 -*-
"""页面 v37 转换：v34_index.html 就地改（先备份）。
内容：范围下拉+「无限制」、无限制保留分面、加载反馈（⏳+脉冲）、追加载失败不毁列表、页脚版本标记。"""
import hashlib
import shutil
import time

ts = time.strftime('%Y%m%d_%H%M%S')
p = 'v34_index.html'
src = open(p, encoding='utf-8', newline='').read()

pairs = [
    # R1 范围下拉：加「无限制」
    (
        '    <select id="src" title="列表范围：默认=精选池；「仅用户投稿」=社区投稿项目">\n'
        '      <option value="">范围：精选池</option>\n'
        '      <option value="community">仅用户投稿</option>\n'
        '    </select>',
        '    <select id="src" title="列表范围：精选池=有部署实证；无限制=精选池+用户投稿；仅用户投稿=社区投稿项目">\n'
        '      <option value="">范围：精选池</option>\n'
        '      <option value="all">范围：无限制</option>\n'
        '      <option value="community">范围：仅用户投稿</option>\n'
        '    </select>',
    ),
    # R2 参数构建：community 之外都带分面参数
    (
        'function buildFilterParams(){\n'
        '  const p = new URLSearchParams();\n'
        '  if (st.q) p.set(\'q\', st.q);\n'
        '  if (st.src){ p.set(\'src\', st.src); return p; }   // 用户投稿范围：只带关键词\n'
        '  GROUPS.forEach(function(g){ st.sel[g[0]].forEach(function(v){ p.append(g[0], v); }); });\n'
        '  return p;\n'
        '}',
        'function buildFilterParams(){\n'
        '  const p = new URLSearchParams();\n'
        '  if (st.q) p.set(\'q\', st.q);\n'
        '  if (st.src) p.set(\'src\', st.src);\n'
        '  if (st.src === \'community\') return p;   // 仅投稿：单列，不带分面\n'
        '  GROUPS.forEach(function(g){ st.sel[g[0]].forEach(function(v){ p.append(g[0], v); }); });\n'
        '  return p;\n'
        '}',
    ),
    # R3 分面隐藏：只有「仅用户投稿」隐藏
    (
        "  facetWrap.style.display = st.src ? 'none' : '';",
        "  facetWrap.style.display = (st.src === 'community') ? 'none' : '';",
    ),
    # R4 分面抓取：community 之外都刷新
    (
        "  const p2 = (reset && !st.src) ? api('/api/facets', buildFilterParams()).catch(() => null) : Promise.resolve(null);",
        "  const p2 = (reset && st.src !== 'community') ? api('/api/facets', buildFilterParams()).catch(() => null) : Promise.resolve(null);",
    ),
    # R5 加载反馈：追加加载时显示「正在加载更多…」
    (
        '  const seq = ++st.seq;\n'
        '  st.loading = true;\n'
        "  const p1 = api('/api/items', buildParams(st.shown));",
        '  const seq = ++st.seq;\n'
        '  st.loading = true;\n'
        "  if (!reset){ moreEl.textContent = '⏳ 正在加载更多…'; moreEl.classList.add('loading'); }\n"
        "  const p1 = api('/api/items', buildParams(st.shown));",
    ),
    # R6 加载完成：撤掉脉冲、恢复文案
    (
        "    moreEl.textContent = (st.shown < st.total) ? '向下滚动加载更多' : (st.total ? '已显示全部 ' + st.total + ' 条' : '');",
        "    moreEl.classList.remove('loading');\n"
        "    moreEl.textContent = (st.shown < st.total) ? '向下滚动加载更多' : (st.total ? '已显示全部 ' + st.total + ' 条' : '');",
    ),
    # R7 失败处理：追加失败不毁列表，底部给重试
    (
        '  }).catch(function(){\n'
        '    if (seq !== st.seq) return;\n'
        '    st.loading = false;\n'
        "    grid.innerHTML = '<div class=\"empty\">数据加载失败 · <a href=\"javascript:location.reload()\">点击重试</a></div>';\n"
        '  });',
        '  }).catch(function(){\n'
        '    if (seq !== st.seq) return;\n'
        "    moreEl.classList.remove('loading');\n"
        '    if (reset){\n'
        '      st.loading = false;\n'
        "      grid.innerHTML = '<div class=\"empty\">数据加载失败 · <a href=\"javascript:location.reload()\">点击重试</a></div>';\n"
        '    } else {\n'
        "      moreEl.innerHTML = '⚠ 加载失败 · <a href=\"javascript:void(0)\" id=\"retry-more\">点击重试</a>';\n"
        "      const rm = document.getElementById('retry-more');\n"
        "      if (rm) rm.addEventListener('click', function(){ st.loading = false; load(false); });\n"
        '      /* 保持 st.loading=true：防观察器自动重试风暴；点重试或换筛选即恢复 */\n'
        '    }\n'
        '  });',
    ),
    # R8 meta：范围标注
    (
        "      + (st.src ? ' · 📬 用户投稿' : '')",
        "      + (st.src === 'community' ? ' · 📬 用户投稿' : (st.src === 'all' ? ' · 范围：无限制' : ''))",
    ),
    # R9 空态文案：仅投稿专属
    (
        "    if (!st.shown && reset) grid.innerHTML = st.src ? '<div class=\"empty\">暂无用户投稿项目</div>' : '<div class=\"empty\">没有匹配的工作流 · 换个关键词或去掉几个筛选试试</div>';",
        "    if (!st.shown && reset) grid.innerHTML = (st.src === 'community') ? '<div class=\"empty\">暂无用户投稿项目</div>' : '<div class=\"empty\">没有匹配的工作流 · 换个关键词或去掉几个筛选试试</div>';",
    ),
    # R10 加载中脉冲动画
    (
        '</style>\n</head>',
        '#more.loading{animation:rpulse 1.1s ease-in-out infinite}\n'
        '@keyframes rpulse{50%{opacity:.4}}\n'
        '</style>\n</head>',
    ),
    # R11 页脚版本标记（排查旧缓存）
    (
        '  <span id="f-built"></span>',
        '  <span id="f-built"></span>\n'
        '  <span title="前端版本标记——如果不显示 v37，说明浏览器还在用旧缓存，Ctrl+F5 强刷">前端 v37</span>',
    ),
]

for i, (o, n) in enumerate(pairs, 1):
    c = src.count(o)
    assert c == 1, 'R%d 命中 %d 次（应为1）\n锚点前 100 字: %s' % (i, c, o[:100])
    src = src.replace(o, n)

shutil.copy2(p, p + '.bak.' + ts)
open(p, 'w', encoding='utf-8', newline='').write(src)
print('页面 v37 ok · md5', hashlib.md5(src.encode('utf-8')).hexdigest())
print('  无限制选项:', src.count('范围：无限制'), '· 加载反馈:', src.count('正在加载更多'),
      '· v37 标记:', src.count('前端 v37'), '· retry-more:', src.count('retry-more'))
