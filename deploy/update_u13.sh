#!/usr/bin/env bash
# u13：v3.7 —— 搜索候选池「投稿行全员优先入池」（修 qwen 搜不到投稿项目的根因）
# 原则：先备份、有校验、失败中止、不删旧文件
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore

echo "── 1) API v3.7 换装 + 重启 ──"
cp flowscore_api.py flowscore_api.py.bak.$TS && echo "备份 flowscore_api.py.bak.$TS"
cp flowscore_api_v3_7.py flowscore_api.py
PID=$(ss -tlnp 2>/dev/null | grep 61587 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -n "$PID" ]; then kill "$PID" && echo "旧 API pid $PID 已停"; sleep 1; else echo "未找到旧 API（继续）"; fi
nohup python3 /home/zhenjinchao/flowscore/flowscore_api.py >> /home/zhenjinchao/flowscore/api.log 2>&1 </dev/null & disown
sleep 2
echo "本地 health: $(curl -s --max-time 5 http://127.0.0.1:61587/health)"
echo "本地社区列表头: $(curl -s --max-time 5 'http://127.0.0.1:61587/api/items?src=community&limit=1' | head -c 90)"
echo "本地精选回归头: $(curl -s --max-time 5 'http://127.0.0.1:61587/api/items?limit=1' | head -c 90)"

echo
echo "── 2) 公网语义搜索终测（走服务器 Qwen）──"
for q in 数模管线 数模; do
  echo "· 需求「$q」："
  curl -s -G --max-time 120 --data-urlencode "q=$q" --data-urlencode "n=8" "https://pipeline.zufe.com.cn/api/search" | python3 -c "import sys,json
d=json.load(sys.stdin)
names=[i['full_name'] for i in d.get('items',[])]
print('  engine:', d.get('engine'), '| 挑中数模管线:', 'xtr0928/Multi-agent-mathematical-modeling' in names)
for i in d.get('items',[])[:8]: print('   -', i['full_name'])"
done
echo "── 完成 ──"
