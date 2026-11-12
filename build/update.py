#!/usr/bin/env python3
"""One-click yearly update.

  1. 解析新的 ACL XML → data/papers.json（保留原有 decisions/译文）
  2. 对比 decisions.json，列出尚未判定的新论文 → data/pending.md
  3. 重新生成 index.html 并自检

用法：
  python build/update.py --xml "D:/Downloads/2027.acl.xml"
  python build/update.py --xml new.xml --no-build
  python build/update.py --xml new.xml --pending-out data/pending-2027.md

新论文在没有 decisions 时不会出现在页面上（默认按未收录处理），
所以你审完之后把判定补进 data/decisions.json，再跑一次即可。
"""
import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PY = sys.executable


def run(script, *args):
    cmd = [PY, str(ROOT / 'build' / script), *args]
    print(f'\n$ python build/{script} {" ".join(args)}'.rstrip(), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f'{script} 失败')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xml', required=True, help='新的 ACL XML 路径')
    ap.add_argument('--no-build', action='store_true', help='只解析，不重新生成页面')
    ap.add_argument('--pending-out', default=None, help='待判定清单输出路径')
    args = ap.parse_args()

    run('parse_metadata.py', '--xml', args.xml)

    papers = json.loads((DATA / 'papers.json').read_text(encoding='utf-8'))
    dec_path = DATA / 'decisions.json'
    decisions = json.loads(dec_path.read_text(encoding='utf-8')) if dec_path.exists() else []
    known = {d['id'] for d in decisions}
    new = [p for p in papers if p['id'] not in known]

    stamp = date.today().isoformat()
    out = Path(args.pending_out) if args.pending_out else DATA / 'pending.md'
    lines = [f'# 待判定论文（{stamp}）', '',
             f'本次 XML 共 {len(papers)} 条，已有判定 {len(papers) - len(new)} 条，新增 {len(new)} 条。', '',
             '处理方式：在 `data/decisions.json` 里为每条补一条记录（至少 `id` 与 `status`，'
             'status 取 `核心` / `延伸` / `排除`），再运行 `python build/build_site.py`。', '']
    for p in new:
        sig = '、'.join(p.get('signals', [])) or '—'
        lines.append(f"- [ ] `{p['id']}` · {sig} · {p['title']}")
        lines.append(f"      {p['url']}")
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'\n新增 {len(new)} 条，清单已写入 {out.relative_to(ROOT)}')
    if new:
        print('这些论文暂不会出现在页面上，补完判定后重新构建即可。')

    if not args.no_build:
        run('build_site.py')
        run('verify_site.py')

    zh = json.loads((DATA / 'zh.json').read_text(encoding='utf-8')) if (DATA / 'zh.json').exists() else {}
    tt = json.loads((DATA / 'titles.json').read_text(encoding='utf-8')) if (DATA / 'titles.json').exists() else {}
    picked = [p['id'] for p in papers
              if {d['id']: d for d in decisions}.get(p['id'], {}).get('status') in ('核心', '延伸')]
    missing_zh = [i for i in picked if i not in zh]
    missing_tt = [i for i in picked if i not in tt]
    print(f'\n入选 {len(picked)} 篇：中文摘要覆盖 {len(picked)-len(missing_zh)}/{len(picked)}，'
          f'中文标题覆盖 {len(picked)-len(missing_tt)}/{len(picked)}')
    if missing_zh or missing_tt:
        print('缺译文的论文会回退显示英文原文；补齐 data/zh.json 与 data/titles.json 即可。')


if __name__ == '__main__':
    main()
