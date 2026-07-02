# 🔬 ClinicalTrials Query & Analysis

基于 ClinicalTrials.gov API v2 的临床试验智能搜索与总结工具。支持关键词、时间范围、国家多维度筛选，输出结构化试验列表与智能总结。

## ✨ 功能特性

- **🔍 多维度搜索** — 关键词（基因/疾病/药物）+ 时间范围 + 国家 + 招募状态
- **🎯 智能 Biomarker 提取** — 自动从入排标准中识别 40+ 种肿瘤标志物（KRAS G12D、BRCA1/2、MSI-H 等）
- **📊 智能总结** — 自动生成搜索结果统计、阶段分布、靶点分布、热门药物、地区分布、申办方排行
- **🌍 全球覆盖** — 覆盖 ClinicalTrials.gov 所有注册试验，支持 50+ 国家/地区筛选
- **📋 双格式输出** — 交互式表格（默认）+ 纯 JSON（程序调用）
- **🔄 自动重试** — 内置 3 次重试 + 指数退避，应对 API 限速
- **🚫 无需 API Key** — ClinicalTrials.gov 是免费公开 API

## 📦 目录结构

```
clinicaltrials-search/
├── README.md                    # 本文件
├── SKILL.md                     # ZCode 技能定义文件
├── scripts/
│   └── search.py                # 核心搜索脚本
└── references/
    └── api_reference.md         # ClinicalTrials.gov API v2 参考文档
```

## 🚀 快速开始

### 依赖安装

```bash
pip install httpx
```

### 基本用法

```bash
# 1. 关键词搜索（必填）
python3 scripts/search.py --keyword "KRAS G12D"

# 2. 带时间范围
python3 scripts/search.py --keyword "KRAS G12D" --start-date 2024-01-01 --end-date 2025-12-31

# 3. 带国家筛选
python3 scripts/search.py --keyword "pancreatic cancer immunotherapy" --country China

# 4. 完整参数
python3 scripts/search.py \
  --keyword "BRCA1" \
  --start-date 2023-06-01 \
  --end-date 2025-06-01 \
  --country "United States" \
  --max-results 100

# 5. JSON 输出（便于程序调用）
python3 scripts/search.py --keyword "KRAS G12D" --max-results 10 --json
```

### 参数说明

| 参数 | 短写 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| `--keyword` | `-k` | ✅ | 搜索关键词（基因名、疾病名、药物名等） | — |
| `--start-date` | `-s` | ❌ | 起始日期 (YYYY-MM-DD) | — |
| `--end-date` | `-e` | ❌ | 结束日期 (YYYY-MM-DD) | — |
| `--country` | `-c` | ❌ | 试验开展国家（英文名，如 China, United States） | — |
| `--status` | | ❌ | 招募状态筛选 | RECRUITING,ACTIVE_NOT_RECRUITING |
| `--max-results` | `-n` | ❌ | 最大返回结果数 | 50（上限 1000） |
| `--json` | | ❌ | 以 JSON 格式输出（提示信息走 stderr） | — |

## 📊 输出示例

### 交互式表格

```
====================================================================================================
  临床试验搜索结果（共 9 条）
====================================================================================================

  1. [NCT07621718] Study of Zoldonrasib + Chemo ... (RASolute 305)
     阶段: Not specified  |  状态: 🟢 招募中
     药物: Zoldonrasib, Placebo, Oxaliplatin ...
     Biomarker: KRAS G12D, ATM, MET
     申办方: Revolution Medicines, Inc.
     国家: United States
     启动日期: 2026-05-22
     🔗 https://clinicaltrials.gov/study/NCT07621718

====================================================================================================
  📊 智能总结 — 关键词: "KRAS G12D"
====================================================================================================

  📈 搜索结果统计: 共 9 条试验
     • 招募中 (RECRUITING): 9

  🎯 Biomarker / 靶点分布:
     • MET: 9 █████████
     • ATM: 8 ████████
     • KRAS G12D: 7 ███████

  💊 热门药物/干预措施 Top 15:
     • Zoldonrasib: 1 █
     • Setidegrasib: 1 █

  🌍 地区分布 Top 10:
     • United States: 8 ████████
     • Australia: 4 ████

  🔑 关键发现:
     •   招募中试验占 100%（9/9）
     •   最热门靶点: MET(9), ATM(8), KRAS G12D(7)
     •   试验覆盖 22 个国家/地区
```

### JSON 输出

```bash
python3 scripts/search.py --keyword "KRAS G12D" --max-results 2 --json
```

```json
[
  {
    "nct_id": "NCT07621718",
    "title": "Study of Zoldonrasib + Chemo ...",
    "phase": "Not specified",
    "status": "RECRUITING",
    "drugs": ["Zoldonrasib", "Placebo", "Oxaliplatin", ...],
    "biomarker": "KRAS G12D, ATM, MET",
    "sponsor": "Revolution Medicines, Inc.",
    "countries": ["United States"],
    "start_date": "2026-05-22",
    "url": "https://clinicaltrials.gov/study/NCT07621718"
  }
]
```

