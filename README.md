# 流谱 · FlowScore — 站点代码存档

**线上**：https://pipeline.zufe.com.cn/
（FrankenPHP/Caddy 反代 + 服务器本地 Qwen 语义搜索；数据全走 `/api/*`）

## 这是什么

「流谱 · FlowScore」是一个 AI 工作流精选导航站：

- **数据**：全量池 18,267 个 GitHub 工作流仓库 → 部署实证核查 → 精选 12,894 条「可部署」
- **分面筛选**：用途分类 / 类别 / 形态 / 部署方式 / 模型运行 / 使用方式 / 置信度（共 7 组，可折叠多选）
- **范围切换**：精选池（默认）/ 无限制（精选池 ∪ 用户投稿）/ 仅用户投稿
- **语义搜索**：服务器本地 Qwen3.8-27B（关闭思考链）从候选清单中挑选编号，失败自动回退关键词；投稿项目全员优先入候选池；领域简称扩展表 `KW_EXPAND`（如「数模」→「数学建模」）。**v4.0 起 Agent 使用规范**：查询 >200 字直接拒答（400）、每 IP 每秒限 1 次（429）、每次搜索均为无状态单轮、单段提示词（只返回管线编号结果）
- **社区投稿**：`xtr0928/flowscore` 仓库 Issue 表单投稿 → 数据侧标记（submission 字段）入池
- **配套页面**：简介页 / 热度榜 / agent 更快查找（纯地址列表，可整段复制给 agent）/ 可视化管线编排器（`/orchestrator/`）
- **滚动**：追加式无限加载（加载中显示「⏳ 正在加载更多…」，失败不毁列表、底部可点重试）

## 目录

```
web/      前端页面源稿（index.html = 首页 v38；intro / agent / hot / community）
api/      flowscore_api.py = 当前查询服务（v4.0，只读 SQLite，127.0.0.1:61587）
          history/ = 版本链 v3.4 → v3.9
tools/    ingest_flowscore_v2_3.py    数据入库（全量 JSON → items 表）
          migrate_community_v1.py     社区投稿迁移（加 submission 列 + 首批种子）
          promote_projects_v1.py      投稿行升入精选池（verified=1，幂等）
          snapshot_stars.py           星数快照
          community_seed.json         首批投稿种子（站长 10 仓库）
          transforms/                 各版本转换脚本（可重放的补丁集）
deploy/   update_u5.sh ~ update_u16.sh    逐次上线脚本（先备份 / 有校验 / 失败中止）
          Caddyfile.reference            服务器 Caddy 配置（参考）
          deploy_final_data.sh           全量数据部署
tests/    playwright 验收脚本：
          scroll_check.py        公网滚动全链（追加 / 首卡稳定 / 溢出 / 控制台）
          verify_v38_live.py     无限制范围 / 加载反馈 / 投稿切换 / 头部统计
          verify_v37_extra.py    语义搜索泛化回归（防投稿霸榜）
          test_kw39.py           简称扩展候选池验证（数模 → 数学建模）
          test_v38.py            本地全链（接口 + 页面，配本地 API 61589）
          test_v40.py            API v4.0 使用规范（200 字上限 / 1 秒 1 次 / 单段提示词无上下文）
          test_mobile_v38.py     移动端顶部折叠（默认收起 / localStorage 记忆 / 桌面不受影响）
          verify_v40_live.py     公网实测（并发捕捉 429 / 手机视口折叠 / 页脚 v38）
```

## 架构

- 服务器（frp-fog.com:33023，用户 zhenjinchao，免密 ssh）：
  - webroot `/home/zhenjinchao/pipelines/` —— FrankenPHP/Caddy `:61000` → cloudflared 隧道 → 公网域名；静态侧 `Cache-Control: no-cache`（改版即见新版）
  - API `~/flowscore/flowscore_api.py` —— `127.0.0.1:61587`，只读 `~/flowscore/flowscore.db`；每请求开只读连接，重启即生效
  - 本地 Qwen `http://127.0.0.1:8000` —— vLLM `Qwen3.8-27B-FP8`（OpenAI 兼容；必须 `enable_thinking=false`）
- 数据表 `items`：18,267 行；`verified=1` → 精选 12,894；`submission` 非空 = 投稿行（10 条，已升入精选池）
- 安全设计：API 只读 SELECT、只监听 127.0.0.1、限流 90 次/分/IP；Qwen 只做「从给定候选编号中挑选」，清单文本永不执行

## 版本

- 前端：v34 基础 → v35 滚动追加修复 → v36 范围下拉 + 置信度移入分面 → v37 无限制范围 + 加载反馈 + 失败保护 + 页脚版本标记 → **v38 移动端顶部可折叠（收起 63px 细条）**
- API：v3.4 语义调优 → v3.5 投稿通道 → v3.6 搜索纳入投稿 + `/api/items?src=community` → v3.7 投稿行全员进候选池 → v3.8 `src=all`（无限制） → v3.9 简称扩展（数模 → 数学建模） → **v4.0 Agent 使用规范（200 字 / 1 秒 1 次 / 无状态单段提示词）**
- 数据：2026-10-07 投稿 10 仓库升入精选池（12,884 → 12,894）

## 上线流程

本地改源稿 → 本机 playwright 验收 → scp 上传（服务器旧文件自动备份 `.bak.<ts>`）→
服务器 cp 换装 → API 按端口杀进程重启 / Caddy `adapt` 校验 + `kill -USR1` 热重载 → 本地 + 公网复测。
每次上线脚本见 `deploy/`（先备份、有校验、失败中止、不删旧文件）。

## 回滚

部署前所有目标文件都会备份：`index.html.bak.*`、`flowscore_api.py.bak.*`、`flowscore.db.bak.*`、`Caddyfile.bak.*`。
回滚 = 把对应 `.bak.<时间戳>` 覆盖回去并重启/热重载。

## 相关仓库

- 投稿入口：https://github.com/xtr0928/flowscore（Issue 表单 `submit.yml`）
- agent 聊天室：https://github.com/xtr0928/The-Watercooler-for-Bots
- 数模管线：https://github.com/xtr0928/Multi-agent-mathematical-modeling
