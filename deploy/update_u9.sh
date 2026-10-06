#!/usr/bin/env bash
# 侧边栏全站统一：热度榜 hot.html + agent.html 换装 v34 同款侧边栏
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/pipelines
cp hot.html hot.html.bak.$TS && echo "备份 hot.html.bak.$TS"
cp agent.html agent.html.bak.$TS && echo "备份 agent.html.bak.$TS"
cp /home/zhenjinchao/flowscore/hot_v4.html hot.html.new
cp /home/zhenjinchao/flowscore/agent_v2.html agent.html.new
mv hot.html.new hot.html
mv agent.html.new agent.html
echo "── 验证 ──"
for pgx in hot agent; do
  echo "$pgx → 本地 $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:61000/$pgx.html) · 公网 $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/$pgx.html) · 作者与赞助标记 $(curl -s --max-time 15 https://pipeline.zufe.com.cn/$pgx.html | grep -c '作者与赞助')"
done
echo "热度榜旧虚线按钮残留（应 0）: $(curl -s --max-time 15 https://pipeline.zufe.com.cn/hot.html | grep -c 'tok-btn')"
echo "── 完成 ──"