> 提示信息输出到 stderr，JSON 数据输出到 stdout，可安全管道到 `jq` 等工具。

## 🧬 支持的 Biomarker 自动识别

脚本可从入排标准中自动提取以下 40+ 种肿瘤标志物：

| 类别 | Biomarker |
|------|-----------|
| **KRAS 亚型** | KRAS G12C, KRAS G12D, KRAS G12V, KRAS G12R, KRAS G12A, KRAS G13D, KRAS Q61H, KRAS |
| **RAS 家族** | NRAS, HRAS |
| **DDR / HRD** | BRCA1, BRCA2, PALB2, ATM, TP53, PTEN |
| **MSI/dMMR** | MSI-H, MMR 缺陷, Lynch (MLH1/MSH2/MSH6/PMS2) |
| **融合基因** | NTRK, NRG1, FGFR2, ALK, ROS1, RET |
| **其他靶点** | BRAF V600E, HER2/ERBB2, EGFR, VEGF, MET, CDKN2A, SMAD4, PIK3CA |
| **免疫标志物** | PD-L1, PD-1/PD-L1, CTLA-4, TMB-H, CAR-T, TCR-T |

> 特异性匹配优先：如文本中同时出现 "KRAS G12D" 和 "KRAS"，只保留更具体的 "KRAS G12D"。

## 🌍 常用搜索示例

```bash
# 胰腺癌 KRAS G12D — 过去 90 天
python3 scripts/search.py -k "KRAS G12D" -s 2026-04-04

# 中国开展的胰腺癌免疫治疗试验
python3 scripts/search.py -k "pancreatic cancer immunotherapy" -c China

# 全球 BRCA1/2 相关试验
python3 scripts/search.py -k "BRCA mutation solid tumor"

# ATR 抑制剂临床试验
python3 scripts/search.py -k "ATR inhibitor"

# mRNA 个性化疫苗
python3 scripts/search.py -k "mRNA neoantigen vaccine"

# KRAS 疫苗 + 美国开展
python3 scripts/search.py -k "KRAS vaccine" -c "United States"

# 过去一年中国启动的临床试验
python3 scripts/search.py -k "pancreatic cancer" -s 2025-07-01 -c China -n 100
```

## 🔧 技术细节

### API 端点

- **Base URL**: `https://clinicaltrials.gov/api/v2/studies`
- **协议**: HTTPS, GET
- **认证**: 无需 API Key
- **限速**: 无官方文档限制，内置 3 次重试 + 指数退避

### 时间范围搜索语法

使用 `query.term` 配合 `AREA[StartDate]RANGE[起始,结束]`：

```
# 2024年之后启动
query.term = KRAS G12D AND AREA[StartDate]RANGE[2024-01-01,MAX]

# 指定时间范围
query.term = KRAS G12D AND AREA[StartDate]RANGE[2023-01-01,2025-12-31]
```

可用日期字段：`StartDate`, `CompletionDate`, `LastUpdatePostDate`, `PrimaryCompletionDate`

### 国家搜索

`query.locn` 参数支持：国家英文名（China, United States, Japan）、城市名、州/省名。

### 依赖

- Python 3.10+
- httpx（异步 HTTP 客户端）

## 🤖 AI Agent 部署指南

### OpenClaw

**1. 安装技能**

```bash
# 从 GitHub 安装
clawdhub install clinicaltrials-query-analysis

# 或手动复制
git clone https://github.com/opencare-skillhub/clinicaltrials-query-analysis.git ~/.openclaw/skills/clinicaltrials-search
```

**2. 提示词**（写入 `~/.openclaw/workspace/TOOLS.md`）

```markdown
## ClinicalTrials Search Skill

Search ClinicalTrials.gov for clinical trials by keyword, date range, and country.

### When to use
- User asks about clinical trials for a gene/disease/drug
- User wants to find trials in a specific country or time period
- User needs trial statistics or biomarker analysis

### How to use
Run the search script with appropriate parameters:

python3 {baseDir}/scripts/search.py --keyword "QUERY" [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--country COUNTRY] [--max-results N] [--json]

### Examples
- "KRAS G12D试验" → python3 {baseDir}/scripts/search.py -k "KRAS G12D"
- "过去90天中国的胰腺癌试验" → python3 {baseDir}/scripts/search.py -k "pancreatic cancer" -s 2026-04-04 -c China
- "ATR抑制剂试验JSON" → python3 {baseDir}/scripts/search.py -k "ATR inhibitor" --json

### Notes
- No API key required (free public API)
- Default status filter: RECRUITING,ACTIVE_NOT_RECRUITING
- Use --json for programmatic consumption (output to stdout, logs to stderr)
- Built-in 40+ biomarker auto-extraction from eligibility criteria
```

