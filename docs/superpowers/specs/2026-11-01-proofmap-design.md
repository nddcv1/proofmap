# ProofMap：数学教材先修依赖图（设计文档）

- **状态**：设计定稿，未实现
- **日期**：2026-11-01
- **目标目录**：`D:\project`
- **数据基线**：`D:\zzt\math-kb\data\chunks.jsonl`（2026-11-01，5,727 chunks）
- **暂定名**：ProofMap（备选 `theorem-graph` / `proof-graph`）

## 0. 一句话

把非形式化的数学教材和笔记，变成一张**每条边都能引用原文**的“先修依赖图”，并生成可离线打开的单文件交互网页。

## 1. 背景

已有 `math-kb` 提供：

- 教材 OCR、切块、SQLite FTS5 + BGE-M3 混合检索、页码引用。
- `math-tutor` 分层讲解、`math-quiz` 出题批改。

缺的是**结构**：

- 检索能回答“这个概念在哪”，但不能回答“学这个之前要先会什么”“这个定理的证明用了谁”。
- Obsidian 笔记有 8 章、单文件可达 100 KB，但笔记之间的依赖、笔记对教材的覆盖没有结构化。

GitHub 现状（2026-11-01 用 GitHub API 关键词粗查）：

| 关键词 | 仓库数 | 头部项目 |
|---|---:|---|
| `theorem dependency graph` | 24 | `patrik-cihal/lean-graph`（56 star，Lean4 专用）；`holdenlee/depgraph`（7 star）；`c-elvira/rumbaa`（4 star） |
| `math latex linter` | 6 | 最高 8 star，均只做表层检查 |
| `latex formula search` | 10 | 最高 6 star，无结构相似搜索 |
| `proof spaced repetition` | 6 | 最高 1 star，多为 Lean |
| `textbook notes coverage` | 1 | 0 star |

结论：依赖图项目集中在 **Lean 形式化数学**（依赖是现成的）；面向非形式化教材、要求证据可追溯、并报告抽取精度的工具基本空白。这就是本项目的差异化位置。

## 2. 目标与非目标

### 2.1 目标

1. 从教材 chunks（一期）和 Obsidian 笔记（二期）构建**严格先修 DAG**。
2. 每条自动生成的边都能追溯到原文引用（chunk + quote + span）。
3. 生成单文件、离线可开的交互 HTML，支持章节过滤、先修焦点、学习路径。
4. 可评测：在手标黄金集上报告证明归属准确率和边的 precision / recall。
5. 抽取错误可通过 `corrections.yaml` 持续修正，不需要改代码。
6. v0.1 纯规则离线可跑；LLM 为可选增强，默认关闭。

### 2.2 非目标

- 不做定理自动证明、形式化验证或完整数学语义等价。
- 不做 PDF/OCR 解析（复用 math-kb 的产物）。
- 不做 Web 服务、多用户、协作编辑。
- v0.1 不做 Obsidian 插件；只输出 HTML。
- v0.1 不追求补全所有隐性定义；只用 `kind=definition` 的显式定义。
- v0.1 不做跨书依赖（如数分上 → 数分下、数分 → 线代）。

## 3. 已确认的设计决策

| 决策点 | 选择 | 理由 |
|---|---|---|
| 数据源 | 融合：教材 chunks 为骨架，Obsidian 笔记做覆盖标记 | 教材结构规整；笔记反映真实学习状态。分两期：v0.1 只做教材，v0.2 加笔记 |
| 图节点 | 定义 + 定理族（定理/引理/推论/命题） | 图聚焦“先修”；例题/习题不做节点 |
| 边语义 | 严格先修：证明中实际使用 | 图小但每根线有意义；能回答“学 X 前要会什么” |
| 定义边 | 算先修，但单独线型（概念边），可关闭 | 避免定义节点全部孤立；同时不污染定理依赖视图 |
| 抽取手段 | 规则为主 + 可选 LLM | 纯规则可离线复现；LLM 补隐式依赖，但必须锁定原文证据 |
| 输出 | 单文件 HTML（Cytoscape.js + dagre，库内嵌） | 零服务端、可分享、适合 GitHub 展示 |
| 方向约定 | `from` = 先修，`to` = 依赖方；`B → A` 表示 A 的证明用了 B | 与“学习方向”一致 |
| 证明归属 | 同节 + 向前 5 个 chunk 内最近节点，异常进人工清单 | 基线覆盖 449/475（94.5%） |

