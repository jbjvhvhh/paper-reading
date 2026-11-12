# Paper Reading

> 项目名：**Paper Reading**（论文阅读）

把 ACL 2026 文集里与**剪枝 / LLM 效率 / 资源受限场景**相关的论文，整理成一个可以搜索、筛选、标记阅读状态的单文件网页。

- 931 篇入选（核心 595 / 延伸 336），另有 1,717 条已筛除、2 条源文件无摘要
- 每篇含：中英文标题、中文精简摘要、5 个关键词、效率结果、纳入理由、完整英文摘要、作者、DOI、论文页 / PDF / 代码链接
- 页面完全静态，**没有后端**；打开 `index.html` 即可用，数据已内嵌

## 目录结构

```
.
├─ index.html              # 生成的页面（可直接部署，勿手改）
├─ build/
│  ├─ parse_metadata.py    # ACL XML → data/papers.json
│  ├─ build_site.py        # data/* → index.html
│  ├─ update.py            # 一键年度更新（解析 + 对比 + 重建 + 自检）
│  └─ verify_site.py       # 自检：数据一致性、JS 语法
├─ data/
│  ├─ papers.json          # 全部 2,650 条书目信息（含摘要）
│  ├─ decisions.json       # 每条的筛选判定与依据
│  ├─ zh.json              # 中文精简摘要 + 关键词
│  ├─ titles.json          # 中文标题
│  ├─ curation.json        # 精选导读、剪枝对象、资源受限清单
│  └─ source.md            # 原始 XML 位置说明（XML 本身不入库）
└─ .github/workflows/build.yml
```

`data/` 是唯一需要维护的地方：改判定只动 `decisions.json`，补译文只动 `zh.json` / `titles.json`。

## 本地使用 / 重建

```bash
pip install lxml
python build/build_site.py     # 生成 index.html
python build/verify_site.py    # 自检
```

双击 `index.html`，或 `python -m http.server` 后访问。

## 年度更新

等新的文集出现（例如 `2027.acl.xml`）：

```bash
python build/update.py --xml "D:/Downloads/2027.acl.xml"
```

它会：

1. 重新解析 XML，覆盖 `data/papers.json`
2. 与 `decisions.json` 比对，把**新增论文**写成 `data/pending.md` 清单
3. 重建 `index.html` 并自检
4. 报告中文覆盖情况

**新论文在补上判定前不会出现在页面上。** 处理流程：

1. 打开 `data/pending.md`，按标题摘要判断
2. 在 `data/decisions.json` 补记录，最少需要 `{"id": "...", "status": "核心"}`（可选 `排除` / `延伸`）
3. 若是入选论文，再补 `data/titles.json` 与 `data/zh.json`（格式见下）
4. 重跑 `python build/build_site.py`

> 判定与翻译目前是人工 + 模型协作完成的，脚本不会自动分类。若要全自动，需要接一个 LLM API，这部分未包含在本仓库。

数据格式：

```jsonc
// data/decisions.json（数组）
[{"id": "2026.acl-long.23", "status": "核心", "category": "剪枝与稀疏化",
  "reason": "…", "tags": ["场景图剪枝"], "summary_zh": "…",
  "efficiency": "…", "evidence": "（摘要原文片段）", "priority": "优先读"}]

// data/titles.json（映射）
{"2026.acl-long.23": "CAPruner：提升大语言模型 3D 空间推理的概念邻接场景图剪枝器"}

// data/zh.json（映射）
{"2026.acl-long.23": {"zh": "中文精简摘要…", "kw": ["场景图剪枝", "空间推理"]}}
```

## 阅读状态（想读 / 已读）

卡片上的「想读 / 已读」按钮把状态写进浏览器 `localStorage`（键名 `paper-reading-fav-v1`），**不上传、不需要后台**。

- 顶部下拉可筛选「想读 / 已读 / 未标记」
- 状态按浏览器 + 域名隔离：换设备、换地址不会同步
- 清除浏览器数据会丢失；重要的话定期导出

## 部署

### GitHub Pages（免费）

1. 推到 GitHub，仓库 Settings → Pages → Source 选 `main` / 根目录
2. 访问 `https://<用户名>.github.io/<仓库名>/`
3. 推送到 `main` 后 `.github/workflows/build.yml` 会自动重建并部署

仓库自带的工作流还会在每月 1 日检查一次更新——在仓库 Variables 里设置 `ACL_XML_URL` 指向新的 XML 地址即可启用，否则跳过。

> **公开注意**：页面内含 931 篇论文的完整英文摘要，属他人作品。ACL Anthology 的**代码**是 Apache-2.0，但**摘要本身**不等于可以公开再分发。仅自己和课题组使用建议用私有仓库 + Cloudflare Pages（免费支持私有仓库）；要公开的话，建议改成只展示中文摘要与元数据，完整英文摘要留作本地版。

### 其他静态托管

Cloudflare Pages、Vercel、Netlify、对象存储 + CDN 都可以，直接上传整个目录即可（入口是 `index.html`）。

## 数据来源与边界

- 来源：`2026.acl.xml`（ACL Anthology 元数据），未联网核验官方收录状态
- 收录口径：以降低训练/推理的计算、内存、存储、Token、能耗或部署成本为实质目标；相关但不以效率为主贡献的标为「延伸」
- **中文摘要、中文标题与关键词由模型生成**，用于浏览与检索，可能与原文有偏差；以英文原文为准
- 效率数字均为摘要自述并保留原有比较条件，未做换算，也未独立复现
- 「资源受限」「剪枝对象」两类标注由摘要规则判定，未逐篇人工复核
- 首轮未命中的 1,040 条只做了标题复核，未逐篇深读
