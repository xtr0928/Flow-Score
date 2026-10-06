#!/usr/bin/env bash
# u14：v37 前端（范围+无限制 / 加载反馈 / 追加载失败保护）+ API v3.8 + 投稿行升入精选池 + 静态 no-cache
# 原则：先备份、有校验、失败中止、不删旧文件
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore

echo "── 1) DB：投稿行升入精选池（先备份） ──"
cp flowscore.db flowscore.db.bak.$TS && echo "备份 flowscore.db.bak.$TS"
python3 promote_projects_v1.py /home/zhenjinchao/flowscore/flowscore.db

echo
echo "── 2) API v3.8 换装 + 重启 ──"
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_8.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "本地 health: $(curl -s --max-time 5 http://127.0.0.1:61587/health)"
echo "本地 stats: $(curl -s --max-time 5 http://127.0.0.1:61587/api/stats | head -c 130)"
echo "本地 src=all: $(curl -s --max-time 5 'http://127.0.0.1:61587/api/items?src=all&limit=1' | head -c 110)"

echo
echo "── 3) 首页 v37 换装 ──"
cd /home/zhenjinchao/pipelines
cp index.html index.html.bak.$TS && echo "备份 index.html.bak.$TS"
cp /home/zhenjinchao/flowscore/v37_index.html index.html

echo
echo "── 4) Caddy 静态侧改 no-cache（备份 + 校验 + 热重载） ──"
cp Caddyfile Caddyfile.bak.$TS && echo "备份 Caddyfile.bak.$TS"
python3 - <<'PYEOF'
p = '/home/zhenjinchao/pipelines/Caddyfile'
s = open(p, encoding='utf-8').read()
old = 'header Cache-Control "public, max-age=300"'
new = 'header Cache-Control "no-cache"'
assert s.count(old) == 1, 'Caddyfile 锚点命中 %d 次（应为1）' % s.count(old)
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
print('Caddyfile: max-age=300 -> no-cache ✓')
PYEOF
/home/zhenjinchao/flarum/_dl/frankenphp adapt --config /home/zhenjinchao/pipelines/Caddyfile >/dev/null && echo "adapt 校验 OK"
kill -USR1 $(pgrep -x frankenphp) && echo "frankenphp 已热重载"
sleep 1

echo
echo "── 5) 公网验证 ──"
echo "首页: $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/)"
echo "公网缓存头: $(curl -s -I --max-time 15 https://pipeline.zufe.com.cn/ | grep -i cache-control | tr -d '\r')"
echo "本地缓存头: $(curl -s -I --max-time 10 http://127.0.0.1:61000/ | grep -i cache-control | tr -d '\r')"
H=$(curl -s --max-time 15 https://pipeline.zufe.com.cn/)
echo "v37 标记(应=1): $(echo "$H" | grep -c '前端 v37')"
echo "无限制选项(应=1): $(echo "$H" | grep -c 'value=\"all\"')"
echo "加载反馈(应=1): $(echo "$H" | grep -c '正在加载更多')"
echo "滚动标记(应 1/1): $(echo "$H" | grep -c 'if (reset) grid.innerHTML') / $(echo "$H" | grep -c 'window.innerHeight + 700')"
echo "公网 stats: $(curl -s --max-time 15 https://pipeline.zufe.com.cn/api/stats | head -c 130)"
echo "公网 src=all: $(curl -s --max-time 15 'https://pipeline.zufe.com.cn/api/items?src=all&limit=1' | head -c 110)"
echo
echo "── 语义搜索复查（q=数模管线，走服务器 Qwen）──"
curl -s -G --max-time 120 --data-urlencode "q=数模管线" --data-urlencode "n=4" "https://pipeline.zufe.com.cn/api/search" | python3 -c "import sys,json
d=json.load(sys.stdin)
names=[i['full_name'] for i in d.get('items',[])]
print('engine:', d.get('engine'), '| #1:', names[0] if names else '-')"
echo "── 完成 ──"