## 4. 数据基线（可行性依据）

### 4.1 语料

当前 `chunks.jsonl` 实际包含 5 本书（README 只列了前 3 本）：

| book_id | 书名 | chunks |
|---|---|---:|
| `shufeng` | 数学分析（第三版）上册，陈纪修 | 1,220 |
| `shuxia` | 数学分析（第三版）下册，陈纪修 | 1,439 |
| `lay` | 线性代数及其应用（原书第 5 版），Lay 等 | 1,967 |
| `gaoshu_c1` | 高等数学 C1 习题课讲义 | 348 |
| `mailuo` | 数学分析脉络（分析之路——群星谱系） | 753 |
| **合计** | | **5,727** |

v0.1 默认处理前三本教材；`gaoshu_c1` / `mailuo` 通过配置可选加入。所有统计口径为全部 5 本。

### 4.2 结构统计

`kind` 分布：

| kind | 数量 |
|---|---:|
| text | 3,050 |
| example | 773 |
| note | 585 |
| proof | 475 |
| theorem | 412 |
| exercise | 280 |
| definition | 152 |

关键事实：

1. **定理族 412 个**（`theorem` 模式包含 定理/引理/推论/命题）；证明 475 个。
2. 只有 **44 个定理 chunk 自带内联证明**；绝大多数证明是独立 chunk。
3. 475 个证明中：
   - 330 个紧跟在定理/例/习题之后；
   - 449 个能在同书、同节、向前 5 个 chunk 内找到最近的定理/例/习题（94.5%）；
   - 441 个与目标同节；
   - 26 个无法归属，需人工清单。
4. **显式编号引用覆盖率低**：475 个证明中只有 133 个（28%）出现至少一个 `定理/定义/引理/推论/命题 + 编号`；342 个完全没有。
5. 391 个定理 chunk 在前 120 字符内声明了编号；**256 个不同编号** → 编号必须在书/章作用域内解析。
6. 67 个 section/subsection 标题带“定理/公式/不等式”等命名特征，可作为命名引用别名来源。

### 4.3 对设计的直接影响

- 节点抽取可行，成本低（`kind` 已就绪）。
- 证明归属必须是一个独立、可评测的步骤；归属错则边全错。
- 纯规则的边召回上限不高，v0.1 要如实报告 recall；LLM 层是 v0.2 的召回主力，不是装饰。
- 编号跨书重复，主键绝不能直接用 OCR 编号。

## 5. 架构与数据流

```text
chunks.jsonl / notes.md
        │  adapter（mathkb v0.1 / notes v0.2）
        ▼
   nodes.jsonl ──► 证明归属 ──► attachments.jsonl
        │                              │
        │                              ▼
        └──────────────► 边抽取（L1–L4，v0.2 加 L5 LLM）
                                       │
                                       ▼
                                 edges.jsonl
                                       │
              corrections.yaml ────────┤
                                       ▼
                                  graph.json
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
              graph.html                         reports/*.md
```

原则：

- 所有中间产物是纯文本（JSONL/YAML），HTML 只是渲染器。
- 规则、LLM、人工纠错三层相互独立，可分别测试与替换。
- 同一输入 + 同一配置 → 同一输出；LLM 结果必须缓存。

中间契约（`schema_version: 1`）：

- `nodes.jsonl`：一行一个节点。
- `attachments.jsonl`：一行一个证明归属记录。
- `edges.jsonl`：一行一条边。
- `graph.json`：节点 + 边 + 元数据，供 HTML 渲染。

## 6. 数据模型

### 6.1 Node

