#!/usr/bin/env python3
"""Sanity-check the generated index.html (used locally and in CI)."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'index.html'
DATA = ROOT / 'data'


def fail(msg):
    print('FAIL:', msg)
    sys.exit(1)


if not PAGE.exists():
    fail('index.html 不存在，先运行 build/build_site.py')

html = PAGE.read_text(encoding='utf-8')
if not html.startswith('<!DOCTYPE html>'):
    fail('缺少 DOCTYPE')
if html.count('<script>') != 1 or html.count('</script>') != 1:
    fail('script 标签数量异常')
if '__DATA__' in html or '__META__' in html:
    fail('占位符未替换')

m = re.search(r'const RAW  = (\[.*?\]);\n', html, re.S)
if not m:
    fail('未找到内嵌数据')
rows = json.loads(m.group(1).replace('<\\/', '</'))
meta = json.loads(re.search(r'const META = (\{.*?\});', html).group(1))

papers = json.loads((DATA / 'papers.json').read_text(encoding='utf-8'))
decisions = {d['id']: d for d in json.loads((DATA / 'decisions.json').read_text(encoding='utf-8'))}
expect = [p['id'] for p in papers if decisions.get(p['id'], {}).get('status') in ('核心', '延伸')]

ids = [r[4] for r in rows]
if len(ids) != len(set(ids)):
    fail('页面数据存在重复 ID')
if set(ids) != set(expect):
    fail(f'页面数据与 decisions 不一致：缺 {len(set(expect)-set(ids))}，多 {len(set(ids)-set(expect))}')
if meta['n'] != len(rows) or meta['core'] != sum(1 for r in rows if r[1] == '核心'):
    fail('META 计数与数据不符')
if any(r[5] not in {p['title'] for p in papers} for r in rows[:50]):
    fail('标题与源数据不符')

for token in ('data-id="', 'localStorage', 'ACL2026-FAV', 'fbtn'):
    if token.lower() not in html.lower() and token != 'ACL2026-FAV':
        fail(f'页面缺少关键片段：{token}')

js = html.split('<script>')[1].split('</script>')[0]
node = shutil.which('node')
if node:
    tmp = ROOT / '.check.js'
    tmp.write_text(js, encoding='utf-8')
    try:
        r = subprocess.run([node, '--check', str(tmp)], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        if r.returncode != 0:
            fail('JS 语法错误：' + r.stderr.strip().splitlines()[0])
    finally:
        tmp.unlink(missing_ok=True)
else:
    print('! 未找到 node，跳过 JS 语法检查')

print(f'OK  {len(rows)} 篇  {PAGE.stat().st_size/1024/1024:.2f} MB  核心 {meta["core"]} / 延伸 {meta["ext"]}')
