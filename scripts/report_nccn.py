#!/usr/bin/env python3
"""
NCCN 胰腺癌临床试验月报生成器。

执行流程：
  1. 加载 genes.yaml 配置
  2. 确定时间窗口（过去30天）
  3. 逐基因搜索 → 缓存 JSON
  4. 汇总统计
  5. LLM 生成深度分析段落
  6. 组装最终报告

用法：
  python3 report_nccn.py                    # 生成月报
  python3 report_nccn.py --no-llm           # 跳过LLM，输出骨架
  python3 report_nccn.py --gene kras        # 仅生成单基因报告
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# 添加脚本目录到路径
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from config_loader import load_config, get_report_genes, get_llm_config, get_gene_by_id
from search import ClinicalTrialsSearch

# 路径常量
_SKILL_ROOT = _SCRIPT_DIR.parent
_CACHE_DIR = _SKILL_ROOT / "outputs" / "gene_cache"
_REPORT_DIR = _SKILL_ROOT / "outputs" / "reports"
_TEMPLATE_PATH = _SKILL_ROOT / "templates" / "report_nccn.md"

# 状态中文名
_STATUS_CN = {
    "RECRUITING": "招募中",
    "ACTIVE_NOT_RECRUITING": "暂停招募",
    "COMPLETED": "已完成",
    "TERMINATED": "已终止",
    "WITHDRAWN": "已撤回",
    "SUSPENDED": "暂停",
    "NOT_YET_RECRUITING": "尚未招募",
}

_STATUS_ICON = {
    "RECRUITING": "🟢",
    "ACTIVE_NOT_RECRUITING": "🟡",
    "COMPLETED": "✅",
    "TERMINATED": "🔴",
    "WITHDRAWN": "⚫",
    "SUSPENDED": "🟠",
    "NOT_YET_RECRUITING": "⚪",
}


# ---------------------------------------------------------------------------
# LLM 深度分析
# ---------------------------------------------------------------------------
def llm_analyze(prompt: str, config: dict[str, Any], use_llm: bool = True) -> str:
    """调用 LLM 生成深度分析段落。无 API Key 时返回占位符。"""
    if not use_llm:
        return f"<!-- LLM 跳过。Prompt: {prompt[:100]}... -->"

    llm_cfg = get_llm_config(config)
    if not llm_cfg["api_key"]:
        return f"> ⚠️ 未配置 LLM_API_KEY，深度分析段落待补充。\n> Prompt: {prompt[:80]}..."

    try:
        from openai import OpenAI
    except ImportError:
        return "> ⚠️ openai 库未安装，请运行 pip install openai"

    try:
        client = OpenAI(
            api_key=llm_cfg["api_key"],
            base_url=llm_cfg["base_url"] or None,
        )
        resp = client.chat.completions.create(
            model=llm_cfg["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是胰腺癌临床研究专家，擅长将临床试验数据转化为病友可理解的深度分析。"
                        "要求：专业、简洁、无废话和重复，重点给出清晰指引。"
                        "输出 Markdown 格式，控制在 300-500 字。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=llm_cfg["temperature"],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"> ⚠️ LLM 调用失败: {exc}"


# ---------------------------------------------------------------------------
# 数据获取与缓存
# ---------------------------------------------------------------------------
async def fetch_gene_trials(
    gene: dict[str, Any],
    start_date: str,
    end_date: str,
    max_results: int = 50,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """搜索单个基因的临床试验，支持缓存。"""
    month_tag = datetime.now().strftime("%Y-%m")
    cache_file = _CACHE_DIR / f"{gene['id']}_{month_tag}.json"

    # 检查缓存
    if use_cache and cache_file.exists():
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    # 逐个 search_term 搜索并合并去重
    client = ClinicalTrialsSearch()
    all_trials: list[dict[str, Any]] = []
    seen_nct: set[str] = set()

    try:
        for term in gene.get("search_terms", []):
            trials = await client.search(
                keyword=term,
                start_date=start_date,
                end_date=end_date,
                max_results=max_results,
            )
            for t in trials:
                nct = t.get("nct_id", "")
                if nct and nct not in seen_nct:
                    t["_gene_id"] = gene["id"]
                    t["_gene_name"] = gene["name"]
                    all_trials.append(t)
                    seen_nct.add(nct)
    finally:
        await client.aclose()

    # 写入缓存
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_trials, f, ensure_ascii=False, indent=2)

    return all_trials


# ---------------------------------------------------------------------------
# 统计汇总
# ---------------------------------------------------------------------------
def compute_stats(trials: list[dict[str, Any]]) -> dict[str, Any]:
    """计算试验统计。"""
    status_counter = Counter(t.get("status", "Unknown") for t in trials)
    phase_counter = Counter(t.get("phase", "Not specified") for t in trials)

    # Biomarker 分布
    biomarker_counter: Counter[str] = Counter()
    for t in trials:
        bm = t.get("biomarker", "")
        if bm:
            for b in bm.split(", "):
                biomarker_counter[b] += 1

    # 药物分布
    drug_counter: Counter[str] = Counter()
    for t in trials:
        for drug in t.get("drugs", []):
            drug_counter[drug] += 1

    # 国家分布
    country_counter: Counter[str] = Counter()
    for t in trials:
        for c in t.get("countries", []):
            country_counter[c] += 1

    # 申办方分布
    sponsor_counter: Counter[str] = Counter()
    for t in trials:
        sp = t.get("sponsor", "")
        if sp:
            sponsor_counter[sp] += 1

    return {
        "total": len(trials),
        "status": dict(status_counter.most_common()),
        "phase": dict(phase_counter.most_common()),
        "biomarker": dict(biomarker_counter.most_common(15)),
        "drug": dict(drug_counter.most_common(15)),
        "country": dict(country_counter.most_common(10)),
        "sponsor": dict(sponsor_counter.most_common(10)),
    }


def stats_to_table(stats: dict[str, Any]) -> str:
    """将统计转为 Markdown 表格。"""
    lines = []

    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 试验总数 | {stats['total']} |")
    lines.append(f"| 招募中 | {stats['status'].get('RECRUITING', 0)} |")
    lines.append(f"| 暂停招募 | {stats['status'].get('ACTIVE_NOT_RECRUITING', 0)} |")
    lines.append(f"| 涉及国家 | {len(stats['country'])} |")
    lines.append(f"| 涉及药物 | {len(stats['drug'])} |")
    lines.append("")

    lines.append("**招募状态分布：**")
    lines.append("")
    for status, count in stats["status"].items():
        cn = _STATUS_CN.get(status, status)
        icon = _STATUS_ICON.get(status, "❓")
        bar = "█" * count
        lines.append(f"- {icon} {cn} ({status}): {count} {bar}")
    lines.append("")

    lines.append("**临床阶段分布：**")
    lines.append("")
    for phase, count in stats["phase"].items():
        bar = "█" * count
        lines.append(f"- {phase}: {count} {bar}")
    lines.append("")

    lines.append("**热门靶点 Top 10：**")
    lines.append("")
    for bm, count in list(stats["biomarker"].items())[:10]:
        bar = "█" * count
        lines.append(f"- {bm}: {count} {bar}")
    lines.append("")

    lines.append("**热门药物 Top 10：**")
    lines.append("")
    for drug, count in list(stats["drug"].items())[:10]:
        lines.append(f"- {drug}: {count}")
    lines.append("")

    lines.append("**地区分布 Top 10：**")
    lines.append("")
    for c, count in list(stats["country"].items())[:10]:
        lines.append(f"- {c}: {count}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 基因专区生成
# ---------------------------------------------------------------------------
def format_gene_section(gene: dict[str, Any], trials: list[dict[str, Any]], llm_content: str) -> str:
    """生成单个基因的分析专区。"""
    stats = compute_stats(trials)

    lines = []
    lines.append(f"### {gene['name']}（{gene.get('cn_name', '')}）")
    lines.append("")
    lines.append(f"> {gene.get('cn_desc', '')}")
    lines.append("")

    if not trials:
        lines.append("⚠️ 本月未检索到相关试验。")
        lines.append("")
        return "\n".join(lines)

    # 统计概要
    lines.append(f"- **试验数**：{stats['total']} 项 | **招募中**：{stats['status'].get('RECRUITING', 0)} 项")
    if stats["biomarker"]:
        top_bm = list(stats["biomarker"].items())[:3]
        bm_str = ", ".join(f"{bm}({cnt})" for bm, cnt in top_bm)
        lines.append(f"- **Biomarker**：{bm_str}")
    if stats["drug"]:
        top_drugs = list(stats["drug"].items())[:3]
        drug_str = ", ".join(f"{d}({cnt})" for d, cnt in top_drugs)
        lines.append(f"- **热门药物**：{drug_str}")
    lines.append("")

    # 临床清单（精简表格）
    lines.append("| NCT ID | 标题 | 阶段 | 状态 | 药物 | 国家 |")
    lines.append("|--------|------|------|------|------|------|")
    for t in trials[:15]:
        nct = t.get("nct_id", "")
        title = t.get("title", "")[:50]
        phase = t.get("phase", "")
        status_cn = _STATUS_CN.get(t.get("status", ""), t.get("status", ""))
        drugs = ", ".join(t.get("drugs", [])[:2])
        countries = ", ".join(t.get("countries", [])[:2])
        lines.append(f"| [{nct}]({t.get('url', '')}) | {title} | {phase} | {status_cn} | {drugs} | {countries} |")

    if len(trials) > 15:
        lines.append(f"| ... | *还有 {len(trials) - 15} 项* | | | | |")
    lines.append("")

    # LLM 深度分析
    lines.append("**📊 深度分析：**")
    lines.append("")
    lines.append(llm_content)
    lines.append("")

    return "\n".join(lines)


def format_trial_list_all(all_trials: list[dict[str, Any]]) -> str:
    """生成全部试验的合并清单。"""
    if not all_trials:
        return "本月无匹配试验。"

    # 按 gene_name 分组
    by_gene: dict[str, list[dict[str, Any]]] = {}
    for t in all_trials:
        gene_name = t.get("_gene_name", "其他")
        by_gene.setdefault(gene_name, []).append(t)

    lines = []
    for gene_name, trials in by_gene.items():
        lines.append(f"#### {gene_name}（{len(trials)} 项）")
        lines.append("")
        lines.append("| NCT ID | 标题 | 阶段 | 状态 | 国家 |")
        lines.append("|--------|------|------|------|------|")
        for t in trials[:10]:
            nct = t.get("nct_id", "")
            title = t.get("title", "")[:40]
            phase = t.get("phase", "")
            status_cn = _STATUS_CN.get(t.get("status", ""), "")
            countries = ", ".join(t.get("countries", [])[:2])
            lines.append(f"| [{nct}]({t.get('url', '')}) | {title} | {phase} | {status_cn} | {countries} |")
        if len(trials) > 10:
            lines.append(f"| ... | *+{len(trials) - 10} 项* | | | |")
        lines.append("")

    return "\n".join(lines)


def format_glossary(genes: list[dict[str, Any]]) -> str:
    """生成医学术语速查表。"""
    lines = ["| 缩写 | 全称 | 作用 |", "|------|------|------|"]
    for g in genes:
        name = g["name"]
        cn_name = g.get("cn_name", "")
        cn_desc = g.get("cn_desc", "")
        lines.append(f"| {name} | {cn_name} | {cn_desc} |")
    lines.append("")
    # 通用术语
    lines.extend([
        "| ADC | 抗体偶联药物 | 抗体+毒素的精准制导导弹 |",
        "| PARP | 多聚ADP核糖聚合酶 | DDR靶向，合成致死策略 |",
        "| ATR | ATM和Rad3相关激酶 | DDR靶向，合成致死策略 |",
        "| PROTAC | 蛋白水解靶向嵌合体 | 降解靶蛋白的分子胶 |",
        "| SHP2 | 含SH2结构域蛋白酪氨酸磷酸酶 | RAS/MAPK通路 |",
        "| CAR-T | 嵌合抗原受体T细胞 | 基因工程免疫细胞疗法 |",
        "| TCR-T | T细胞受体工程T细胞 | 靶向特定突变蛋白 |",
        "| DDR | DNA损伤反应 | 细胞修复DNA的系统 |",
        "| HRD | 同源重组缺陷 | PARP抑制剂敏感标志 |",
        "| ICI | 免疫检查点抑制剂 | PD-1/PD-L1/CTLA-4抗体 |",
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
async def generate_report(
    gene_filter: str | None = None,
    use_llm: bool = True,
) -> str:
    """生成月报主流程。"""
    config = load_config()

    # 确定基因列表
    if gene_filter:
        gene = get_gene_by_id(gene_filter, config)
        if not gene:
            return f"错误：基因 '{gene_filter}' 未在配置中找到"
        genes = [gene]
    else:
        genes = get_report_genes(config)

    # 时间窗口（过去30天）
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    month_label = datetime.now().strftime("%Y年%m月")

    print(f"📋 月报生成开始")
    print(f"   时间窗口: {start_date} ~ {end_date}")
    print(f"   基因数量: {len(genes)}")
    print(f"   LLM 分析: {'启用' if use_llm else '禁用'}")
    print()

    # Step 1: 逐基因搜索
    print("🔍 Step 1: 逐基因搜索 ClinicalTrials.gov ...")
    gene_data: dict[str, list[dict[str, Any]]] = {}
    all_trials: list[dict[str, Any]] = []

    for i, gene in enumerate(genes, 1):
        print(f"   [{i}/{len(genes)}] {gene['name']} ...", end=" ", flush=True)
        trials = await fetch_gene_trials(gene, start_date, end_date, max_results=50)
        gene_data[gene["id"]] = trials
        all_trials.extend(trials)
        print(f"{len(trials)} 项")

    print(f"\n   ✅ 共检索到 {len(all_trials)} 项试验\n")

    # Step 2: 总体统计
    print("📊 Step 2: 生成总体统计 ...")
    overall_stats = compute_stats(all_trials)
    stats_table = stats_to_table(overall_stats)
    print("   ✅ 完成\n")

    # Step 3: LLM 深度分析
    print("🤖 Step 3: LLM 深度分析 ...")

    # 准备数据摘要给 LLM
    data_summary = json.dumps({
        "total_trials": len(all_trials),
        "gene_count": len(genes),
        "status_dist": overall_stats["status"],
        "top_biomarkers": list(overall_stats["biomarker"].items())[:5],
        "top_drugs": list(overall_stats["drug"].items())[:5],
        "top_countries": list(overall_stats["country"].items())[:5],
        "phase_dist": overall_stats["phase"],
    }, ensure_ascii=False, indent=2)

    # 3.1 总体分析
    print("   [1/9] 总体分析 ...", end=" ", flush=True)
    llm_overview = llm_analyze(
        f"基于以下胰腺癌临床试验数据，生成本月概览分析（300字内）：\n\n{data_summary}\n\n"
        "重点：总体趋势、招募状态分布、阶段分布、与上月可能的对比方向。",
        config, use_llm,
    )
    print("✅")

    # 3.2 逐基因分析
    gene_sections: list[str] = []
    for gene in genes:
        trials = gene_data.get(gene["id"], [])
        gene_stats = compute_stats(trials)
        gene_summary = json.dumps({
            "gene": gene["name"],
            "trials": len(trials),
            "top_drugs": list(gene_stats["drug"].items())[:3],
            "top_biomarkers": list(gene_stats["biomarker"].items())[:3],
            "status": gene_stats["status"],
            "countries": list(gene_stats["country"].items())[:3],
        }, ensure_ascii=False)

        print(f"   [基因] {gene['name']} 分析 ...", end=" ", flush=True)
        llm_gene = llm_analyze(
            f"分析 {gene['name']}（{gene.get('cn_name','')}）靶点的胰腺癌临床试验现状（300字内）：\n\n"
            f"数据：{gene_summary}\n"
            f"基因说明：{gene.get('cn_desc','')}\n\n"
            "重点：本月新进展、关键药物、阶段分布、与同类靶点对比。",
            config, use_llm,
        )
        print("✅")

        gene_sections.append(format_gene_section(gene, trials, llm_gene))

    # 3.3 技术赛道分析
    tracks = [
        ("ras", "RAS 抑制剂赛道",
         "分析 RAS 抑制剂赛道进展（KRAS G12D/G12C/G12V 抑制剂、三复合物抑制剂、RMC-5127 等）"),
        ("adc", "ADC 药物赛道",
         "分析 ADC 药物赛道进展（TROP2/TF/Nectin-4/CEACAM5/CDH17/CLDN18.2 ADC）"),
        ("immune", "免疫治疗赛道",
         "分析免疫治疗进展（CAR-T/TCR-T/mRNA疫苗/ICI 在胰腺癌的进展）"),
        ("ddr", "DDR 靶向赛道",
         "分析 DDR 靶向赛道进展（PARP抑制剂、ATR抑制剂、ATM缺陷合成致死）"),
        ("protac", "PROTAC 降解剂赛道",
         "分析 PROTAC 降解剂在胰腺癌的进展（ARV-806 等 KRAS PROTAC）"),
        ("shp2", "SHP2 抑制剂赛道",
         "分析 SHP2 抑制剂赛道进展（联合 KRAS 抑制剂策略）"),
    ]

    llm_tracks: dict[str, str] = {}
    for track_id, track_name, prompt_hint in tracks:
        print(f"   [赛道] {track_name} ...", end=" ", flush=True)
        llm_tracks[track_id] = llm_analyze(
            f"{prompt_hint}（300字内）。基于本月试验数据：\n{data_summary}",
            config, use_llm,
        )
        print("✅")

    # 3.4 中国可及性 + 里程碑
    print("   [中国可及性] ...", end=" ", flush=True)
    china_trials = [t for t in all_trials if "China" in t.get("countries", [])]
    china_summary = json.dumps({
        "china_trials": len(china_trials),
        "china_genes": list(Counter(t.get("_gene_name", "") for t in china_trials).most_common(5)),
    }, ensure_ascii=False)
    llm_china = llm_analyze(
        f"分析胰腺癌临床试验的中国可及性（300字内）：\n{china_summary}\n"
        "重点：中国开展试验统计、国产药物进展（HRS-4642/GFH375/ABO2102等）、医保前景。",
        config, use_llm,
    )
    print("✅")

    print("   [里程碑] ...", end=" ", flush=True)
    llm_milestones = llm_analyze(
        f"列出本月胰腺癌临床试验的重要里程碑（300字内）：\n{data_summary}\n"
        "重点：3期发布、FDA/NMPA批准、关键数据读出、新药首次人体试验。",
        config, use_llm,
    )
    print("✅\n")

    # Step 4: 组装报告
    print("📝 Step 4: 组装最终报告 ...")
    report = assemble_report(
        template_path=_TEMPLATE_PATH,
        month_label=month_label,
        issue_num=1,
        start_date=start_date,
        end_date=end_date,
        gene_count=len(genes),
        trial_count=len(all_trials),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        overall_stats_table=stats_table,
        llm_overview=llm_overview,
        gene_sections="\n\n".join(gene_sections),
        llm_ras=llm_tracks["ras"],
        llm_adc=llm_tracks["adc"],
        llm_immune=llm_tracks["immune"],
        llm_ddr=llm_tracks["ddr"],
        llm_protac=llm_tracks["protac"],
        llm_shp2=llm_tracks["shp2"],
        trial_list_all=format_trial_list_all(all_trials),
        llm_china=llm_china,
        llm_milestones=llm_milestones,
        glossary=format_glossary(genes),
    )
    print("   ✅ 完成\n")

    # 写入文件
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    month_tag = datetime.now().strftime("%Y-%m")
    output_path = _REPORT_DIR / f"NCCN_月报_{month_tag}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 月报已生成: {output_path}")
    print(f"   字数: ~{len(report)} 字符")
    return report


def assemble_report(**kwargs) -> str:
    """读取模板并填充占位符。"""
    with open(kwargs["template_path"], encoding="utf-8") as f:
        template = f.read()

    for key, value in kwargs.items():
        if key == "template_path":
            continue
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, str(value))

    return template


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------
async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="NCCN 胰腺癌临床试验月报生成器")
    parser.add_argument("--gene", "-g", default=None, help="仅生成指定基因的报告（基因ID）")
    parser.add_argument("--no-llm", action="store_true", help="跳过 LLM 分析，输出骨架")
    parser.add_argument("--no-cache", action="store_true", help="忽略缓存，重新搜索")
    args = parser.parse_args()

    await generate_report(
        gene_filter=args.gene,
        use_llm=not args.no_llm,
    )


if __name__ == "__main__":
    asyncio.run(main())