```json
{
  "schema_version": 1,
  "id": "shuxia:定理9.2.2",
  "kind": "theorem",
  "subkind": "theorem",
  "label": "定理 9.2.2",
  "title": "上极限的性质",
  "aliases": ["定理 9.2.2", "上极限性质定理"],
  "book_id": "shuxia",
  "chapter": "第 9 章 数项级数",
  "section": "§ 9.2 上极限与下极限",
  "pdf_page": 31,
  "printed_page": 8,
  "statement": "……",
  "proof": "……",
  "source_chunks": ["shuxia-p0031-0123"],
  "formula_review": false
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `id` | 稳定主键，不依赖 OCR 编号的唯一性 |
| `kind` | `definition` 或 `theorem` |
| `subkind` | `theorem` / `lemma` / `corollary` / `proposition` |
| `label` | 印刷编号，如“定理 9.2.2”，只作展示与别名 |
| `title` | 首个句号前的标题或首句摘要 |
| `aliases` | 编号、标题、人工维护的常用名 |
| `statement` | 定理陈述；定义节点为定义正文 |
| `proof` | 归属后的证明文本；定义节点为空 |
| `source_chunks` | 可追溯的原始 chunk |

节点抽取规则：

- `kind=definition` → 定义节点。
- `kind=theorem` → 按首行前缀映射 `subkind`。
- `kind=proof` 不单独成节点，通过归属挂到目标节点。
- 同一本书同一 `label` 重复时保留正文最长者，其余进 `duplicate` 报告。
- `example` / `exercise` 在内部保留为“归属目标”，但**不进入图**；它们的证明不产生图边（见 7.3）。

### 6.2 ProofAttachment

```json
{
  "schema_version": 1,
  "proof_chunk": "shuxia-p0313-1053",
  "target_id": "shuxia:定理9.2.2",
  "target_kind": "theorem",
  "method": "proximity",
  "score": 0.92,
  "margin": 0.35,
  "status": "attached",
  "non_graph": false,
  "evidence": "证明中直接复述了定理条件"
}
```

`status`：`attached` / `ambiguous` / `unresolved`。

`target_kind` 为 `example` 或 `exercise` 时，该归属记录标记为 `non_graph`，不参与边抽取。

### 6.3 Edge

```json
{
  "schema_version": 1,
  "from": "shuxia:定理7.1.2",
  "to": "shuxia:定理9.2.2",
  "type": "numbered_ref",
  "confidence": "explicit",
  "proof_chunk": "shuxia-p0313-1053",
  "evidence": {
    "quote": "由定理 7.1.2 可知 …",
    "char_start": 123,
    "char_end": 156
  },
  "source": "rule"
}
```

| 字段 | 取值 |
|---|---|
| `type` | `numbered_ref` / `named_ref` / `anaphora_ref` / `definition_term` / `llm` / `manual` |
| `confidence` | `confirmed`（人工）/ `explicit`（显式引用）/ `inferred`（术语或 LLM）/ `tentative`（指代、多义） |
| `source` | `rule` / `llm` / `manual` |

方向：`from` 是先修，`to` 是依赖方。

### 6.4 ID 规则

1. 若 `label` 在本书内唯一且稳定：`{book_id}:{label去空格}`，如 `shuxia:定理9.2.2`。
2. 否则：`{book_id}:{section_key}:{ordinal}`，`section_key` 由章节标题规范化得到。
3. OCR 原始编号、标题、命名别名一律进 `aliases`。
4. 主键一经生成不随 OCR 修正变化；若必须变化，提供 `id_migrations.yaml`。

### 6.5 不变量

1. **方向**：所有边的 `from` 都是先修，`to` 都是依赖方。
2. **证据**：规则/LLM 生成的每条边必须有 `proof_chunk` + 原文 `quote` + `char_start/char_end`；无法定位的边丢弃并计数。
3. **人工边**：可以没有 quote，但必须有 `reason`，`confidence=confirmed`。
4. **主键独立**：主键不得由 OCR 编号单独推导。
5. **纠错最后应用**：优先级 `manual > explicit > inferred > tentative`。
6. **严格先修子图必须无环**；出现环不静默删除，写入审计报告。
7. **LLM 默认关闭**；缓存键 = 模型 + prompt 版本 + 输入哈希。
8. **HTML 只读**；纠错只写 YAML，避免两套真相。

## 7. 抽取设计

### 7.1 节点抽取

- 输入：`chunks.jsonl`。
- 步骤：
  1. 过滤 `kind ∈ {definition, theorem}`。
  2. 解析 `subkind`、`label`、`title`。
  3. 生成规范 ID 与别名。
  4. 按书内 `label` 去重。
  5. 输出 `nodes.jsonl` + `node_audit.md`（重复编号、缺失编号、异常标题）。
- 定义节点的一期缺口：只收 `kind=definition`，正文中的隐性定义（“称…为…”）留到 v0.2。

### 7.2 证明归属

目标：把 475 个 `proof` chunk 挂到正确的定理/例/习题上。

候选范围：

- 同一本书；
- 向前最多 5 个 chunk；
- 候选 `kind ∈ {theorem, example, exercise}`；
- 同节优先。

打分（0–1）：

| 信号 | 分值 |
|---|---:|
| 同 section | +0.45 |
| 距离 1 / 2 / 3 / 4 / 5 | +0.40 / +0.30 / +0.22 / +0.15 / +0.10 |
| 证明文本点名候选的 label 或 title | +0.30 |
| 候选已有内联证明 | −0.50 |

总分裁剪到 `[0, 1]`。

归属条件：

- 最高分 ≥ 0.55；
- 且与第二名差距 ≥ 0.15。

否则标记 `ambiguous`，不强行归属，进入 `attachment_audit.md`。

其它规则：

- 跨 section、跨书不作为候选。
- 若 `section` 为空，退化为“同 chapter + 距离阈值”，并将结果标记为 `ambiguous`，进入人工清单。
- `theorem` chunk 已有内联证明时不再归属后续 proof；若其后仍出现 proof chunk，进人工清单确认是否为重复证明。
- 目标为 `example` / `exercise` 时保留归属，但 `non_graph=true`，不生成图边。
- `corrections.yaml` 可 `force_attach` / `detach`。
- 26 个基线未归属项必须出现在审计报告中，逐条可处理。

### 7.3 边抽取

证据机制（所有层共用）：

- 在**原始 chunk 文本**上匹配；
- 保存 `quote` 与原始字符区间 `char_start/char_end`；
- 归一化只用于匹配，不改变证据定位；
- 同名多义、多候选时默认**不生成边**，进报告；`--include-ambiguous` 才生成 `tentative` 边。

#### L1 编号引用

- 正则：`(定理|引理|推论|命题|定义)\s*([0-9]+(?:\.[0-9]+)*)`。
- 作用域：
  - 带两级以上编号（如 `9.2.2`）→ 全书范围；
  - 单级编号（如 `定理 4`）→ 当前章；
  - 仍无法唯一 → 歧义，进报告。
- 置信度：`explicit`。

#### L2 命名引用

- 别名索引来源：
  - 教材命名 section/subsection（如“Rolle 定理”）；
  - `aliases.yaml` 人工维护；
  - 节点 title 中的专名。
- 匹配：最长优先。
- 通用词黑名单：`中值定理`、`基本定理`、`定理`、`公式`、`不等式` 等不在限定作用域内自动匹配。
- 置信度：`explicit`。

#### L3 指代引用

- 模式：`上述定理`、`前一定理`、`上节定理`、`由定理可知`、`由此可得`。
- 解析：同节最近的定理族节点。
- 置信度：`tentative`，默认不在 HTML 显示，需手动开启。

#### L4 定义术语边

- 从定义节点的 `label` / `title` / `aliases` 建术语索引。
- 术语准入：
  - 中文长度 ≥ 3，或包含拉丁字母/专名；
  - 黑名单：`函数`、`集合`、`连续`、`极限`、`导数`、`积分` 等过泛词；
  - 人工 `terms.yaml` 可增删。
- 扫描范围：定理陈述 + 证明。
- 置信度：`inferred`，`type=definition_term`，HTML 中默认虚线、可关闭。
- 概念边不参与“严格先修子图无环”检查，但单独报告概念环。

#### L5 可选 LLM（v0.2）

- 触发：对每个有证明的节点，构造**闭集候选**：
  - 同章节点；
  - FTS5 关键词 top-k；
  - 可选向量 top-k（BGE-M3 可用时）。
  - 候选取并集，上限 40，排除自身。
- Prompt 契约：
  - 输入：证明文本 + 候选列表（id/label/statement 摘要）；
  - 输出 JSON：`[{"candidate_id": "...", "quote": "..."}]`；
  - 明确要求：只选证明中**实际使用**的候选；必须给出证明原文的连续子串；不确定则不给。
- 校验：
  - `candidate_id` 必须在候选集内；
  - `quote` 必须在证明原文中逐字出现（空白归一化后）；
  - 否则丢弃并计数。
- 存储：`cache/llm_edges/{proof_chunk}.json`，键含模型 + prompt 版本 + 输入哈希。
- 置信度：`inferred`，`source=llm`。
- 默认关闭；`--llm` 开启；无 API key 时明确报错，不静默降级。

### 7.4 人工纠错

`corrections.yaml`：

```yaml
proof_attachments:
  force:
    - proof_chunk: shuxia-p0313-1053
      target: shuxia:定理9.2.2
      reason: 证明正文复述了该定理条件
  detach:
    - proof_chunk: shuxia-p0401-1402
      reason: 实为例题证明，误挂到定理

