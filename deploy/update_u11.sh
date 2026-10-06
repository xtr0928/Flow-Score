#!/usr/bin/env bash
# u11：社区投稿栏目上线 —— API v3.5 + DB 种入 10 个仓库 + community.html + 四页侧边栏加「社区投稿」+ Caddy 路由
# 原则：先备份、有校验、失败中止、不删旧文件
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore

echo "── 1) 数据库备份 + 迁移 ──"
cp flowscore.db flowscore.db.bak.$TS && echo "备份 flowscore.db.bak.$TS"
python3 migrate_community_v1.py flowscore.db community_seed.json || { echo "!! 迁移失败，中止（旧库有备份）"; exit 1; }

echo
echo "── 2) API v3.5 换装 + 重启 ──"
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_5.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "本地 health: $(curl -s --max-time 5 http://127.0.0.1:61587/health)"
echo "本地 community: $(curl -s --max-time 5 'http://127.0.0.1:61587/api/community?limit=1' | head -c 160)"

echo
echo "── 3) 页面换装（先备份） ──"
cd /home/zhenjinchao/pipelines
for f in index intro hot agent; do cp $f.html $f.html.bak.$TS && echo "备份 $f.html.bak.$TS"; done
cp /home/zhenjinchao/flowscore/v35_index.html index.html
cp /home/zhenjinchao/flowscore/intro_v5.html intro.html
cp /home/zhenjinchao/flowscore/hot_v5.html hot.html
cp /home/zhenjinchao/flowscore/agent_v3.html agent.html
cp /home/zhenjinchao/flowscore/community.html community.html
echo "已换装：index / intro / hot / agent / community"

echo
echo "── 4) Caddyfile 加 /api/community 路由 ──"
if grep -q '/api/community' Caddyfile; then
  echo "路由已存在（跳过）"
else
  cp Caddyfile Caddyfile.bak.$TS && echo "备份 Caddyfile.bak.$TS"
  python3 - <<'PYEOF'
src = open('/home/zhenjinchao/pipelines/Caddyfile', encoding='utf-8').read()
old = '''    handle /api/facets* {
        header Cache-Control "no-store"
        reverse_proxy 127.0.0.1:61587
    }'''
new = old + '''
    handle /api/community* {
        header Cache-Control "no-store"
        reverse_proxy 127.0.0.1:61587
    }'''
assert src.count(old) == 1, 'facets 块未找到或多次出现'
open('/home/zhenjinchao/pipelines/Caddyfile', 'w', encoding='utf-8').write(src.replace(old, new))
print('Caddyfile 已插入 /api/community 路由')
PYEOF
  FP=/home/zhenjinchao/flarum/_dl/frankenphp; [ -x "$FP" ] || FP=frankenphp
  if "$FP" adapt --config /home/zhenjinchao/pipelines/Caddyfile >/dev/null 2>&1; then
    kill -USR1 $(pgrep -x frankenphp) && echo "已热重载 frankenphp"
    sleep 1
  else
    echo "!! Caddyfile 语法校验失败，回滚配置"
    cp Caddyfile.bak.$TS Caddyfile
  fi
fi

echo
echo "── 5) 验证 ──"
echo "本地 community.html: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:61000/community.html)"
echo "公网 community.html: $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/community.html)"
echo "公网 /api/community: $(curl -s --max-time 15 'https://pipeline.zufe.com.cn/api/community?limit=2' | head -c 220)"
echo "公网 stats: $(curl -s --max-time 15 https://pipeline.zufe.com.cn/api/stats | python3 -c 'import json,sys; d=json.load(sys.stdin); print("total", d["total"], "| total_all", d["total_all"], "| community", d.get("community"))')"
for pgx in index intro hot agent; do
  echo "$pgx → 公网 $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/$pgx.html) · 社区投稿项 $(curl -s --max-time 15 https://pipeline.zufe.com.cn/$pgx.html | grep -c '社区投稿')"
done
echo "首页滚动标记(应 1 / 1): $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'if (reset) grid.innerHTML') / $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'window.innerHeight + 700')"
echo "community.html → 我要投稿按钮 $(curl -s --max-time 15 https://pipeline.zufe.com.cn/community.html | grep -c '我要投稿') · 侧边栏高亮 $(curl -s --max-time 15 https://pipeline.zufe.com.cn/community.html | grep -c 'side-link on')"
echo "── 完成 ──"
