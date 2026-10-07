# -*- coding: utf-8 -*-
"""页面 v38 转换（就地改，先备份 .bak）：
① 首页移动端：顶部搜索区可折叠（默认收起，localStorage fs_top 记忆）
② 首页语义搜索：200 字前端预检 + 服务端错误提示（too_long / too_frequent）透传
③ agent 页：同样 200 字预检 + 错误提示 + 使用规范说明。"""
import hashlib
import pathlib
import shutil
import time

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
TS = time.strftime('%Y%m%d_%H%M%S')


def md5s(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()[:10]


def apply(fname, pairs):
    p = ROOT / fname
    src = p.read_text(encoding='utf-8')
    bak = p.with_suffix(p.suffix + '.bak.' + TS)
    shutil.copy2(p, bak)
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        assert n == 1, f'{fname} 锚点{i} 命中 {n} 次: {old[:70]!r}'
        src = src.replace(old, new)
    p.write_text(src, encoding='utf-8', newline='\n')
    print(f'{fname} ok · md5 {md5s(src)} · 备份 {bak.name}')
    return src


# ══════════ 首页 v38 ══════════
idx_pairs = [
    # ① 基础样式：折叠按钮（桌面隐藏，手机端由媒体查询打开）
    ('.ai-btn[disabled]{opacity:.55;cursor:wait}\n.cat{font-size:12.5px;',
     '.ai-btn[disabled]{opacity:.55;cursor:wait}\n'
     '#top-toggle{display:none;align-items:center;gap:8px;width:100%;padding:9px 12px;background:var(--card);'
     'border:1px solid var(--rule);border-radius:4px;font-size:13.5px;font-family:var(--sans);color:var(--ink-2);'
     'cursor:pointer;transition:.15s}\n'
     '#top-toggle:hover{border-color:var(--accent);color:var(--accent)}\n'
     '#top-toggle .arr{margin-left:auto;color:var(--ink-3);font-size:11px;transition:transform .18s}\n'
     '.cat{font-size:12.5px;'),
    # ② 手机端媒体查询：展开折叠规则
    ('  body.side-collapsed #side{width:auto;padding:10px 16px}\n  body.side-collapsed .lbl{display:inline}\n}',
     '  body.side-collapsed #side{width:auto;padding:10px 16px}\n  body.side-collapsed .lbl{display:inline}\n'
     '  /* 顶部搜索区：手机端可折叠（默认收起，localStorage 记忆 fs_top） */\n'
     '  #top-toggle{display:flex}\n'
     '  body.top-collapsed #top-in{padding:10px 16px 12px}\n'
     '  body.top-collapsed #brand,body.top-collapsed #controls,body.top-collapsed #facets{display:none}\n'
     '  body:not(.top-collapsed) #top-toggle .arr{transform:rotate(180deg)}\n}'),
    # ③ 结构：折叠按钮置于顶部区第一行
    ('<header id="top"><div id="top-in">\n  <div id="brand">',
     '<header id="top"><div id="top-in">\n'
     '  <button id="top-toggle" type="button" title="展开或收起搜索与筛选">'
     '<span>🔎 搜索与筛选</span><span class="arr">▾</span></button>\n'
     '  <div id="brand">'),
    # ④ 折叠逻辑（追加在原侧边栏脚本尾）
    ('  sync();\n})();</script>',
     '  sync();\n})();\n'
     '(function(){\n'
     "  var KEY='fs_top', b=document.body, t=document.getElementById('top-toggle');\n"
     '  if(!t) return;\n'
     "  var mq=window.matchMedia('(max-width:820px)');\n"
     '  var saved=null; try{ saved=localStorage.getItem(KEY); }catch(e){}\n'
     '  function apply(){\n'
     "    var col = mq.matches ? (saved===null ? true : saved==='1') : false;\n"
     "    b.classList.toggle('top-collapsed', col);\n"
     '  }\n'
     '  apply();\n'
     "  try{ mq.addEventListener('change', apply); }catch(e){}\n"
     "  t.addEventListener('click',function(){\n"
     "    var col=!b.classList.contains('top-collapsed');\n"
     "    b.classList.toggle('top-collapsed', col);\n"
     "    saved=col?'1':'0';\n"
     '    try{ localStorage.setItem(KEY,saved); }catch(e){}\n'
     "    if(!col){ var q=document.getElementById('q'); if(q) setTimeout(function(){q.focus();},80); }\n"
     '  });\n'
     '})();</script>'),
    # ⑤ api()：把服务端错误码/说明透传出来
    ("function api(path, params){\n  const qs = params ? ('?' + params.toString()) : '';\n"
     "  return fetch(BASE + path + qs, {cache:'no-cache'}).then(r => {\n"
     "    if (!r.ok) throw new Error('HTTP ' + r.status);\n"
     '    return r.json();\n  });\n}',
     "function api(path, params){\n  const qs = params ? ('?' + params.toString()) : '';\n"
     "  return fetch(BASE + path + qs, {cache:'no-cache'}).then(r => {\n"
     '    if (!r.ok) return r.json().catch(function(){ return {}; }).then(function(j){\n'
     "      var e = new Error(j.message || ('HTTP ' + r.status)); e.code = j.error || ''; throw e;\n"
     '    });\n'
     '    return r.json();\n  });\n}'),
    # ⑥ aiSearch：前端 200 字预检
    ("  if (!q){ document.getElementById('q').focus(); return; }\n  st.ai = true; st.seq++;",
     "  if (!q){ document.getElementById('q').focus(); return; }\n"
     '  if (q.length > 200){\n'
     "    grid.innerHTML = '<div class=\"empty\">需求最多 200 字（当前 ' + q.length + ' 字）· 请精简后再试</div>';\n"
     "    metaEl.textContent = '语义搜索未执行'; moreEl.textContent = '';\n"
     '    return;\n'
     '  }\n'
     '  st.ai = true; st.seq++;'),
    # ⑦ aiSearch：错误分支展示具体原因
    ("  }).catch(function(){\n    grid.innerHTML = '<div class=\"empty\">语义搜索暂不可用</div>';\n"
     '    st.ai = false; load(true);\n  }).finally(function(){ aiBtn.disabled = false; });',
     '  }).catch(function(e){\n'
     "    const code = (e && e.code) || '';\n"
     "    let msg = '语义搜索暂不可用（' + esc((e && e.message) || '网络错误') + '）';\n"
     "    if (code === 'too_long') msg = '需求最多 200 字，请精简后再试';\n"
     "    else if (code === 'too_frequent') msg = '搜索每 1 秒仅限 1 次，请稍候再试';\n"
     "    grid.innerHTML = '<div class=\"empty\">' + msg + '</div>';\n"
     "    metaEl.textContent = '语义搜索未完成 · 修改条件后恢复常规列表';\n"
     "    if (code !== 'too_long' && code !== 'too_frequent'){ st.ai = false; load(true); }\n"
     '  }).finally(function(){ aiBtn.disabled = false; });'),
    # ⑧ 页脚版本标记
    ('<span title="前端版本标记——如果不显示 v37，说明浏览器还在用旧缓存，Ctrl+F5 强刷">前端 v37</span>',
     '<span title="前端版本标记——如果不显示 v38，说明浏览器还在用旧缓存，Ctrl+F5 强刷">前端 v38</span>'),
]

# ══════════ agent 页 ══════════
agt_pairs = [
    # ① 前端 200 字预检 + 服务端错误说明透传
    ("async function run(){\n  const need = needEl.value.trim();\n  if (!need){ needEl.focus(); return; }\n"
     '  goEl.disabled = true;',
     'async function run(){\n  const need = needEl.value.trim();\n  if (!need){ needEl.focus(); return; }\n'
     '  if (need.length > 200){\n'
     "    statusEl.textContent = '最多 200 字（当前 ' + need.length + ' 字）· 请精简后再试';\n"
     '    needEl.focus(); return;\n'
     '  }\n'
     '  goEl.disabled = true;'),
    ("    if (!r.ok) throw new Error('HTTP ' + r.status);",
     '    if (!r.ok){\n'
     '      const j = await r.json().catch(function(){ return {}; });\n'
     "      throw new Error(j.message || ('HTTP ' + r.status));\n"
     '    }'),
    # ② 使用规范说明
    ('    接口清单见 <a href="llms.txt">llms.txt</a> · 全站浏览见 <a href="./">首页</a>。',
     '    接口清单见 <a href="llms.txt">llms.txt</a> · 全站浏览见 <a href="./">首页</a>。<br>\n'
     '    使用规范：查询 ≤200 字 · 每秒限 1 次 · 无状态单轮（不带上下文）· 只返回管线地址列表。'),
    # ③ 页脚版本
    ('<span>本地 Qwen 语义挑选 · 失败自动回退关键词</span>',
     '<span>本地 Qwen 语义挑选 · 失败自动回退关键词 · 接口 v4.0</span>'),
]

apply('v34_index.html', idx_pairs)
apply('agent.html', agt_pairs)
print('页面 v38 + agent 转换全部完成')
