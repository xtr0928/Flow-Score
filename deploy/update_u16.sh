#!/usr/bin/env bash
# u16：API v4.0（Agent 使用规范：200 字上限 / 1 秒 1 次 / 无状态单段提示词）
#      + 前端 v38（移动端顶部可折叠 + 语义搜索错误提示）+ agent 页更新
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore
SITE=/home/zhenjinchao/pipelines

echo "── ① API v4.0 换装 + 重启 ──"
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v4_0.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "本地 health: $(curl -s --max-time 5 http://127.0.0.1:61587/health)"

echo
echo "── ② 前端 v38 + agent 页换装 ──"
cp "$SITE/index.html" "$SITE/index.html.bak.$TS" && echo "备份 index.html.bak.$TS"
cp "$SITE/agent.html" "$SITE/agent.html.bak.$TS" && echo "备份 agent.html.bak.$TS"
cp v38_index.html "$SITE/index.html"
cp agent_v3.html "$SITE/agent.html"
echo "首页「前端 v38」标记: $(grep -c '前端 v38' "$SITE/index.html") 处 · top-toggle: $(grep -c 'top-toggle' "$SITE/index.html") 处"
echo "agent 页 200 字预检: $(grep -c '最多 200 字' "$SITE/agent.html") 处 · 使用规范: $(grep -c '使用规范' "$SITE/agent.html") 处"

echo
echo "── ③ 公网接口行为实测 ──"
LONG=$(python3 -c "print('数'*201)")
echo "· 201 字 → $(curl -s -G --max-time 20 --data-urlencode "q=$LONG" "https://pipeline.zufe.com.cn/api/search" | head -c 130)"
echo "· 数模（正常语义）→ $(curl -s -G --max-time 120 --data-urlencode 'q=数模' --data-urlencode 'n=6' 'https://pipeline.zufe.com.cn/api/search' | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('engine'), [i['full_name'] for i in d.get('items',[])][:6])")"
curl -s -G --max-time 120 --data-urlencode 'q=数模管线' --data-urlencode 'n=6' 'https://pipeline.zufe.com.cn/api/search' > /tmp/first_search.json & FIRST=$!
sleep 0.3
echo "· 首搜进行中紧接第 2 次 → $(curl -s -G --max-time 20 --data-urlencode 'q=数模管线' 'https://pipeline.zufe.com.cn/api/search' | head -c 130)"
wait $FIRST
echo "· 首搜最终结果 → $(python3 -c "import json;d=json.load(open('/tmp/first_search.json'));print(d.get('engine'), [i['full_name'] for i in d.get('items',[])][:6])")"
echo "── 完成 ──"
