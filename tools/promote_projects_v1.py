# -*- coding: utf-8 -*-
"""把投稿行升入精选池（submission 标记行 → verified=1）。幂等，可重复跑。
用法：python promote_projects_v1.py [db路径]   （默认服务器库；本地测试传 test_*.db）"""
import sqlite3
import sys

DB = sys.argv[1] if len(sys.argv) > 1 else '/home/zhenjinchao/flowscore/flowscore.db'
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM items WHERE submission IS NOT NULL AND submission != ''")
subs = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM items WHERE verified=1")
before = cur.fetchone()[0]
cur.execute("UPDATE items SET verified=1 WHERE submission IS NOT NULL AND submission != ''")
con.commit()
cur.execute("SELECT COUNT(*) FROM items WHERE verified=1")
after = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM items WHERE submission IS NOT NULL AND submission != '' AND verified=1")
post = cur.fetchone()[0]
print('精选池: %d -> %d（+%d）· 投稿行 %d 条全在池内: %s  [%s]'
      % (before, after, after - before, subs, post == subs, DB))
con.close()
