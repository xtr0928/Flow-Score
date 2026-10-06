#!/bin/bash
# 流谱 · 星数快照定时任务包装
# token 在运行时从 amiya 档案 .env 提取（不落盘、不回显、不进 crontab 明文）
set -u
ENVF=/home/zhenjinchao/.hermes/profiles/amiya/.env
TOKEN=$(grep -m1 -E '^(export )?GITHUB_TOKEN=' "$ENVF" 2>/dev/null | sed -E 's/^export //' | cut -d= -f2- | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//')
[ -n "${TOKEN:-}" ] && export GITHUB_TOKEN="$TOKEN"
cd /home/zhenjinchao/pipelines/tools || exit 1
exec /usr/bin/python3 snapshot_stars.py
