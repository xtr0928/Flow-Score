# -*- coding: utf-8 -*-
"""API v4.0 本地验收：200 字上限 / 1 秒 1 次节流 / 单段提示词与无状态 / 回归。
前置：API v4.0 在 61589（FLOWSCORE_AI=0 + test_community_v38.db）。"""
import importlib.util
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(r"C:/Users/XXQ0928/AppData/Local/hermes/cache/scratch/cardsite")
LAPI = 'http://127.0.0.1:61589'


def get(path, headers=None):
    req = urllib.request.Request(LAPI + path, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


print('── ① 200 字上限 ──')
s1, d1 = get('/api/search?q=' + urllib.parse.quote('数' * 201))
print('201 字 → %s %s %r' % (s1, d1.get('error'), d1.get('message')))
s2, d2 = get('/api/search?q=' + urllib.parse.quote('数模' * 100))
print('200 字 → %s（%s 条 · engine=%s）' % (s2, len(d2.get('items', [])), d2.get('engine')))
time.sleep(1.15)   # 让 200 字那次搜索的节流过期

print()
print('── ② 1 秒 1 次节流（同 IP）──')
s3, d3 = get('/api/search?q=' + urllib.parse.quote('数模管线'))
s4, d4 = get('/api/search?q=' + urllib.parse.quote('数模管线'))
print('第 1 次 → %s engine=%s' % (s3, d3.get('engine')))
print('紧接第 2 次 → %s %s %r' % (s4, d4.get('error'), d4.get('message')))
time.sleep(1.15)
s5, d5 = get('/api/search?q=' + urllib.parse.quote('数模管线'))
print('等 1.15s 后 → %s engine=%s' % (s5, d5.get('engine')))
s6, d6 = get('/api/search?q=' + urllib.parse.quote('数模管线'), headers={'X-Forwarded-For': '203.0.113.9'})
print('异 IP 立即再搜 → %s %s（期望放行）' % (s6, d6.get('error')))

print()
print('── ③ 单段提示词 & 无状态（单元级）──')
spec = importlib.util.spec_from_file_location('api40', str(ROOT / 'flowscore_api_v4_0.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

cands = [(101, {'summary': '把会议录音变成中文纪要', 'desc_en': '', 'full_name': 'a/x', 'category': '音频'}),
         (102, {'summary': '数学建模全流程管线', 'desc_en': '', 'full_name': 'b/y', 'category': '科研'})]
p1 = m.build_prompt('数模', cands)
p2 = m.build_prompt('把会议录音变成纪要', cands)
ok_seg = ('只返回管线编号结果' in p1) and ('只返回管线编号结果' in p2)
ok_iso = ('用户需求：把会议录音变成纪要' in p2) and ('用户需求：数模' not in p2)
print('单段含「只返回管线编号结果」: %s · 无上下文泄漏: %s' % (ok_seg, ok_iso))

captured = {}


class FakeR:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.payload


def fake_urlopen(req, timeout=None):
    captured['body'] = json.loads(req.data.decode('utf-8'))
    return FakeR(json.dumps({'choices': [{'message': {'content': '[101, 102]'}}]}).encode('utf-8'))


_orig_urlopen = urllib.request.urlopen
urllib.request.urlopen = fake_urlopen
try:
    picked = m.qwen_pick('数模', cands)
finally:
    urllib.request.urlopen = _orig_urlopen
msgs = captured['body']['messages']
print('messages 条数: %d（role=%s）· picked=%s' % (len(msgs), msgs[0]['role'], picked))
ok_one = (len(msgs) == 1 and msgs[0]['role'] == 'user'
          and all(x['role'] != 'system' for x in msgs)
          and '只返回管线编号结果' in msgs[0]['content']
          and picked == [101, 102])

print()
print('── ④ 回归：普通搜索照常 ──')
time.sleep(1.15)
s7, d7 = get('/api/search?q=' + urllib.parse.quote('数模'))
names = [i['full_name'] for i in d7.get('items', [])]
print('数模 → %s · %s 条 · 前 3: %s' % (s7, len(names), names[:3]))

ok = (s1 == 400 and d1.get('error') == 'too_long' and '200' in d1.get('message', '')
      and s2 == 200 and s3 == 200 and s4 == 429 and d4.get('error') == 'too_frequent'
      and s5 == 200 and s6 == 200 and d6.get('error') is None
      and ok_seg and ok_iso and ok_one and s7 == 200 and len(names) > 0)
print()
print('判定:', 'PASS ✓' if ok else 'FAIL ✗')
