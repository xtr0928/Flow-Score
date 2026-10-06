#!/usr/bin/env bash
# 简介页 v4（Anthropic 风高端化改版）上线
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/pipelines
cp intro.html intro.html.bak.$TS && echo "备份 intro.html.bak.$TS"
cp /home/zhenjinchao/flowscore/intro_v4.html intro.html.new
mv intro.html.new intro.html
echo "── 验证 ──"
echo "本地 HTTP: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:61000/intro.html)"
echo "公网 HTTP: $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/intro.html)"
echo "公网含新侧边项（应 ≥2）: $(curl -s --max-time 15 https://pipeline.zufe.com.cn/intro.html | grep -c 'agent 更快查找')"
echo "公网含陶土色变量（应 ≥1）: $(curl -s --max-time 15 https://pipeline.zufe.com.cn/intro.html | grep -c 'c96442')"
echo "── 完成 ──"