**3. 验证安装**

```bash
openclaw status | grep clinicaltrials
python3 ~/.openclaw/skills/clinicaltrials-search/scripts/search.py -k "KRAS G12D" -n 3
```

---

### Codex CLI

**1. 安装技能**

```bash
git clone https://github.com/opencare-skillhub/clinicaltrials-query-analysis.git ./skills/clinicaltrials-search
```

**2. 配置**（写入 `.codex/settings.json`）

```json
{
  "skills": [
    {
      "name": "clinicaltrials-search",
      "description": "Search ClinicalTrials.gov for clinical trials by keyword, date range, and country with smart biomarker extraction and summary",
      "path": "./skills/clinicaltrials-search",
      "commands": {
        "search": "python3 ./skills/clinicaltrials-search/scripts/search.py --keyword \"{query}\" --json"
      }
    }
  ]
}
```

**3. 系统提示词**（写入 `.codex/instructions.md`）

```markdown
## ClinicalTrials Search

You have access to a ClinicalTrials.gov search skill. Use it when the user asks about:
- Clinical trials for specific genes (KRAS G12D, BRCA1, ATM, etc.)
- Trials in specific countries or time periods
- Drug development landscape for a target
- Biomarker distribution across trials

### Command
python3 ./skills/clinicaltrials-search/scripts/search.py --keyword "QUERY" [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--country COUNTRY] [--max-results N]

### Output
- Default: interactive table + smart summary (statistics, biomarker distribution, drug ranking, geography)
- With --json: structured JSON array for programmatic use

### Tips
- Always include --json when you need to parse results programmatically
- Use Chinese keywords for better results on Chinese trials
- Combine keyword + country for focused searches
```

---

### Hermes

**1. 安装技能**

```bash
git clone https://github.com/opencare-skillhub/clinicaltrials-query-analysis.git ./skills/clinicaltrials-search
```

**2. 技能注册**（写入 `.hermes/skills.yaml`）

```yaml
skills:
  - name: clinicaltrials-search
    description: "Search ClinicalTrials.gov for clinical trials by keyword, date range, and country. Auto-extracts 40+ biomarkers and generates smart summary with statistics, drug ranking, and geography distribution."
    path: ./skills/clinicaltrials-search
    entry: scripts/search.py
    runtime: python3
    parameters:
      - name: keyword
        required: true
        description: "Search keyword (gene, disease, drug name)"
      - name: start-date
        required: false
        description: "Start date filter (YYYY-MM-DD)"
      - name: end-date
        required: false
        description: "End date filter (YYYY-MM-DD)"
      - name: country
        required: false
        description: "Trial country (English name)"
      - name: max-results
        required: false
        default: 50
        description: "Max results (1-1000)"
      - name: json
        required: false
        type: boolean
        description: "Output as JSON"
```

**3. 系统提示词**（写入 `.hermes/SYSTEM.md`）

```markdown
## ClinicalTrials Search Skill

### Activation
When the user asks about clinical trials, drug development, gene mutations, or trial availability in specific regions, invoke the clinicaltrials-search skill.

### Invocation
python3 ./skills/clinicaltrials-search/scripts/search.py --keyword "{user_query}" [--start-date DATE] [--country COUNTRY] [--json]

### Response Guidelines
1. Run the search with the user's keyword
2. If user specifies a time range, add --start-date and --end-date
3. If user specifies a country, add --country
4. Summarize key findings from the output:
   - Total trials found and recruitment status breakdown
   - Top biomarkers/targets identified
   - Leading drugs/interventions
   - Geographic distribution
   - Notable findings (e.g., new drug classes, Chinese trial presence)
5. Provide the trial list in a structured table format
6. If results are sparse, suggest broadening the search (remove country filter, expand time range)

### Special Cases
- For KRAS subtypes: search exact mutation (e.g., "KRAS G12D" not just "KRAS")
- For DDR/HRD trials: search both "ATM ATR inhibitor" and specific drug names
- For vaccine trials: search "mRNA neoantigen vaccine" or "KRAS vaccine"
- For Chinese trials specifically: always add --country China
```

---

### 通用 Shell 别名

无论使用哪个 Agent 平台，都可以设置 shell 别名快速调用：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias ctsearch='python3 /path/to/skills/clinicaltrials-search/scripts/search.py'

# 使用
ctsearch -k "KRAS G12D" -n 20
ctsearch -k "pancreatic cancer" -c China -s 2025-01-01
ctsearch -k "ATR inhibitor" --json | jq '.[].nct_id'
```

## 📄 License

MIT License

## 🙏 致谢

小胰宝开源社区志愿者的❤️贡献
