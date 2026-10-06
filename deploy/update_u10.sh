#!/usr/bin/env bash
# u10：首页滚动修复版上线（追加式加载 + 并发护栏 + 实时位置守卫）
# 原则：先备份、有校验、失败中止、不删旧文件
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/pipelines
cp index.html index.html.bak.$TS && echo "备份 index.html.bak.$TS"

cp /home/zhenjinchao/flowscore/v34_index.html index.html.new
if ! grep -q "if (reset) grid.innerHTML" index.html.new; then echo "!! 缺追加修复标记，中止"; rm index.html.new; exit 1; fi
if ! grep -q "window.innerHeight + 700" index.html.new; then echo "!! 缺实时位置守卫，中止"; rm index.html.new; exit 1; fi
if ! grep -q "st.loading" index.html.new; then echo "!! 缺并发护栏，中止"; rm index.html.new; exit 1; fi
mv index.html.new index.html
echo "── 验证 ──"
echo "文件 md5: $(md5sum index.html | cut -d' ' -f1)"
echo "文件大小: $(stat -c %s index.html)B"
echo "本地 HTTP: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:61000/)"
echo "公网 HTTP: $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pipeline.zufe.com.cn/)"
echo "公网·追加修复标记(应=1): $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'if (reset) grid.innerHTML')"
echo "公网·实时位置守卫(应=1): $(curl -s --max-time 15 https://pipeline.zufe.com.cn/ | grep -c 'window.innerHeight + 700')"
echo "── 完成 ──"
