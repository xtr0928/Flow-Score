#!/usr/bin/env bash
# 流谱 v3.4 上线：API v3.2（可部署精选语义 + total_all）+ 前端 v34（侧边栏升级）+ agent 页
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_2.py flowscore_api.py
echo "── 重启 API（按端口反查 pid，防自杀）──"
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "── 换前端 v34 + agent 页 ──"
cp /home/zhenjinchao/flowscore/v34_index.html /home/zhenjinchao/pipelines/index.html.new
cp /home/zhenjinchao/flowscore/agent.html /home/zhenjinchao/pipelines/agent.html.new
cd /home/zhenjinchao/pipelines
cp index.html index.html.bak.$TS && echo "备份 index.html.bak.$TS"
mv index.html.new index.html
mv agent.html.new agent.html
echo "── 本地验证 ──"
curl -s --max-time 5 "http://127.0.0.1:61587/api/stats" | python3 -c "import sys,json;d=json.load(sys.stdin);print('stats:',{k:d[k] for k in ('total','total_all','high','over10k')})"
echo "首页 v34 标记（应 2）: $(curl -s --max-time 5 http://127.0.0.1:61000/ | grep -c 'fs_fopen2')"
echo "首页 agent 链接（应 ≥1）: $(curl -s --max-time 5 http://127.0.0.1:61000/ | grep -c 'agent.html')"
echo "agent 页 HTTP: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:61000/agent.html)"
echo "── 公网验证 ──"
curl -s --max-time 15 "https://pipeline.zufe.com.cn/api/stats" | python3 -c "import sys,json;d=json.load(sys.stdin);print('公网 stats:',{k:d[k] for k in ('total','total_all','high','over10k')})"
echo "公网 agent 页 HTTP: $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/agent.html)"
echo "── 公网语义搜索实测（本地 Qwen）──"
curl -s -G --max-time 90 --data-urlencode "q=把会议录音变成纪要" --data-urlencode "n=5" "https://pipeline.zufe.com.cn/api/search" | python3 -c "import sys,json;d=json.load(sys.stdin);print('engine:',d.get('engine'));[print('  -',i['full_name']) for i in d.get('items',[])[:5]]"
echo "── 完成 ──"
