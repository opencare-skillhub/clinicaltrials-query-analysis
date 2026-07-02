---
name: clinicaltrials-search
description: 搜索 ClinicalTrials.gov 临床试验数据库。用户输入关键词（如基因名 KRAS G12D、疾病名、药物名）、时间范围、国家后，输出匹配的临床试验列表及智能总结。
---

# 临床试验搜索技能

通过 ClinicalTrials.gov API v2 搜索全球临床试验，支持关键词、时间范围、国家多维度筛选，输出结构化试验列表与智能总结。

## 核心功能

1. **关键词搜索**：支持基因名（KRAS G12D、BRCA1）、疾病名（pancreatic cancer）、药物名（Gemcitabine）等自由关键词
2. **时间范围筛选**：支持指定起始/结束日期，筛选特定时间段内启动或更新的试验
3. **国家/地区筛选**：支持按试验开展国家筛选（如 China、United States、Japan）
4. **智能总结**：自动生成搜索结果摘要，包括靶点分布、阶段分布、热门药物、招募状态统计

## 使用指南

### 输入参数

用户需提供以下信息（关键词为必填，其余可选）：

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| 关键词 | ✅ | 搜索关键词，支持基因、疾病、药物等 | `KRAS G12D` |
| 开始日期 | ❌ | 筛选此日期之后启动/更新的试验 | `2024-01-01` |
| 结束日期 | ❌ | 筛选此日期之前启动/更新的试验 | `2025-12-31` |
| 国家 | ❌ | 试验开展国家/地区 | `China` |

### 调用方式

```bash
# 基本搜索
python3 scripts/search.py --keyword "KRAS G12D"

# 带时间范围
python3 scripts/search.py --keyword "KRAS G12D" --start-date 2024-01-01 --end-date 2025-12-31

# 带国家筛选
python3 scripts/search.py --keyword "pancreatic cancer immunotherapy" --country China

# 完整参数
python3 scripts/search.py --keyword "BRCA1" --start-date 2023-06-01 --end-date 2025-06-01 --country "United States" --max-results 50
```

### 输出格式

输出包含两部分：

#### 1. 临床试验列表

| # | NCT ID | 标题 | 阶段 | 状态 | 国家 | biomarker | 药物 | 链接 |
|---|--------|------|------|------|------|-----------|------|------|
| 1 | NCT07621718 | Zoldonrasib + Chemo... | Phase III | 招募中 | US | KRAS G12D | Zoldonrasib | [链接](https://clinicaltrials.gov/study/NCT07621718) |

#### 2. 智能总结

- 📊 搜索结果统计（总数、招募中/暂停/已完成）
- 🎯 靶点/Biomarker 分布
- 💊 热门药物/干预措施排行
- 📈 临床阶段分布
- 🌍 地区分布（如筛选了国家）

## 资源说明

- **`scripts/search.py`**: 核心搜索脚本，封装了完整的 API 调用、参数构建、结果解析和总结生成逻辑
- **`references/api_reference.md`**: ClinicalTrials.gov API v2 查询参数与字段参考

## 依赖

- Python 3.10+
- httpx（HTTP 异步客户端）
- 无需 API Key（ClinicalTrials.gov 是免费公开 API）

## 注意事项

- API 免费但有限速，脚本内置了重试和退避机制
- 国家筛选通过 `query.locn` 参数实现，支持国家英文名称
- 时间范围通过 `query.term` 的 `AREA[StartDate]RANGE[...]` 语法实现
- 默认返回最多 50 条结果，可通过 `--max-results` 调整（上限 1000）
