#!/usr/bin/env bash
# 流谱全量终版数据入库（18,267 池 / 12,884 可部署；json 已经 sha256 校验）
set -u
TS=$(date +%Y%m%d_%H%M%S)
cd /home/zhenjinchao/flowscore
cp ingest_flowscore_v2.py ingest_flowscore_v2.py.bak.$TS && echo "备份 ingest_flowscore_v2.py.bak.$TS"
cp ingest_flowscore_v2_3.py ingest_flowscore_v2.py
echo "── 全量数据入库 ──"
python3 ingest_flowscore_v2.py --json /home/zhenjinchao/可本地部署Agent工作流_全量_2026-10-07.json --db /home/zhenjinchao/flowscore/flowscore.db --static /home/zhenjinchao/pipelines 2>&1 | tail -40
echo "── 服务验证（API 每请求重开只读库，无需重启）──"
curl -s --max-time 5 "http://127.0.0.1:61587/api/stats" | python3 -c "import sys,json;d=json.load(sys.stdin);print('stats:',{k:d[k] for k in ('total','high','over10k','updated')})"
curl -s --max-time 5 "http://127.0.0.1:61587/api/facets" | python3 -c "import sys,json;d=json.load(sys.stdin);print('use:',[(x['v'],x['c']) for x in d.get('use',[])][:12]);print('matched:',d.get('matched'))"
echo "── 公网验证 ──"
curl -s --max-time 15 "https://pipeline.zufe.com.cn/api/stats" | python3 -c "import sys,json;d=json.load(sys.stdin);print('公网 stats:',{k:d[k] for k in ('total','high','over10k')})"
echo "── 完成 ──"
