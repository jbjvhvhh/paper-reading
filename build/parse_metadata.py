#!/usr/bin/env python3
"""Parse an ACL Anthology XML file into data/papers.json.

Usage:
  python build/parse_metadata.py --xml path/to/2026.acl.xml
  python build/parse_metadata.py --xml new.xml --out data/papers.json --report
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / 'data' / 'papers.json'

# 用于给新论文打「可能有关系」的提示，不参与最终判定
SIGNALS = {
    '剪枝': r'prun|spars|sparse|compression|quantiz|distill|low.rank|binar|ternar',
    '效率': r'efficien|speed|latency|throughput|accelerat|memory|compute|FLOPs|budget|lightweight|compact|faster',
    '解码/缓存': r'speculative|early.exit|token.reduc|token.merg|KV.cache|key.value|cache|long.context|attention.sink',
    '受限': r'resource.constrain|limited.resource|low.resource|on.device|edge.device|mobile|energy|PEFT|LoRA|single.GPU',
}


def text(el):
    return ''.join(el.itertext()).strip() if el is not None else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xml', required=True, help='ACL Anthology XML 文件路径')
    ap.add_argument('--out', default=str(DEFAULT_OUT), help='输出 papers.json 路径')
    ap.add_argument('--report', action='store_true', help='与现有 decisions.json 对比，列出新增论文')
    args = ap.parse_args()

    try:
        from lxml import etree
    except ImportError:
        sys.exit('需要 lxml：pip install lxml')

    src = Path(args.xml)
    if not src.exists():
        sys.exit(f'找不到文件：{src}')

    tree = etree.parse(str(src))
    root = tree.getroot()
    collection = root.get('id') or src.stem

    papers = []
    for vol in root.findall('volume'):
        meta = vol.find('meta')
        vtype = vol.get('id')
        for p in vol.findall('paper'):
            pid = f'{collection}-{vtype}.{p.get("id")}'
            papers.append({
                'id': pid,
                'title': text(p.find('title')),
                'abstract': text(p.find('abstract')),
                'authors': '; '.join(
                    ' '.join(x for x in (text(a.find('first')), text(a.find('last'))) if x)
                    for a in p.findall('author')),
                'volume': vtype,
                'booktitle': text(meta.find('booktitle')),
                'year': text(meta.find('year')),
                'pages': text(p.find('pages')),
                'doi': text(p.find('doi')),
                'url': f'https://aclanthology.org/{pid}/',
                'pdf': f'https://aclanthology.org/{pid}.pdf' if p.find('pdf') is not None else '',
                'line': p.sourceline,
                'signals': [k for k, pat in SIGNALS.items()
                            if re.search(pat, text(p.find('title')) + ' ' + text(p.find('abstract')), re.I)],
            })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(papers, ensure_ascii=False, indent=0), encoding='utf-8')

    missing = sum(1 for p in papers if not p['abstract'])
    print(f'{len(papers)} 条记录 → {out}（无摘要 {missing} 条）')
    vols = {}
    for p in papers:
        vols[p['volume']] = vols.get(p['volume'], 0) + 1
    print('赛道：' + '，'.join(f'{k} {v}' for k, v in vols.items()))

    if args.report:
        dec_path = ROOT / 'data' / 'decisions.json'
        if dec_path.exists():
            known = {d['id'] for d in json.loads(dec_path.read_text(encoding='utf-8'))}
            new = [p for p in papers if p['id'] not in known]
            print(f'\n新增 {len(new)} 条（decisions.json 中尚无判定）')
            for p in new[:20]:
                print(f"  {p['id']}  {'/'.join(p['signals']) or '-'}  {p['title'][:70]}")
            if len(new) > 20:
                print(f'  …… 其余 {len(new)-20} 条省略')


if __name__ == '__main__':
    main()
