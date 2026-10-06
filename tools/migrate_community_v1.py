#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""社区投稿 v1 迁移：items 表增加 submission 列 + 种入首批（站长 10 个仓库）。

用法: python3 migrate_community_v1.py <db路径> <seed.json>
幂等：只删除/重建 submission='xtr0928' 的行，其余数据零触碰（不删任何旧内容）。
说明：种子 verified=0 且带 submission 标记 → 主列表/搜索/分面（全部过滤 verified=1）完全不受影响；
      社区页走 /api/community（只取 submission 非空行）。
注意：若未来重跑全量 ingest 重建了 items 表，需要重新执行本脚本（见部署手册）。
"""
import json
import sqlite3
import sys

KEYS = ('full_name', 'url', 'stars', 'forks', 'lang', 'summary', 'desc_en', 'category',
        'confidence', 'pushed_at', 'license', 'deploy', 'tech', 'topics',
        'f_use', 'f_form', 'f_deploy', 'f_model', 'f_ui', 'hits', 'verified', 'submission')


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    dbp, seedp = sys.argv[1], sys.argv[2]
    seed = json.load(open(seedp, encoding='utf-8'))
    con = sqlite3.connect(dbp)
    cur = con.cursor()

    cols = [c[1] for c in cur.execute('PRAGMA table_info(items)')]
    if 'submission' not in cols:
        cur.execute('ALTER TABLE items ADD COLUMN submission TEXT DEFAULT NULL')
        print('已加列: submission')
    else:
        print('列 submission 已存在（跳过 ALTER）')

    before = cur.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    cur.execute("DELETE FROM items WHERE submission = 'xtr0928'")
    removed = cur.rowcount
    sql = 'INSERT INTO items (%s) VALUES (%s)' % (','.join(KEYS), ','.join('?' * len(KEYS)))
    for x in seed:
        cur.execute(sql, [x.get(k) for k in KEYS])
    con.commit()

    after = cur.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    n_sub = cur.execute("SELECT COUNT(*) FROM items WHERE submission IS NOT NULL AND submission != ''").fetchone()[0]
    n_main = cur.execute("SELECT COUNT(*) FROM items WHERE COALESCE(submission,'') = ''").fetchone()[0]
    n_ver = cur.execute('SELECT COUNT(*) FROM items WHERE verified = 1').fetchone()[0]
    print('删除旧种子 %d 行 · 新增 %d 行 · 总行数 %d→%d' % (removed, len(seed), before, after))
    print('submission 标记行: %d（应为 %d） · 主池行: %d（应 %d） · verified=1: %d（不变）'
          % (n_sub, len(seed), n_main, before - removed, n_ver))
    for r in cur.execute("SELECT full_name, stars, verified, submission FROM items WHERE submission != '' ORDER BY id DESC LIMIT 3"):
        print('  ·', r[0], '| ★', r[1], '| verified', r[2], '| by', r[3])
    con.close()


if __name__ == '__main__':
    main()