aliases:
  shufeng:定理5.2.3:
    - Rolle 定理
    - 罗尔定理

edges:
  add:
    - from: shuxia:定义9.2.1
      to: shuxia:定理9.2.2
      type: manual
      reason: 证明直接使用上极限定义
  remove:
    - from: shuxia:定理3.1.2
      to: shuxia:定理9.2.2
      reason: OCR 编号误匹配
```

应用顺序：规则 → LLM → 人工。人工 `add` 可覆盖同向同类型边的置信度。

### 7.5 审计

`attachment_audit.md`：

- 已归属 / 歧义 / 未归属数量；
- 26 个基线未归属项清单；
- 目标为例题/习题的归属清单（不生成边，但要可见）。

`edge_audit.md`：

- 各类型、各置信度边数量；
- 未解析引用、歧义引用清单；
- 零边证明（自含还是漏抽？）；
- 孤立节点；
- 严格先修子图中的环；
- 重复/缺失编号。

`node_audit.md`：

- 重复 label、异常标题、缺失页码、公式 OCR 存疑。

## 8. 评测设计

### 8.1 黄金集

- 规模：30 个证明。
- 分层：前三本教材各 10 个，覆盖不同章节与证明长度。
- 标注内容：
  - 证明归属目标；
  - 证明实际使用的定理族节点；
  - 证明实际使用的定义节点；
  - 歧义/无法判断项单独记录。
- 存储：`gold/edges.yaml`，格式与 `edges.jsonl` 同构，人工确认。
- 标注协议：先只看证明，不看自动结果；二遍复核；歧义处记录理由。

### 8.2 指标

| 指标 | 定义 |
|---|---|
| 归属准确率 | 黄金集中归属正确的证明数 / 30 |
| 边 precision（按类型） | TP / (TP + FP) |
| 边 recall（按类型） | TP / (TP + FN) |
| 歧义率 | 歧义引用数 / 全部引用数 |
| 未归属率 | 未归属证明数 / 全部证明数 |

报告按书拆分，并给出规则层与 LLM 层对照。

### 8.3 目标

- 证明归属准确率 ≥ 95%（黄金集）。
- 显式边（L1/L2）precision ≥ 95%。
- recall 首版如实报告，不设虚高目标；LLM 层上线后再评估提升幅度。
- 每个数字都可复现：`proofmap eval` 输出机器可读 JSON + Markdown 表。

### 8.4 README 呈现

README 必须包含：

- 黄金集规模与标注协议；
- precision / recall 表格；
- 已知限制（隐性定义未覆盖、指代边默认隐藏、跨书依赖未做）；
- 一张由私有数据生成的截图/GIF（不提交原始数据）。

## 9. 单文件 HTML

- 技术：Cytoscape.js + dagre 布局，库文件 vendored 进仓库；HTML 内嵌 `graph.json`。
- 离线：不请求任何外部 CDN；双击即开。
- 默认视图：只加载一本书的一章，避免 500+ 节点毛线球。
- 交互：
  - 书/章过滤；
  - 节点搜索（编号或别名）；
  - 点击节点 → 右侧面板：陈述、证明、页码、入边/出边及证据原文；
  - 焦点模式：只看上游先修（反向 BFS）或下游被依赖；
  - 一键生成“学习路径”：上游子图拓扑排序；
  - 边类型开关：定理依赖 / 概念边 / LLM 推断 / 指代边；
  - 可疑环红色高亮。
- 视觉编码：

| 元素 | 含义 |
|---|---|
| 蓝色方形 | 定义 |
| 橙色圆形 | 定理 |
| 三角 | 引理/推论/命题 |
| 实线 | 显式编号/命名引用 |
| 虚线 | 定义概念边 |
| 点线 | LLM 推断 |
| 细点线 | 指代边（默认隐藏） |
| 加粗 | 人工确认 |
| 红色 | 可疑环 |
| 灰色 | 孤立节点 |

- 性能：500–800 节点目标流畅；超过 1,000 节点提示先按章过滤。v0.2 再做按 section 折叠。
- URL hash 保存当前过滤/选中节点，便于分享。

## 10. CLI

```text
proofmap build   --chunks <path> --out build/ [--book shufeng,shuxia,lay]
proofmap audit   --build build/
proofmap render  --build build/ --out proofmap.html [--chapter ...]
proofmap query   prereq <node-id> [--depth all]
proofmap query   dependents <node-id>
proofmap eval    --build build/ --gold gold/edges.yaml
```

约定：

- 所有命令支持 `--json`，便于脚本消费。
- `build` 默认不调用 LLM；`--llm` 显式开启。
- `--include-ambiguous` 才生成 `tentative` 边。
- 退出码：0 成功；1 输入错误；2 审计发现阻塞问题（如无法解析的配置）；3 评测未达标（仅 `eval`）。

## 11. 代码结构

```text
D:\project\
  pyproject.toml
  README.md
  proofmap/
    __init__.py
    cli.py
    model.py
    io.py
    adapters/
      __init__.py
      mathkb.py
      notes.py            # v0.2
    attach.py
    resolve.py
    extract/
      __init__.py
      numbered.py
      named.py
      anaphora.py
      definitions.py
      llm.py              # v0.2
    corrections.py
    graph.py
    audit.py
    eval.py
    render/
      __init__.py
      template.html
      vendor/cytoscape.min.js
      vendor/dagre.min.js
  gold/
    edges.yaml
  examples/
    demo/
  tests/
    test_node_extraction.py
    test_attachment.py
    test_reference_resolution.py
    test_evidence_span.py
    test_corrections.py
    test_graph_cycles.py
