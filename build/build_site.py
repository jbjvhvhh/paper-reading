#!/usr/bin/env python3
"""Build index.html from data/ (no network, no server).

Inputs (all optional except papers.json + decisions.json):
  data/papers.json     bibliographic metadata for every record
  data/decisions.json  screening decision per record
  data/zh.json         {"<id>": {"zh": "...", "kw": [...]}}
  data/titles.json     {"<id>": "中文标题"}
  data/curation.json   {"reading_guide": [...], "pruning_objects": {...}, "resource_ids": [...]}
Output:
  index.html           self-contained page (data inlined)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
OUT = ROOT / 'index.html'

def load(name, default):
    path = DATA / name
    if not path.exists():
        print(f'  ! {name} 不存在，使用默认值', file=sys.stderr)
        return default
    return json.loads(path.read_text(encoding='utf-8'))

papers = load('papers.json', [])
decisions = {d['id']: d for d in load('decisions.json', [])}
cur = load('curation.json', {})
zh = load('zh.json', {})
tt = load('titles.json', {})

volumes = {'long': '主会长文', 'short': '主会短文', 'demo': '系统演示',
           'srw': '学生研讨会', 'tutorials': '教程', 'industry': '工业赛道'}

selected = []
for p in papers:
    d = decisions.get(p['id'])
    if not d or d.get('status') not in ('核心', '延伸'):
        continue
    selected.append({**p, **d})
selected.sort(key=lambda r: ({'核心': 0, '延伸': 1}[r['status']],
                             r.get('category', ''), {'优先读': 0, '专题读': 1}.get(r.get('priority'), 2),
                             r['id']))
guide = set(cur.get('reading_guide', []))
prune_map = cur.get('pruning_objects', {})
res_ids = set(cur.get('resource_ids', []))

rows = []
for n, r in enumerate(selected, 1):
    z = zh.get(r['id'], {})
    rows.append([
        n, r['status'], r.get('priority', ''), r.get('category', ''), r['id'], r['title'],
        z.get('zh') or r.get('summary_zh', ''), r.get('efficiency', ''), r.get('tags', []),
        prune_map.get(r['id'], ''), '是' if r['id'] in res_ids else '未单列', r.get('reason', ''),
        r.get('authors', ''), volumes.get(r.get('volume'), ''), r.get('year', ''), r.get('pages', ''),
        r.get('doi', ''), r.get('url', ''), r.get('pdf', ''),
        [u for u in (r.get('code_urls') or '').split('\n') if u],
        r.get('abstract', ''), r.get('evidence', ''),
        1 if r['id'] in guide else 0,
        z.get('kw', []),
        tt.get(r['id'], '')
    ])
data = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
cats = []
for r in rows:
    if r[3] not in cats:
        cats.append(r[3])
cats.sort(key=lambda c: -sum(1 for r in rows if r[3] == c))
meta = {'cats': cats, 'vols': [v for v in volumes.values() if any(r[13] == v for r in rows)],
        'n': len(rows), 'core': sum(1 for r in rows if r[1] == '核心'),
        'ext': sum(1 for r in rows if r[1] == '延伸'),
        'prune': sum(1 for r in rows if r[9]), 'res': sum(1 for r in rows if r[10] == '是')}
payload = json.dumps(meta, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Paper Reading</title>
<style>
:root{
  --ink:#111827; --ink2:#374151; --muted:#6b7280; --line:#e5e7eb; --bg:#f7f8fa;
  --card:#ffffff; --accent:#0f766e; --accent-soft:#e6f4f1;
  --gold:#b45309; --gold-soft:#fef3c7; --slate-soft:#eef2f7;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg); color:var(--ink);
  font:14px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.site{
  background:linear-gradient(180deg,#0f2b33 0%,#123c40 100%); color:#fff;
  padding:28px 24px 22px;
}
.wrap{max-width:1080px;margin:0 auto}
header.site h1{margin:0 0 6px;font-size:21px;letter-spacing:.3px;font-weight:650}
header.site p{margin:0;color:#a7c4c6;font-size:13px}
.statline{display:flex;gap:18px;flex-wrap:wrap;margin-top:14px;font-size:13px;color:#cfe6e4}
.statline b{color:#fff;font-weight:650}
.toolbar{
  position:sticky;top:0;z-index:20;background:rgba(247,248,250,.94);
  backdrop-filter:saturate(180%) blur(10px);border-bottom:1px solid var(--line);
  padding:12px 24px;
}
.searchrow{max-width:1080px;margin:0 auto;display:flex;gap:10px;align-items:center}
.searchbox{position:relative;flex:1}
.searchbox input{
  width:100%;padding:11px 36px 11px 13px;border:1px solid #d7dbe0;border-radius:9px;
  font-size:14px;background:#fff;color:var(--ink);outline:none;
}
.searchbox input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(15,118,110,.12)}
.searchbox .kbd{
  position:absolute;right:10px;top:50%;transform:translateY(-50%);
  font-size:11px;color:#9aa3af;border:1px solid #e3e6ea;border-radius:4px;padding:1px 5px;background:#fafbfc;
}
.clearbtn{border:1px solid #d7dbe0;background:#fff;border-radius:9px;padding:10px 12px;font-size:13px;color:var(--ink2);cursor:pointer}
.clearbtn:hover{border-color:#b9c0c8}
.filters{max-width:1080px;margin:9px auto 0;display:flex;flex-direction:column;gap:8px}
.frow{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
#f-cat{flex-wrap:nowrap;overflow-x:auto;padding-bottom:3px;scrollbar-width:thin}
#f-cat::-webkit-scrollbar{height:5px}
#f-cat::-webkit-scrollbar-thumb{background:#d7dde3;border-radius:3px}
.flabel{font-size:12px;color:var(--muted);min-width:66px;letter-spacing:.04em;flex-shrink:0}
.chip{
  border:1px solid #dbe0e6;background:#fff;color:var(--ink2);border-radius:20px;
  padding:5px 11px;font-size:12.5px;cursor:pointer;line-height:1.4;transition:.12s;
}
.chip:hover{border-color:#b9c6c4}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.chip .n{opacity:.6;margin-left:4px;font-size:11px}
.chip.on .n{opacity:.85}
.chip.gold.on{background:var(--gold);border-color:var(--gold)}
select.sortsel{
  border:1px solid #dbe0e6;background:#fff;border-radius:8px;padding:6px 9px;font-size:12.5px;color:var(--ink2);
}
main{max-width:1080px;margin:0 auto;padding:18px 24px 80px}
.resultbar{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:4px 0 14px;flex-wrap:wrap}
.resultbar .cnt{font-size:13px;color:var(--muted)}
.resultbar .cnt b{color:var(--ink);font-size:15px}
.card{
  background:var(--card);border:1px solid var(--line);border-radius:11px;
  padding:16px 18px;margin-bottom:12px;transition:box-shadow .15s,border-color .15s;
}
.card:hover{box-shadow:0 2px 10px rgba(17,24,39,.06);border-color:#d3d9e0}
.card.guide{border-left:3px solid var(--gold)}
.toprow{display:flex;gap:9px;align-items:flex-start}
.idx{font-size:12px;color:#9aa3af;font-variant-numeric:tabular-nums;min-width:28px;padding-top:3px}
.badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:5px}
.b{font-size:11.5px;padding:2px 8px;border-radius:5px;line-height:1.6;white-space:nowrap}
.b.core{background:var(--accent-soft);color:#0b5d57;font-weight:600}
.b.ext{background:var(--slate-soft);color:#4b5563}
.b.cat{background:#f3f4f6;color:#4b5563;border:1px solid #e9ecef}
.b.pri{background:#fff7ed;color:#9a3412}
.b.guide{background:var(--gold-soft);color:#92400e;font-weight:600}
.b.prune{background:#eef6ff;color:#1d4ed8}
.b.res{background:#f0fdf4;color:#15803d}
.card h2{margin:0 0 5px;font-size:15.5px;font-weight:600;line-height:1.5;letter-spacing:.1px}
.card h2 a{color:#111827}
.card h2 a:hover{color:var(--accent);text-decoration:none}
.zht{font-size:14.5px;color:#3f4a5a;font-weight:600;line-height:1.55;margin:-2px 0 6px;letter-spacing:.1px}
.byline{font-size:12.5px;color:var(--muted);margin-bottom:9px}
.byline .dot{margin:0 6px;color:#d1d5db}
.summary{font-size:13.5px;color:var(--ink2);margin:0 0 9px;line-height:1.75;text-align:justify}
.kwrow{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:0 0 10px}
.kwl{font-size:11.5px;color:#9aa3af;letter-spacing:.04em}
.kwc{font-size:12px;color:#0b5d57;background:var(--accent-soft);border-radius:4px;padding:2px 8px}
.eff{
  font-size:12.5px;background:#f8fafc;border:1px solid #e8edf2;border-left:3px solid var(--accent);
  padding:7px 10px;border-radius:0 6px 6px 0;color:#334155;margin:0 0 9px;
}
.eff.warn{border-left-color:#d97706;background:#fffdf5;border-color:#f3e8cf}
.eff b{color:#0f766e;font-weight:600}
.tags{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px}
.tag{font-size:11.5px;color:#5b6472;background:#f4f6f8;border-radius:4px;padding:1.5px 7px}
.links{display:flex;gap:14px;align-items:center;font-size:12.5px;flex-wrap:wrap}
.links a{display:inline-flex;align-items:center;gap:4px}
.links .sep{color:#e5e7eb}
.mini{border:none;background:none;color:var(--muted);font-size:12.5px;cursor:pointer;padding:0;display:inline-flex;gap:4px;align-items:center}
.mini:hover{color:var(--accent);text-decoration:underline}
.fbtn{border:1px solid #dbe0e6;background:#fff;color:#7b8494;font-size:11.5px;padding:2px 9px;border-radius:20px;cursor:pointer;line-height:1.55;transition:.12s}
.fbtn:hover{border-color:#b9c6c4;color:var(--accent)}
.fbtn.on.want{background:#fef3c7;border-color:#fcd34d;color:#92400e}
.fbtn.on.done{background:#dcfce7;border-color:#86efac;color:#15803d}
.favchip{font-weight:600}
.favchip.fw{background:#fef3c7;color:#92400e}
.favchip.fd{background:#dcfce7;color:#15803d}
.favline{margin-left:10px;color:#8a93a1;font-size:12px}
.card.fav-want{border-left:3px solid #f59e0b}
.card.fav-done{border-left:3px solid #22c55e}
.card.guide.fav-want,.card.guide.fav-done{border-left-width:3px}
.abstract{margin:12px 0 0;padding:12px 14px;background:#fbfcfd;border:1px solid #edf0f4;border-radius:8px;display:none}
.abstract.open{display:block}
.abstract .h{font-size:11.5px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}
.abstract p{margin:0 0 10px;font-size:13px;line-height:1.7;color:#374151;text-align:justify}
.abstract .ev{font-size:12.5px;background:#fffef8;border:1px dashed #e5dcc4;border-radius:6px;padding:8px 10px;color:#6b5b3e}
.reason{font-size:12.5px;color:var(--muted);margin-top:8px}
.reason b{color:#4b5563;font-weight:600}
mark{background:#fde68a;color:inherit;padding:0 1px;border-radius:2px}
.empty{text-align:center;color:var(--muted);padding:70px 20px;font-size:14px}
.more{display:block;width:100%;margin:16px 0 0;padding:12px;border:1px dashed #cfd6dd;background:#fff;
  border-radius:9px;color:var(--ink2);font-size:13px;cursor:pointer}
.more:hover{border-color:var(--accent);color:var(--accent)}
footer{max-width:1080px;margin:0 auto;padding:26px 24px 40px;color:#9aa3af;font-size:12px;line-height:1.8;border-top:1px solid var(--line)}
@media (max-width:640px){
  header.site{padding:20px 16px}.toolbar{padding:10px 16px}main{padding:14px 16px 60px}
  .card{padding:14px}.flabel{min-width:100%}
}
</style>
</head>
<body>
<header class="site"><div class="wrap">
  <h1>Paper Reading</h1>
  <p>剪枝 · LLM 效率 · 资源受限场景 — 摘自 2026.acl.xml 元数据与摘要</p>
  <div class="statline">
    <span>共 <b id="s-n"></b> 篇</span><span>核心 <b id="s-core"></b></span><span>延伸 <b id="s-ext"></b></span>
    <span>剪枝 <b id="s-prune"></b></span><span>资源受限 <b id="s-res"></b></span>
  </div>
</div></header>

<div class="toolbar"><div class="searchrow">
  <div class="searchbox">
    <input id="q" type="search" placeholder="搜索标题、摘要、作者、关键词（空格分隔＝同时包含）" autocomplete="off" spellcheck="false">
    <span class="kbd">/</span>
  </div>
  <select class="sortsel" id="sort" title="排序">
    <option value="rank">默认（核心优先）</option>
    <option value="rank2">阅读优先级</option>
    <option value="year">年份</option>
    <option value="title">标题 A–Z</option>
  </select>
  <select class="sortsel" id="read" title="阅读状态（保存在本机浏览器）">
    <option value="">全部状态</option>
    <option value="want">想读</option>
    <option value="done">已读</option>
    <option value="none">未标记</option>
  </select>
  <button class="clearbtn" id="reset">重置</button>
</div>
<div class="filters">
  <div class="frow" id="f-cat"><span class="flabel">类别</span></div>
</div></div>

<main>
  <noscript><div class="empty">本页需要启用 JavaScript 才能搜索与筛选。若在受限环境中打开，请改用附带的 Excel 或 CSV 版本。</div></noscript>
  <div class="resultbar">
    <div class="cnt">命中 <b id="cnt">0</b> 篇 <span id="cntnote"></span>
      <span class="favline" id="favcnt"></span></div>
    <div class="cnt" id="activefilters"></div>
  </div>
  <div id="list"></div>
  <div id="empty" class="empty" style="display:none">没有匹配的论文，试试减少筛选项或换关键词。</div>
  <button class="more" id="more" style="display:none"></button>
</main>

<footer>
  <div>数据来源：2026.acl.xml（用户提供的本地文件）。共 2,650 条记录，其中 931 篇进入本库；核心 595、延伸 336。</div>
  <div>效率数字均为摘要原文自述并保留原有比较条件，不等同于独立复现；摘要为 XML 原文，未改写。</div>
  <div>「资源受限」「剪枝对象」由摘要规则判定，未逐篇人工复核。阅读优先级为编辑建议，非质量排名。</div>
</footer>

<script>
const META = __META__;
const RAW  = __DATA__;
const K = {n:0,st:1,pr:2,cat:3,id:4,t:5,sum:6,eff:7,tags:8,prune:9,res:10,reason:11,auth:12,vol:13,yr:14,pg:15,doi:16,url:17,pdf:18,code:19,abs:20,ev:21,guide:22,kw:23};
const DATA = RAW.map(r=>({
  n:r[0],status:r[1],pri:r[2],cat:r[3],id:r[4],title:r[5],summary:r[6],eff:r[7],tags:r[8]||[],
  prune:r[9],res:r[10],reason:r[11],authors:r[12],vol:r[13],year:r[14],pages:r[15],
  doi:r[16],url:r[17],pdf:r[18],code:r[19],abs:r[20],ev:r[21],guide:!!r[22],kw:r[23]||[],zht:r[24]||'',
  hay:(r[5]+' '+(r[24]||'')+' '+r[6]+' '+(r[8]||[]).join(' ')+' '+(r[23]||[]).join(' ')+' '+r[12]+' '+(r[9]||'')+' '+r[20]).toLowerCase()
}));

const state={q:'',status:new Set(),cat:new Set(),pri:new Set(),prune:false,res:false,guide:false,sort:'rank',read:''};
const FKEY='paper-reading-fav-v1';
let FAV={};
try{FAV=JSON.parse(localStorage.getItem(FKEY)||'{}')||{}}catch(e){FAV={}}
function saveFav(){try{localStorage.setItem(FKEY,JSON.stringify(FAV))}catch(e){}}
function favOf(id){return FAV[id]||''}
function setFav(id,v){ if(FAV[id]===v) delete FAV[id]; else FAV[id]=v; saveFav(); }
function paintFav(card){
  const id=card.dataset.id, v=favOf(id);
  card.querySelectorAll('.fbtn').forEach(b=>b.classList.toggle('on',b.dataset.fav===v));
  card.classList.toggle('fav-want',v==='want');
  card.classList.toggle('fav-done',v==='done');
  let chip=card.querySelector('.favchip');
  if(!v){ if(chip) chip.remove(); return; }
  if(!chip){ chip=document.createElement('span'); chip.className='b favchip'; card.querySelector('.badges').appendChild(chip); }
  chip.textContent = v==='want'?'想读':'已读';
  chip.className = 'b favchip '+(v==='want'?'fw':'fd');
}
function paintAllFav(){ document.querySelectorAll('.card').forEach(paintFav); favCount(); }
function favCount(){
  const ids=Object.keys(FAV);
  const w=ids.filter(k=>FAV[k]==='want').length, d=ids.filter(k=>FAV[k]==='done').length;
  const el=document.getElementById('favcnt'); if(el) el.textContent = ids.length? `想读 ${w} · 已读 ${d}` : '';
}
const PAGE=60; let shown=0, view=[];

function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
const RE_SPECIAL=".^$*+?()[]{}|\\\\/-";
function escapeRe(s){let o="";for(const c of s){o+=RE_SPECIAL.indexOf(c)>=0?"\\\\"+c:c;}return o;}
function hl(s,q){
  const e=esc(s);
  const terms=q.trim().split(" ").filter(Boolean);
  if(!terms.length) return e;
  const re=new RegExp("("+terms.map(escapeRe).join("|")+")","gi");
  return e.replace(re,"<mark>$1</mark>");
}

function buildCats(){
  const box=document.getElementById('f-cat');
  META.cats.forEach(c=>{
    const n=DATA.filter(d=>d.cat===c).length;
    const b=document.createElement('button');
    b.className='chip'; b.dataset.cat=c;
    b.innerHTML=esc(c)+'<span class="n">'+n+'</span>';
    b.onclick=()=>{toggle(state.cat,c);b.classList.toggle('on');apply();};
    box.appendChild(b);
  });
}
function toggle(set,v){set.has(v)?set.delete(v):set.add(v);}

function apply(){
  const q=state.q.trim().toLowerCase();
  const terms=q.split(" ").filter(Boolean);
  view=DATA.filter(d=>{
    if(state.status.size&&!state.status.has(d.status))return false;
    if(state.cat.size&&!state.cat.has(d.cat))return false;
    if(state.pri.size&&!state.pri.has(d.pri))return false;
    if(state.prune&&!d.prune)return false;
    if(state.res&&d.res!=='是')return false;
    if(state.guide&&!d.guide)return false;
    if(state.read==='none'&&favOf(d.id))return false;
    if(state.read&&state.read!=='none'&&favOf(d.id)!==state.read)return false;
    if(terms.length&&!terms.every(t=>d.hay.includes(t)))return false;
    return true;
  });
  const order={core:0,ext:1}, po={'优先读':0,'专题读':1,'补充读':2};
  if(state.sort==='rank') view.sort((a,b)=>(order[a.status==='核心'?'core':'ext']-order[b.status==='核心'?'core':'ext'])||a.n-b.n);
  else if(state.sort==='rank2') view.sort((a,b)=>(po[a.pri]??3)-(po[b.pri]??3)||a.n-b.n);
  else if(state.sort==='year') view.sort((a,b)=>String(b.year).localeCompare(String(a.year))||a.n-b.n);
  else view.sort((a,b)=>a.title.localeCompare(b.title,'en'));
  document.getElementById('cnt').textContent=view.length;
  document.getElementById('cntnote').textContent=view.length?'':'' ;
  shown=0; document.getElementById('list').innerHTML='';
  render(PAGE);
  const f=[];
  if(state.status.size)f.push([...state.status].join('/'));
  if(state.cat.size)f.push([...state.cat].join('、'));
  if(state.pri.size)f.push([...state.pri].join('/'));
  if(state.prune)f.push('剪枝专题');
  if(state.res)f.push('资源受限');
  if(state.guide)f.push('精选导读');
  if(q)f.push('“'+state.q.trim()+'”');
  document.getElementById('activefilters').textContent=f.length?'筛选：'+f.join(' · '):'';
}

function cardHTML(d,q){
  const b=[];
  b.push('<span class="b '+(d.status==='核心'?'core':'ext')+'">'+esc(d.status)+'</span>');
  b.push('<span class="b cat">'+esc(d.cat)+'</span>');
  if(d.guide)b.push('<span class="b guide">精选</span>');
  if(d.prune)b.push('<span class="b prune">剪枝 · '+esc(d.prune)+'</span>');
  if(d.res==='是')b.push('<span class="b res">资源受限</span>');
  if(d.pri)b.push('<span class="b pri">'+esc(d.pri)+'</span>');
  const meta=[esc(d.authors||''),d.vol?esc(d.vol):'',d.year?esc(d.year):'',d.pages?'pp. '+esc(d.pages):''].filter(Boolean);
  const links=['<a href="'+esc(d.url)+'" target="_blank" rel="noopener">论文页 ↗</a>'];
  if(d.pdf)links.push('<a href="'+esc(d.pdf)+'" target="_blank" rel="noopener">PDF ↗</a>');
  if(d.doi)links.push('<a href="https://doi.org/'+esc(d.doi)+'" target="_blank" rel="noopener">DOI ↗</a>');
  if(d.code&&d.code.length)links.push('<a href="'+esc(d.code[0])+'" target="_blank" rel="noopener">代码 ↗</a>');
  links.push('<span class="sep">|</span>');
  links.push('<button class="mini" data-copy="'+esc(d.url)+'">复制链接</button>');
  const effCls=/未给出|未报告|不可比|缺少|冲突|无单位/.test(d.eff)?'eff warn':'eff';
  return '<article class="card'+(d.guide?' guide':'')+'" data-id="'+esc(d.id)+'">'+
    '<div class="toprow"><div class="idx">'+d.n+'</div><div style="flex:1;min-width:0">'+
      '<div class="badges">'+b.join('')+'</div>'+
      '<h2><a href="'+esc(d.url)+'" target="_blank" rel="noopener">'+hl(d.title,q)+'</a></h2>'+
      (d.zht?'<div class="zht">'+hl(d.zht,q)+'</div>':'')+
      '<div class="byline">'+meta.join('<span class="dot">·</span>')+'</div>'+
      (d.summary?'<p class="summary">'+hl(d.summary,q)+'</p>':'')+
      (d.eff?'<div class="'+effCls+'"><b>效率</b> '+hl(d.eff,q)+'</div>':'')+
      (d.kw&&d.kw.length?'<div class="kwrow"><span class="kwl">关键词</span>'+d.kw.map(t=>'<span class="kwc">'+esc(t)+'</span>').join('')+'</div>':'')+
      '<div class="links">'+links.join('')+
        '<span class="sep">|</span>'+
        '<button class="fbtn want" data-fav="want">想读</button>'+
        '<button class="fbtn done" data-fav="done">已读</button>'+
        '<span class="sep">|</span><button class="mini" data-more="1">展开摘要 ↓</button></div>'+
      '<div class="abstract">'+
        '<div class="h">Abstract（原文）</div><p>'+hl(d.abs,q)+'</p>'+
        (d.ev?'<div class="ev"><b>纳入依据：</b>'+hl(d.ev,q)+'</div>':'')+
        '<div class="reason"><b>纳入理由：</b>'+hl(d.reason,q)+'</div>'+
        (d.tags&&d.tags.length?'<div class="tags" style="margin-top:8px">'+d.tags.map(t=>'<span class="tag">'+esc(t)+'</span>').join('')+'</div>':'')+
      '</div>'+
    '</div></div></article>';
}

function render(n){
  const end=Math.min(view.length,shown+n);
  const html=view.slice(shown,end).map(d=>cardHTML(d,state.q.trim())).join('');
  document.getElementById('list').insertAdjacentHTML('beforeend',html);
  shown=end;
  paintAllFav();
  const more=document.getElementById('more');
  if(shown<view.length){more.style.display='block';more.textContent='显示更多（还有 '+(view.length-shown)+' 篇）';}
  else more.style.display='none';
  document.getElementById('empty').style.display=view.length?'none':'block';
}

document.addEventListener('click',e=>{
  const fb=e.target.closest('.fbtn');
  if(fb){
    const card=fb.closest('.card');
    setFav(card.dataset.id, fb.dataset.fav);
    paintFav(card); favCount();
    if(state.read) apply();
    return;
  }
  const m=e.target.closest('[data-more]');
  if(m){const a=m.closest('.card').querySelector('.abstract');a.classList.toggle('open');
    m.textContent=a.classList.contains('open')?'收起摘要 ↑':'展开摘要 ↓';return;}
  const c=e.target.closest('[data-copy]');
  if(c){navigator.clipboard?.writeText(c.dataset.copy).then(()=>{c.textContent='已复制 ✓';setTimeout(()=>c.textContent='复制链接',1200);});}
});

const qEl=document.getElementById('q');
let tmr;
qEl.addEventListener('input',()=>{clearTimeout(tmr);tmr=setTimeout(()=>{state.q=qEl.value;apply();},160);});
document.addEventListener('keydown',e=>{
  if(e.key==='/'&&document.activeElement!==qEl){e.preventDefault();qEl.focus();}
  if(e.key==='Escape'&&document.activeElement===qEl){qEl.value='';state.q='';apply();qEl.blur();}
});
document.getElementById('reset').onclick=()=>{
  qEl.value='';state.q='';state.status.clear();state.cat.clear();state.pri.clear();
  state.prune=state.res=state.guide=false;state.read='';
  const rd=document.getElementById('read'); if(rd)rd.value='';
  document.querySelectorAll('.chip.on').forEach(b=>b.classList.remove('on'));
  apply();
};
document.querySelectorAll('[data-f]').forEach(btn=>{
  const f=btn.dataset.f;
  if(f==='status'||f==='pri')btn.onclick=()=>{toggle(f==='status'?state.status:state.pri,btn.dataset.v);btn.classList.toggle('on');apply();};
  else btn.onclick=()=>{state[f]=!state[f];btn.classList.toggle('on');apply();};
});
document.getElementById('sort').onchange=e=>{state.sort=e.target.value;apply();};
document.getElementById('read').onchange=e=>{state.read=e.target.value;apply();};
document.getElementById('more').onclick=()=>render(PAGE);

document.getElementById('s-n').textContent=META.n;
document.getElementById('s-core').textContent=META.core;
document.getElementById('s-ext').textContent=META.ext;
document.getElementById('s-prune').textContent=META.prune;
document.getElementById('s-res').textContent=META.res;
buildCats();apply();
</script>
</body>
</html>
"""
out = HTML.replace('__META__', payload).replace('__DATA__', data)
OUT.write_text(out, encoding='utf-8')
print(f'index.html  {len(out.encode("utf-8"))/1024/1024:.2f} MB  {len(rows)} 篇  {OUT}')
