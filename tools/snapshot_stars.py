#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流谱 · 星数快照 v1
每天记录站内工作流的 GitHub 星数，供热度榜计算日增/周增。
- 输入：同目录 gh_pipe_judged.json（verdict.v == 'yes' 的仓库）
- 输出：star_snapshots/YYYY-MM-DD.json {date, ts, stars:{repo: n}, fails:[...]}
- token：环境变量 GITHUB_TOKEN（由 wrapper 从档案 .env 运行时注入；Masks secrets：本脚本从不打印 token）
- 幂等：当天已记录的仓库自动跳过；原子写入（tmp + rename）
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'gh_pipe_judged.json')
SNAPDIR = os.path.join(HERE, 'star_snapshots')
TOKEN = (os.environ.get('GITHUB_TOKEN') or '').strip()
CST = timezone(timedelta(hours=8))

def fetch_stars(name, token):
    headers = {'User-Agent': 'flowscore-snapshot/1.0', 'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request('https://api.github.com/repos/' + name, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        j = json.load(r)
    return int(j.get('stargazers_count') or 0)

def main():
    d = json.load(open(SRC, encoding='utf-8'))
    repos = sorted({x['full_name'] for x in d if x.get('verdict', {}).get('v') == 'yes'})
    today = datetime.now(CST).strftime('%Y-%m-%d')
    os.makedirs(SNAPDIR, exist_ok=True)
    out = os.path.join(SNAPDIR, today + '.json')
    stars, fails = {}, []
    if os.path.exists(out):
        try:
            old = json.load(open(out, encoding='utf-8'))
            stars = dict(old.get('stars', {}))
        except Exception:
            pass
    todo = [r for r in repos if r not in stars]
    if not TOKEN:
        todo = todo[:55]  # 未认证限流兜底：每小时最多 ~55 个，可多跑几轮补齐
    print(f'[{today}] 目标 {len(repos)} 个仓库，已有 {len(stars)}，本轮拉取 {len(todo)}，token={"有" if TOKEN else "无"}')
    for i, name in enumerate(todo, 1):
        for attempt in (1, 2):
            try:
                stars[name] = fetch_stars(name, TOKEN)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    fails.append(name)
                    break
                if attempt == 2:
                    fails.append(name)
                else:
                    time.sleep(2)
            except Exception:
                if attempt == 2:
                    fails.append(name)
                else:
                    time.sleep(2)
        if i % 50 == 0:
            print(f'  进度 {i}/{len(todo)}', flush=True)
        time.sleep(0.12 if TOKEN else 1.1)
    tmp = out + '.tmp'
    json.dump({'date': today, 'ts': int(time.time()), 'stars': stars, 'fails': fails},
              open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(tmp, out)
    print(f'完成：{out} 共 {len(stars)} 个仓库，失败 {len(fails)}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
