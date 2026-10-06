#!/usr/bin/env bash
# 流谱 API v3.3 上线：语义搜索修复（关思考 + 拆词候选 + 90s 超时）
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_3.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "── 公网语义搜索实测（应 engine=qwen）──"
time curl -s -G --max-time 120 --data-urlencode "q=把会议录音变成纪要" --data-urlencode "n=5" "https://pipeline.zufe.com.cn/api/search" | python3 -c "import sys,json
d=json.load(sys.stdin)
print('engine:', d.get('engine'))
for i in d.get('items', [])[:5]:
    print('  -', i['full_name'], '|', (i.get('summary') or i.get('desc_en') or '')[:48])"
echo "── 完成 ──"
