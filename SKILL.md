---
name: clinicaltrials-search
description: 胰腺癌临床试验搜索与月报分析系统。支持单基因搜索、多基因专题分析、NCCN月报生成、多格式报告导出。覆盖KRAS/CLDN18.2/HER2/BRCA/MTAP/TROP2/TF/MET/MSLN/B7-H3/Nectin-4/pan-TRK/CDH17/CEACAM5等26个胰腺癌靶点，配置化基因列表，LLM深度分析，输出专业级月报。
---

# 临床试验搜索与月报分析技能

基于 ClinicalTrials.gov API v2 的胰腺癌临床情报系统，提供搜索、分析、月报、报告导出四大能力。

## 核心功能

### 1. 单基因搜索
搜索指定基因/靶点的临床试验，支持关键词、时间范围、国家筛选。

```bash
python3 scripts/search.py --keyword "KRAS G12D" --country China --max-results 50
```

### 2. 多基因专题分析
批量搜索多个基因并生成对比报告。

### 3. NCCN 月报生成 📋
生成本月胰腺癌临床试验月报，覆盖 14+ 核心靶点，LLM 深度分析，输出万字级 Markdown 报告。

```bash
# 生成完整月报（需 LLM_API_KEY）
python3 scripts/report_nccn.py

# 跳过 LLM，输出骨架
python3 scripts/report_nccn.py --no-llm

# 仅生成单基因报告
python3 scripts/report_nccn.py --gene kras
```

### 4. 多格式报告导出 📑
将搜索结果一键导出为 5 种格式，每种包含完整联络信息。

```bash
# 步骤1：抓取试验详细信息（PI、联络方式、中国医院）
python3 scripts/fetch_details.py

# 步骤2：生成 MD/DOCX/PDF/XLSX/HTML 报告
python3 scripts/generate_reports.py
```

输出按搜索条件组织在 `outputs/{关键词}_{状态}/` 目录下，包含：
- 招募状态、最近更新日期
- PI（主要研究者）姓名及机构
- 中心联络电话/邮箱
- 中国可报名医院列表及联系人

### 5. 交互式菜单
```bash
python3 scripts/main.py
```

菜单集成：1-单基因搜索 / 2-多基因专题 / 3-月报生成 / 4-报告导出

## 基因配置

覆盖 26 个胰腺癌靶点，分四组：

| 分组 | 基因 | 数量 |
|------|------|------|
| **A 指南推荐** | EGFR, KRAS, HER2(ERBB2), TROP2, CLDN18.2, BRCA1/2, ATM, BRAF V600E, NTRK, NRG1, RET, FGFR | 13 |
| **B 临床热点** | C-MET(MET), TF(组织因子) | 2 |
| **C 进阶靶点** | MSLN, B7-H3, Nectin-4, pan-TRK, CDH17, CEACAM5, MTAP(loss) | 7 |
| **D 补充检测** | MUC1, FOLR1, DLL3, CA125 | 4 |

配置文件: `config/genes.yaml`

## 月报结构

1. **本月概览** — 总体统计 + LLM 变化主题分析
2. **靶点专区** — 每个基因的试验统计 + 临床清单 + LLM 深度分析
3. **技术赛道** — RAS抑制剂/ADC/免疫/DDR/PROTAC/SHP2 六大赛道进展
4. **临床清单** — 全部试验合并表格
5. **中国可及性** — 中国试验统计 + 国产药物进展
6. **里程碑提醒** — 3期发布/FDA批准/关键数据
7. **术语速查** — 医学缩写一句话解释

## 环境变量

```bash
# LLM 配置（月报深度分析用，无则输出骨架）
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export LLM_MODEL="glm-4-flash"
```

## 文件结构

```
clinicaltrials-search/
├── config/genes.yaml          # 基因配置（26靶点）
├── scripts/
│   ├── search.py              # 单基因搜索
│   ├── report_nccn.py         # 月报生成器
│   ├── config_loader.py       # 配置加载器
│   ├── translator.py          # 翻译模块
│   ├── main.py                # 交互式菜单
│   ├── fetch_details.py       # 单试验详情抓取（PI/联络/中国医院）
│   └── generate_reports.py    # 多格式报告导出（5种格式）
├── templates/report_nccn.md   # 月报模板
├── outputs/                   # 生成的报告
│   ├── CLDN18.2_RECRUITING/   # 按搜索条件命名的子目录
│   └── cldn18_2_enriched.json # 详情缓存
└── references/api_reference.md
```

## 依赖

- Python 3.10+
- httpx, PyYAML, openai, openpyxl, python-docx, fpdf2
- ClinicalTrials.gov API 免费，无需 API Key
- LLM 分析需配置 LLM_API_KEY
