#!/usr/bin/env bash
# u15：API v3.9 —— 领域简称扩展（数模 → 数学建模）；纯 API 换装
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore

echo "── API v3.9 换装 + 重启 ──"
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_9.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "本地 health: $(curl -s --max-time 5 http://127.0.0.1:61587/health)"
echo "本地 stats 头: $(curl -s --max-time 5 http://127.0.0.1:61587/api/stats | head -c 80)"
echo
echo "── 公网语义搜索三项实测 ──"
for q in 数模 数模管线 把会议录音变成纪要; do
  echo "· 需求「$q」："
  curl -s -G --max-time 120 --data-urlencode "q=$q" --data-urlencode "n=10" "https://pipeline.zufe.com.cn/api/search" | python3 -c "import sys,json
d=json.load(sys.stdin)
items=d.get('items',[])
names=[i['full_name'] for i in items]
xtr=sum(1 for n in names if n.startswith('xtr0928/'))
print('  engine:', d.get('engine'), '· 共', len(items), '条 · xtr0928', xtr, '条')
for n in names: print('   -', n)"
done
echo "── 完成 ──"
