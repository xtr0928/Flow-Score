#!/usr/bin/env bash
# u12：v3.6 —— 语义搜索纳入投稿候选 + 首页「仅用户投稿」范围切换 + 置信度分面组
# 原则：先备份、有校验、失败中止、不删旧文件
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore

echo "── 1) API v3.6 换装 + 重启 ──"
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_6.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "本地 health: $(curl -s --max-time 5 http://127.0.0.1:61587/health)"
echo "本地 src=community: $(curl -s --max-time 5 'http://127.0.0.1:61587/api/items?src=community&limit=2' | head -c 130)"

echo
echo "── 2) 首页 v36 换装 ──"
cd /home/zhenjinchao/pipelines
cp index.html index.html.bak.$TS && echo "备份 index.html.bak.$TS"
cp /home/zhenjinchao/flowscore/v36_index.html index.html

echo
echo "── 3) 验证 ──"
echo "公网首页: $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/)"
echo "src 选择器(应=1): $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'id="src"')"
echo "滚动标记(应 1/1): $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'if (reset) grid.innerHTML') / $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'window.innerHeight + 700')"
echo "社区投稿项(应=1): $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c '社区投稿')"
echo "公网 src=community: $(curl -s --max-time 15 'https://pipeline.zufe.com.cn/api/items?src=community&limit=1' | head -c 200)"
echo "公网 facets conf: $(curl -s --max-time 15 https://pipeline.zufe.com.cn/api/facets | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("conf"))' 2>/dev/null | head -c 160)"
echo
echo "── 语义搜索实测（q=数模管线，走服务器 Qwen）──"
time curl -s -G --max-time 120 --data-urlencode "q=数模管线" --data-urlencode "n=8" "https://pipeline.zufe.com.cn/api/search" | python3 -c "import sys,json
d=json.load(sys.stdin)
names=[i['full_name'] for i in d.get('items',[])]
print('engine:', d.get('engine'))
print('包含数模管线:', 'xtr0928/Multi-agent-mathematical-modeling' in names)
for i in d.get('items',[])[:8]: print('  -', i['full_name'])"
echo "── 完成 ──"
