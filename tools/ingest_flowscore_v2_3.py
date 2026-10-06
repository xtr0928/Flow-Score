#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流谱 · 全量入库 v2.1（在服务器上运行；v2.1 = v2 + 用途分面 f_use）
把数据（JSON 或 xlsx，阿米娅交付格式均可）归一化 → SQLite（供查询服务）→ 再生成静态文件。
  usage: python3 ingest_flowscore_v2.py --json <全量.json 或 全量.xlsx> [--old /tmp/gh_pipe_judged.json]
         [--db /home/zhenjinchao/flowscore/flowscore.db] [--static /home/zhenjinchao/pipelines]
安全：只写自己的产物（db.new→原子替换、api/workflows.json、llms.txt），改动前给旧 db 留 .bak
分面（离线关键词粗分，标注于字段）：
  f_use 用途分类（文档处理/视频生成/图像处理/音频语音/数据采集/流程自动化/科研学术/内容创作/编程开发/其他）
  f_form 形态 / f_deploy 部署方式 / f_model 模型运行 / f_ui 使用方式（见 tag_* 函数）
"""
import argparse, json, os, re, shutil, sqlite3, sys, time, zipfile
import xml.etree.ElementTree as ET

STAMP = time.strftime('%Y%m%d_%H%M%S')
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

# ───────────────────────── xlsx 读取（标准库，无第三方依赖） ─────────────────────────
def read_xlsx(path):
    """返回 [(sheet_name, [row_dict, ...]), ...]；第一行为表头。标准库解析，防注入不执行任何内容。"""
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    wb = None
    if 'xl/workbook.xml' in z.namelist():
        wb = ET.fromstring(z.read('xl/workbook.xml'))
    names = []
    if wb is not None:
        for sh in wb.iter(NS + 'sheet'):
            names.append(sh.get('name') or '')
    sheets = sorted([n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml$', n)],
                    key=lambda n: int(re.search(r'(\d+)', n).group(1)))
    out = []
    for i, sn in enumerate(sheets):
        root = ET.fromstring(z.read(sn))
        rows = []
        for row in root.iter(NS + 'row'):
            cells = {}
            for c in row.findall(NS + 'c'):
                ref = c.get('r') or ''
                col = ''.join(ch for ch in ref if ch.isalpha())
                t = c.get('t')
                v = c.find(NS + 'v')
                if t == 's' and v is not None and v.text is not None:
                    idx = int(v.text)
                    val = shared[idx] if 0 <= idx < len(shared) else ''
                elif t == 'inlineStr':
                    val = ''.join(x.text or '' for x in c.iter(NS + 't'))
                else:
                    val = v.text if v is not None else ''
                cells[col] = val or ''
            rows.append(cells)
        if not rows:
            continue
        headers = rows[0]
        cols = sorted(headers.keys(), key=lambda c: (len(c), c))
        recs = []
        for r in rows[1:]:
            d = {}
            for c in cols:
                h = (headers.get(c) or '').strip()
                if h:
                    d[h] = (r.get(c) or '').strip()
            if any(d.values()):
                recs.append(d)
        sname = names[i] if i < len(names) else ('sheet%d' % (i + 1))
        out.append((sname, recs))
    return out

XLSX_COL_MAP = {'仓库': 'full_name', '⭐': 'stars', '描述': 'desc', '语言': 'lang',
                '更新': 'pushed_at', '部署实证': 'deploy_signals', '许可': 'license',
                'Fork': 'forks', '分类': 'cat_direct', '简介': 'summary', '摘要': 'summary'}

def norm_record(r):
    o = {}
    for k, v in r.items():
        o[XLSX_COL_MAP.get(k, k)] = v
    return o

# ───────────────────────── 用途分类（f_use；交付带「分类」列时该列另存 category） ─────────────────────────
CAT_RULES = [
    ('视频生成', ['video', 'subtitle', 'ffmpeg', 'movie', 'remotion', 'video-generation', '视频', '字幕', '剪辑', '动画']),
    ('图像处理', ['image', 'photo', 'vision', 'segment', 'upscale', 'diffusion', 'stable-diffusion', 'flux', 'comfy',
                  'plot', 'chart', 'drawing', 'paint', '图像', '图片', '修图', '绘图', '画图', '图表']),
    ('音频语音', ['audio', 'voice', 'speech', 'tts', 'asr', 'whisper', 'music', 'song', 'podcast', '音频', '语音', '播客', '音乐']),
    ('文档处理', ['pdf', 'document', 'docx', 'excel', 'spreadsheet', 'ocr', 'markdown', 'translate', '文档', '翻译', '表格', '纪要']),
    ('数据采集', ['scrap', 'crawl', 'spider', 'browser', 'selenium', 'playwright', '采集', '爬虫', '浏览器', '抓取']),
    ('科研学术', ['research', 'paper', 'arxiv', 'science', 'scholar', 'math', 'scientific', '学术', '论文', '科研', '科学']),
    ('编程开发', ['code', 'coding', 'copilot', 'ide', 'devops', 'debug', 'compiler', '代码', '编程', '开发', '审查']),
    ('内容创作', ['content', 'blog', 'writing', 'writer', 'seo', 'slide', 'ppt', '创作', '写作', '文案', '自媒体']),
    ('流程自动化', ['workflow', 'automation', 'automat', 'agent', 'orchestrat', 'pipeline', 'rag', 'llm', 'mcp', '工作流', '自动化', '智能体', '编排']),
]

def assign_category(hay):
    hay = hay.lower()
    best, best_score = '其他', 0
    for cat, kws in CAT_RULES:
        score = 0
        for kw in kws:
            if re.search(r'[a-z]', kw):
                if re.search(r'(?<![a-z0-9])' + re.escape(kw) + r'(?![a-z0-9])', hay):
                    score += 1
            elif kw in hay:
                score += 1
        if score > best_score:
            best, best_score = cat, score
    return best

# ───────────────────────── 形式分面打标（规则粗分 · 全离线 · 不改数据只加标签） ─────────────────────────
def tag_deploy(ev):
    """部署方式：兼容证据文件信号（package.json…）与人工方法名（Node/npm、pnpm…）。"""
    t = (ev or '').lower()
    if 'docker' in t or 'compose' in t:
        return 'Docker 容器'
    if 'install.sh' in t or 'setup.sh' in t:
        return '安装脚本'
    if any(k in t for k in ('pyproject.toml', 'requirements', 'package.json', 'go.mod', 'cargo.toml',
                            'gemfile', 'pom.xml', 'build.gradle', 'composer.json', 'uv.lock',
                            'poetry.lock', 'setup.py', 'cargo.lock',
                            'npm', 'pnpm', 'yarn', 'pip', 'pypi', 'cargo', 'gomod', 'go module',
                            'gem', 'composer', 'nuget', 'maven', 'gradle', 'node', '包管理', '依赖')):
        return '包管理器依赖'
    if 'install' in t or 'curl' in t:
        return '安装脚本'
    if any(k in t for k in ('makefile', 'cmake', 'configure', 'meson.build', 'make', 'build')):
        return '源码编译'
    return '未标注'

def tag_model(txt):
    """模型运行：本地模型 / 云 API / 两者 / 未提及（粗分）"""
    t = (txt or '').lower()
    t = t.replace('openai-compatible', ' ').replace('openai compatible', ' ')
    local = any(k in t for k in ('ollama', 'lm studio', 'lmstudio', 'llama.cpp', 'llamacpp', 'vllm',
                                 'local model', 'local llm', 'local-first', 'self-hosted model',
                                 '本地模型', '本地大模型', '本地推理', '本地部署模型', '离线运行',
                                 'comfyui', 'stable diffusion', 'text-generation-webui', 'sd webui'))
    cloud = any(k in t for k in ('openai', 'anthropic', 'claude', 'gpt-4', 'gpt-5', 'gemini', 'api key',
                                 'api-key', 'dashscope', 'azure openai', 'bedrock', 'moonshot',
                                 'siliconflow', 'openrouter', '百炼', '智谱', '硅基流动'))
    if local and cloud:
        return '本地+云均可'
    if local:
        return '可本地模型'
    if cloud:
        return '调云 API'
    return '未提及'

def tag_form(txt):
    """形态：清单/合集 · 模板/脚手架 · 教程/指南 · 平台/框架 · 库/SDK · 管线/工作流 · 工具/应用"""
    t = (txt or '').lower()
    def has(*ks): return any(k in t for k in ks)
    if has('awesome-', 'awesome ', 'curated list', 'collection of', '合集', '清单', '资源列表'):
        return '清单/合集'
    if has('template', 'boilerplate', 'scaffold', 'starter kit', 'starter template', '模板', '脚手架'):
        return '模板/脚手架'
    if has('tutorial', 'course', 'guide', '教程', '指南', '从入门'):
        return '教程/指南'
    if has('framework', 'platform', 'engine', 'orchestration', '编排', '框架', '平台', '引擎',
            'low-code', 'low code', 'no-code', 'no code', '低代码', 'builder', 'studio'):
        return '平台/框架'
    if has('library', 'sdk', 'toolkit', 'client library', '开发库', '工具包'):
        return '库/SDK'
    if has('pipeline', 'workflow', '工作流', '管线', 'swarm', 'multi-agent', 'multiagent', 'multi agent'):
        return '管线/工作流'
    if has('tool', 'cli', 'command line', 'command-line', 'app', 'application', 'assistant', 'server',
            'bot', 'plugin', 'extension', 'mcp', 'desktop', 'gui', 'webui', 'web ui', '工具', '插件',
            '助手', '客户端', '桌面'):
        return '工具/应用'
    return '未分'

def tag_ui(txt):
    """使用方式：图形界面 · 命令行 · 开发库 · 未分"""
    t = (txt or '').lower()
    def has(*ks): return any(k in t for k in ks)
    def hasw(*ws): return any(re.search(r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])', t) for w in ws)
    if has('webui', 'web ui', 'web interface', 'web-based', 'dashboard', 'studio', 'desktop app',
            'desktop application', 'graphical', 'visual', 'no-code', 'low-code', 'drag', 'canvas',
            '界面', '可视化', '桌面端', '图形界面'):
        return '图形界面'
    if hasw('cli', 'terminal', 'cmd') or has('command line', 'command-line', '命令行'):
        return '命令行'
    if hasw('library', 'sdk') or has('api client', 'python package', 'npm package', '开发库'):
        return '开发库'
    return '未分'

def tag_facets(name, desc, summary, deploy_signals):
    hay = ' '.join([name or '', desc or '', summary or ''])
    return tag_form(hay), tag_deploy(deploy_signals), tag_model(hay), tag_ui(hay)

# ───────────────────────── 工具函数 ─────────────────────────
def s(v, cap):
    if v is None:
        return ''
    if isinstance(v, (list, tuple)):
        v = ','.join(str(x) for x in v if x)
    return re.sub(r'\s+', ' ', str(v)).strip()[:cap]

def toint(v):
    try:
        return int(float(str(v).replace(',', '').strip() or 0))
    except Exception:
        return 0

def first_key(r, keys):
    for k in keys:
        v = r.get(k)
        if v not in (None, '', [], {}):
            return v
    return None

# ───────────────────────── 主流程 ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', required=True, help='全量 JSON 或 xlsx 路径')
    ap.add_argument('--old', default='/tmp/gh_pipe_judged.json')
    ap.add_argument('--db', default='/home/zhenjinchao/flowscore/flowscore.db')
    ap.add_argument('--static', default='/home/zhenjinchao/pipelines')
    a = ap.parse_args()

    src_is_xlsx = a.json.lower().endswith('.xlsx')
    if src_is_xlsx:
        sheets = read_xlsx(a.json)
        print('[ingest] xlsx 工作表:')
        for nm, recs in sheets:
            print(f'    「{nm}」 {len(recs)} 行')
        d = []
        for nm, recs in sheets:
            d += [norm_record(r) for r in recs]
    else:
        raw = json.load(open(a.json, encoding='utf-8'))
        if isinstance(raw, dict):
            for k in ('items', 'rows', 'data', 'repos'):
                if isinstance(raw.get(k), list):
                    raw = raw[k]
                    break
        assert isinstance(raw, list), 'JSON 顶层不是列表'
        d = [norm_record(r) if isinstance(r, dict) else {} for r in raw]

    # 去重（按仓库名，保首现）
    seen, uniq = set(), []
    for r in d:
        nm = str(r.get('full_name') or r.get('name') or '').strip()
        if not nm or nm in seen:
            continue
        seen.add(nm)
        uniq.append(r)
    if len(uniq) != len(d):
        print(f'[ingest] 去重: {len(d)} → {len(uniq)}')
    d = uniq
    print(f'[ingest] 载入 {len(d)} 条 · 样例字段: {sorted(d[0].keys())[:24]}')

    old_map = {}
    if a.old and os.path.exists(a.old):
        try:
            od = json.load(open(a.old, encoding='utf-8'))
            for x in od:
                v = x.get('verdict') or {}
                if v.get('v') == 'yes':
                    old_map[x.get('full_name')] = {
                        'summary': s(v.get('w'), 260),
                        'conf': v.get('c') if v.get('c') in ('high', 'medium', 'low') else None,
                        'tag': s(v.get('t'), 30)}
            print(f'[ingest] 旧 293 富化表: {len(old_map)} 条')
        except Exception as e:
            print('[ingest] 旧文件读取失败（跳过富化）:', e)
    else:
        print('[ingest] 无旧文件（跳过富化）')

    rows = []
    stat = dict(summary=0, deploy=0, tech=0, verified=0)
    fac_stat = {k: {} for k in ('f_use', 'f_form', 'f_deploy', 'f_model', 'f_ui')}
    for r in d:
        if not isinstance(r, dict):
            continue
        name = s(r.get('full_name') or r.get('name') or r.get('repo'), 120)
        if not name:
            continue
        if '/' not in name and 'github.com/' in name:
            name = name.split('github.com/')[-1].strip('/')
        topics = r.get('topics')
        if isinstance(topics, str):
            topics = [t for t in topics.split(',') if t]
        topics = ','.join(str(t).strip() for t in (topics or []) if str(t).strip())[:300]
        desc = s(r.get('desc') or r.get('description') or r.get('desc_en'), 400)
        summary = s(first_key(r, ['summary', 'readme_summary', 'summary_zh', 'abstract', 'desc_zh', '简介', '摘要']), 260)
        deploy = s(first_key(r, ['deploy_methods', 'deploy_signals', 'deploy', 'signals', '部署实证']), 120)
        tech = s(first_key(r, ['tech', 'tech_stack', 'stack', 'technologies']), 160)
        stars = toint(r.get('stars') or r.get('⭐'))
        forks = toint(r.get('forks') or r.get('Fork'))
        cat_direct = s(r.get('cat_direct') or r.get('cat') or r.get('category'), 40)

        if src_is_xlsx:
            verified = 1
        else:
            dep = r.get('deployable')
            if isinstance(dep, str):
                dep = dep.strip() in ('是', 'true', 'True', 'yes', '1')
            verified = 1 if (dep if dep is not None else bool(deploy)) else 0

        old = old_map.get(name)
        conf_v = r.get('confidence')
        if conf_v in ('high', 'medium', 'low'):
            conf = conf_v
        elif old:
            conf = old['conf'] or ('high' if verified else 'low')
        else:
            conf = 'high' if (verified and deploy) else ('medium' if verified else 'low')
        if old and not summary:
            summary = old['summary']
        hay = ' '.join([name, desc, topics, (old or {}).get('tag') or ''])

        if cat_direct:
            cat = cat_direct
        else:
            cat = assign_category(hay)

        f_use = assign_category(hay)
        f_form, f_deploy, f_model, f_ui = tag_facets(name, desc, summary, deploy + ' ' + s(r.get('signals'), 80))
        for k, v in (('f_use', f_use), ('f_form', f_form), ('f_deploy', f_deploy),
                     ('f_model', f_model), ('f_ui', f_ui)):
            fac_stat[k][v] = fac_stat[k].get(v, 0) + 1

        rows.append((name, s(r.get('url'), 200) or ('https://github.com/' + name),
                     stars, forks, s(r.get('lang'), 40),
                     summary, desc, cat, conf, s(r.get('pushed_at') or r.get('updated'), 30), s(r.get('license'), 40),
                     deploy, tech, topics, f_use, f_form, f_deploy, f_model, f_ui,
                     toint(r.get('hits')), verified))
        stat['summary'] += 1 if summary else 0
        stat['deploy'] += 1 if deploy else 0
        stat['tech'] += 1 if tech else 0
        stat['verified'] += verified

    rows.sort(key=lambda x: -x[2])
    dbn = a.db + '.new'
    if os.path.exists(dbn):
        os.remove(dbn)
    con = sqlite3.connect(dbn)
    con.execute('''CREATE TABLE items(id INTEGER PRIMARY KEY, full_name TEXT UNIQUE, url TEXT,
        stars INT, forks INT, lang TEXT, summary TEXT, desc_en TEXT, category TEXT, confidence TEXT,
        pushed_at TEXT, license TEXT, deploy TEXT, tech TEXT, topics TEXT,
        f_use TEXT, f_form TEXT, f_deploy TEXT, f_model TEXT, f_ui TEXT, hits INT, verified INT)''')
    con.executemany('INSERT INTO items(full_name,url,stars,forks,lang,summary,desc_en,category,confidence,'
                    'pushed_at,license,deploy,tech,topics,f_use,f_form,f_deploy,f_model,f_ui,hits,verified) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    for idx, col in (('idx_stars', 'stars'), ('idx_cat', 'category'), ('idx_ver', 'verified'),
                     ('idx_fuse', 'f_use'), ('idx_fform', 'f_form'), ('idx_fmodel', 'f_model'),
                     ('idx_fdpl', 'f_deploy')):
        con.execute(f'CREATE INDEX {idx} ON items({col})')
    con.commit()
    ok = con.execute('PRAGMA integrity_check').fetchone()[0]
    con.close()
    assert ok == 'ok', 'integrity_check 未通过: ' + str(ok)
    if os.path.exists(a.db):
        shutil.copy2(a.db, a.db + '.bak.' + STAMP)
        print(f'[ingest] 旧 db 备份 → {a.db}.bak.{STAMP}')
    os.replace(dbn, a.db)
    print(f'[ingest] 入库完成: {len(rows)} 行 → {a.db}')
    print(f'[ingest] 覆盖: summary {stat["summary"]} · deploy {stat["deploy"]} · tech {stat["tech"]} · verified {stat["verified"]}')
    for k in ('f_use', 'f_form', 'f_deploy', 'f_model', 'f_ui'):
        top = sorted(fac_stat[k].items(), key=lambda x: -x[1])
        print(f'[ingest] {k}: ' + ' · '.join(f'{n} {c}' for n, c in top[:12]))

    con = sqlite3.connect(f'file:{a.db}?mode=ro', uri=True)
    cur = con.cursor()
    total = cur.execute('SELECT COUNT(*) FROM items WHERE verified=1').fetchone()[0]
    total_all = cur.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    high = cur.execute("SELECT COUNT(*) FROM items WHERE verified=1 AND confidence='high'").fetchone()[0]
    o10 = cur.execute('SELECT COUNT(*) FROM items WHERE verified=1 AND stars>=10000').fetchone()[0]
    cats = cur.execute('SELECT category, COUNT(*) FROM items WHERE verified=1 GROUP BY category ORDER BY category COLLATE NOCASE ASC').fetchall()
    print(f'[ingest] stats: 可部署 {total} / 池内 {total_all} / 高置信 {high} / 10k+ {o10}')
    for c, n in cats[:20]:
        print(f'    {c}: {n}')

    # 静态再生成（v2 兼容 workflows.json + llms.txt）
    items = cur.execute('SELECT full_name,url,stars,lang,summary,desc_en,category,confidence,pushed_at,'
                        'f_use,f_form,f_deploy,f_model,f_ui FROM items WHERE verified=1 ORDER BY stars DESC LIMIT 3000').fetchall()
    wf = {'stats': {'total': total, 'total_all': total_all, 'high': high, 'over10k': o10,
                    'built': time.strftime('%Y-%m-%d')},
          'categories': [{'name': c, 'count': n} for c, n in cats],
          'items': [{'n': i[0], 'u': i[1], 's': i[2], 'l': i[3], 'z': i[4], 'd': i[5],
                     'c': i[6], 'k': i[7], 'p': i[8], 'fuse': i[9], 'ff': i[10], 'fd': i[11],
                     'fm': i[12], 'fu': i[13]}
                    for i in items]}
    os.makedirs(os.path.join(a.static, 'api'), exist_ok=True)
    wfpath = os.path.join(a.static, 'api', 'workflows.json')
    if os.path.exists(wfpath):
        shutil.copy2(wfpath, wfpath + '.bak.' + STAMP)
    tmp = wfpath + '.tmp'
    json.dump(wf, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, wfpath)
    print(f'[ingest] api/workflows.json 已更新（top {len(items)} 条, {os.path.getsize(wfpath)} B）')

    llms = f'''# 流谱 · FlowScore —— 开箱即用 AI 工作流精选
站点: https://pipeline.zufe.com.cn/
面向 Agent 的只读接口（无需鉴权，限速 90 次/分/IP，只读不写）:
1) GET /api/stats -> 站点统计（总数 / 高置信 / 10k+ / 分类计数）
2) GET /api/facets?q=&conf=&use=&cat=&form=&dpl=&model=&ui=
   -> 分面计数（同一维度多选=或，跨维度=与；计数为"留一法"：即假设选中该面值时其余条件不变的可选数量）
   维度取值:
     use=用途分类（文档处理/视频生成/图像处理/音频语音/数据采集/流程自动化/科研学术/内容创作/编程开发/其他）
     cat=A/B/C/D 交付类别 | form=形态 | dpl=部署方式 | model=模型运行 | ui=使用方式（均为关键词粗分标签）
3) GET /api/items?offset=0&limit=36&sort=stars&q=<关键词>&conf=<high|medium>&use=&cat=&form=&dpl=&model=&ui=
   - sort: stars | stars-a | push | name
   - 返回 {{total, offset, limit, items:[{{full_name,url,stars,lang,summary,desc_en,category,confidence,pushed_at,license,deploy,tech,topics[],f_use,f_form,f_deploy,f_model,f_ui,hits}}]}}
4) GET /api/search?q=<自然语言需求>&n=10 -> 本地 Qwen 语义挑选（engine 字段标注 qwen|lexical，失败自动回退关键词）
数据口径: GitHub 公开仓库扫描 + 部署实证核查（根目录实测 docker/compose/package.json 等入口）；
confidence 为站点内部标注，仅供参考；"有部署实证"仅表示存在部署入口，不保证运行时无坑；
分面（f_use 用途 / f_form 形态 / f_deploy 部署方式 / f_model 模型运行 / f_ui 使用方式）为离线关键词规则
粗分（打标函数见 ingest_flowscore_v2.py），适合筛选导航，不保证 100% 准确。
示例: curl "https://pipeline.zufe.com.cn/api/search?q=把会议录音变成纪要"
'''
    with open(os.path.join(a.static, 'llms.txt'), 'w', encoding='utf-8') as f:
        f.write(llms)
    print('[ingest] llms.txt 已更新')
    print('[ingest] DONE')

if __name__ == '__main__':
    main()