```

## 12. 里程碑

### v0.1（MVP）

交付：

1. 仓库骨架、数据模型、JSONL I/O。
2. math-kb chunks 适配器。
3. 节点抽取 + 去重 + 稳定 ID。
4. 证明归属 + 审计报告。
5. L1–L4 规则边 + `corrections.yaml`。
6. `graph.json` + 环检测。
7. 单文件 HTML（vendored 依赖，离线）。
8. 30 个证明的黄金集 + 基线评测报告。
9. 单元测试（节点、归属、引用解析、证据 span、纠错、环检测）。

验收：

- 黄金集归属准确率 ≥ 95%；
- 显式边 precision ≥ 95%；
- 一条命令生成 HTML，离线打开可交互；
- 每条自动边都能在面板里看到证据原文；
- 审计报告无未解释的环。

### v0.2

- Obsidian 笔记适配器 + 覆盖/薄弱标记（教材节点 ↔ 笔记节点匹配）。
- L5 LLM 闭集层 + 缓存 + 规则/LLM 对照评测。
- 更多隐性定义抽取句式。
- HTML 支持按 section 折叠。

### v0.3

- 通用 Markdown/JSONL 输入、英文教材支持。
- 可选例题/习题节点（叶子，可开关）。
- 跨书依赖（如数分上 → 数分下）。
- 可选 Obsidian Canvas 导出。

## 13. 开源与数据边界

- 仓库**只放工具**：不提交教材 OCR、原始 PDF、完整笔记。
- `.gitignore` 覆盖：`data/`、`notes/`、`raw/`、`build/`、`*.pdf`、`cache/`。
- 示例数据：只放用户自己可授权的小样本或公有领域内容；README 截图使用私有数据生成。
- 核心不绑定 math-kb：`nodes.jsonl` / `edges.jsonl` 是公开契约，math-kb 只是一个 adapter。
- 不强制 GPU 或嵌入模型；v0.1 纯 Python 可跑。
- 名称与 License 发布前确定（建议 MIT 或 Apache-2.0）。

## 14. 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| OCR 编号错/重复 | 边连错节点 | 稳定 ID + 编号仅作别名 + 作用域解析 + 审计 |
| 证明归属错 | 边全错 | 94.5% 邻近归属 + 26 项人工清单 + `force_attach` |
| 多义引用 | 假边 | 默认不生成，进报告；`--include-ambiguous` 才生成 tentative |
| LLM 幻觉 | 假边 | 闭集候选 + 原文子串校验 + 缓存 + 默认关闭 |
| 图太乱 | 不可用 | 章节过滤 + 焦点模式 + 边开关 + dagre 分层 |
| 隐性定义缺失 | 概念链断裂 | 一期写入 limitations；二期句式抽取 |
| 范围膨胀 | 做不完 | v0.1 明确不做笔记/LLM/插件；里程碑约束 |
| 版权/隐私 | 不能开源 | 只发工具；示例数据自有权；截图替代原始数据 |
| 评测样本小 | 数字不稳 | 30 个分层样本 + 按书报告；结论标注样本量 |

## 15. 开放问题（不阻塞 v0.1）

- 项目名与 License：发布前定；暂用 ProofMap / MIT 候选。
- LLM 候选集是否引入本地嵌入：v0.2 再定；v0.1 不需要。
- 例题/习题节点：v0.3 可选，不进入“严格先修”子图。
- 跨书依赖：v0.3；v0.1 按书隔离。
- Obsidian 插件：暂不做；先验证 HTML 的使用频率。

## 16. v0.1 实现偏差与实测（2026-11-01）

### 16.1 与最初设计的偏差

- 渲染器实现为包 `proofmap/render/`（`render_html` 在 `__init__.py`），而不是单文件 `render.py`；模板与 vendor 文件放在同一目录。
- 新增 `proofmap/build.py` 作为端到端流水线入口，CLI 只是薄封装。
- 证明归属：同节、距离 1 的候选在分数 ≥0.55 时直接归属，不再要求 0.15 分差；距离 ≥2 仍要求 0.15。真实数据表明“证明里提到相邻定理名”会让紧邻定理因分差 0.10 被误判歧义。
- 重复编号：同书、同章、同节的重复编号视为分页/重复排版，合并为一个节点（合并 statement、source_chunks、aliases）；跨章节的重复编号保留为独立 fallback 节点。编号后缀 `′` / `’` / `*` 会保留，避免把“定理 9.2.2′”误合并进“定理 9.2.2”。
- 命名引用：拉丁别名至少 3 个字符才参与匹配；定义节点不参与 `named_ref`（定义由 `definition_term` 负责）。
- 证据 `quote` 取匹配所在的句子（上限 160 字符），而不是固定 ±40 字符，避免短证明里每条边重复整段证明。
- 同一对节点只保留最强的一条证据边，优先级 `manual > numbered_ref > named_ref > llm > anaphora_ref > definition_term`。
- HTML 默认显示节点最多的书、依赖最密的章节，并在孤立节点比例 >20% 时默认隐藏孤立节点；可手动开启。稀疏图用 `concentric` 布局，稠密图用 `dagre`。
- 跨书引用不解析；例如数分下引用数分上的定理会进入 `edge_audit.md`。

### 16.2 实测基线

- 本地 math-kb 5 本书：545 节点、151 条边、0 个环。
- 475 个证明：386 `attached`、55 `ambiguous`、34 `unresolved`。
- 84 条未解析/歧义引用。
- Demo：12 节点、11 条边、9 个证明全部归属；8 个 demo 黄金证明的 attachment accuracy / edge precision / recall 均为 1.000。
- 结构化公开导出：`render --structure-only` 剥离陈述、证明、别名、source_chunks 和证据引用，仅保留章节、编号、页码与依赖边。
- 自动化测试：53 个通过。

### 16.3 尚未完成

- 30 个真实教材证明的黄金集尚未标注；真实数据不报告 precision/recall。
- LLM 闭集补边、Obsidian 笔记覆盖、跨书依赖、隐性定义抽取均为后续版本。

## 附录 A：数据核查方法

基线数字来自对 `D:\zzt\math-kb\data\chunks.jsonl` 的一次性统计：

- 按 `kind`、`book_id` 计数；
- 对每个 `kind=proof` chunk，向前 5 个 chunk 内查找最近的 `theorem/example/exercise`；
- 统计证明文本中编号引用正则的命中数；
- 统计定理 chunk 首 120 字符内的编号声明。

数据基线日期为 2026-11-01；math-kb 重建索引或修正 OCR 后，数字可能变化，实施时需重新测量并更新本文档第 4 节。

## 附录 B：术语

- **定理族**：定理、引理、推论、命题。
- **证明归属**：判断一个 `proof` chunk 在证明哪个节点。
- **严格先修边**：目标节点证明中实际使用了来源节点。
- **概念边**：定理陈述/证明中使用了某定义术语，来源为定义节点。
- **证据 span**：证明原文中的连续字符区间，用于人工核验。
- **黄金集**：人工标注的证明与依赖集合，用于计算 precision / recall。
