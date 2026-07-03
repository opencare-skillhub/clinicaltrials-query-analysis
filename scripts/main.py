#!/usr/bin/env python3
"""
ClinicalTrials 搜索分析系统 — 交互式菜单入口。

提供三个核心功能：
  1. 单基因搜索      — 搜索指定基因的临床试验
  2. 多基因专题分析   — 批量搜索多个基因并对比
  3. NCCN 月报生成   — 生成本月胰腺癌临床月报
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加脚本目录到路径
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from config_loader import load_config, get_all_genes, get_report_genes, get_genes_by_category
from search import ClinicalTrialsSearch, print_trials_table, print_summary
from report_nccn import generate_report


def print_header() -> None:
    """打印系统标题。"""
    print()
    print("=" * 60)
    print("  🔬 ClinicalTrials 搜索分析系统")
    print("  胰腺癌临床情报工具")
    print("=" * 60)
    print()


def print_menu() -> None:
    """打印主菜单。"""
    print("请选择功能：")
    print()
    print("  1. 单基因搜索      — 搜索指定基因的临床试验")
    print("  2. 多基因专题分析   — 批量搜索多个基因并对比")
    print("  3. NCCN 月报生成   — 生成本月胰腺癌临床月报")
    print("  0. 退出")
    print()


def select_genes() -> list[dict]:
    """交互式选择基因。"""
    config = load_config()
    all_genes = get_all_genes(config)

    print("\n可用基因列表：")
    print()
    for i, gene in enumerate(all_genes, 1):
        report_mark = "📊" if gene.get("report") else "  "
        print(f"  {report_mark} {i:2d}. {gene['name']:<20s} [{gene['category']}] {gene.get('cn_name', '')}")

    print()
    print("  输入序号（逗号分隔，如 2,5,7）或输入基因名（如 kras,brca1）")
    print("  输入 'all' 选择全部, 'report' 选择月报默认基因")
    print("  输入 'q' 返回主菜单")
    print()

    choice = input("请选择: ").strip().lower()

    if choice == "q":
        return []
    if choice == "all":
        return all_genes
    if choice == "report":
        return get_report_genes(config)

    selected: list[dict] = []
    for part in choice.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        # 按序号
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(all_genes):
                selected.append(all_genes[idx])
        else:
            # 按基因名/ID
            for g in all_genes:
                if part in (g["id"], g["name"].lower(), g["name"]):
                    selected.append(g)
                    break

    return selected


# ---------------------------------------------------------------------------
# 功能1：单基因搜索
# ---------------------------------------------------------------------------
async def single_gene_search() -> None:
    """单基因搜索交互。"""
    genes = select_genes()
    if not genes:
        return

    gene = genes[0]
    print(f"\n🔍 已选择: {gene['name']}（{gene.get('cn_name', '')}）")
    print(f"   搜索词: {gene.get('search_terms', [])}")
    print()

    # 可选参数
    country = input("国家筛选（回车跳过，如 China）: ").strip() or None
    days_input = input("过去天数（回车=不限）: ").strip()
    max_input = input("最大结果数（回车=50）: ").strip()

    start_date = None
    if days_input.isdigit():
        days = int(days_input)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    max_results = int(max_input) if max_input.isdigit() else 50

    # 执行搜索
    print(f"\n⏳ 正在搜索 {gene['name']} ...\n")
    client = ClinicalTrialsSearch()
    try:
        all_trials = []
        seen_nct: set[str] = set()
        for term in gene.get("search_terms", [gene["name"]]):
            trials = await client.search(
                keyword=term,
                start_date=start_date,
                country=country,
                max_results=max_results,
            )
            for t in trials:
                if t["nct_id"] not in seen_nct:
                    all_trials.append(t)
                    seen_nct.add(t["nct_id"])
    finally:
        await client.aclose()

    # 输出
    print_trials_table(all_trials)
    print_summary(all_trials, gene["name"])

    input("\n按回车返回主菜单...")


# ---------------------------------------------------------------------------
# 功能2：多基因专题分析
# ---------------------------------------------------------------------------
async def multi_gene_analysis() -> None:
    """多基因批量搜索与对比。"""
    genes = select_genes()
    if not genes:
        return

    print(f"\n📊 已选择 {len(genes)} 个基因进行专题分析\n")

    country = input("国家筛选（回车跳过）: ").strip() or None
    max_results = 30

    print(f"\n⏳ 开始批量搜索 ...\n")

    results: dict[str, list] = {}
    client = ClinicalTrialsSearch()
    try:
        for i, gene in enumerate(genes, 1):
            print(f"  [{i}/{len(genes)}] {gene['name']} ...", end=" ", flush=True)
            all_trials = []
            seen_nct: set[str] = set()
            for term in gene.get("search_terms", [gene["name"]]):
                trials = await client.search(
                    keyword=term,
                    country=country,
                    max_results=max_results,
                )
                for t in trials:
                    if t["nct_id"] not in seen_nct:
                        all_trials.append(t)
                        seen_nct.add(t["nct_id"])
            results[gene["name"]] = all_trials
            print(f"{len(all_trials)} 项")
    finally:
        await client.aclose()

    # 对比分析
    print(f"\n{'='*80}")
    print(f"  📊 多基因专题分析报告")
    print(f"{'='*80}\n")

    print("| 基因 | 试验数 | 招募中 | 热门药物 | 热门国家 |")
    print("|------|--------|--------|---------|---------|")
    for gene_name, trials in results.items():
        total = len(trials)
        recruiting = sum(1 for t in trials if t.get("status") == "RECRUITING")
        from collections import Counter
        drugs = Counter(d for t in trials for d in t.get("drugs", []))
        countries = Counter(c for t in trials for c in t.get("countries", []))
        top_drug = drugs.most_common(1)[0][0] if drugs else "-"
        top_country = countries.most_common(1)[0][0] if countries else "-"
        print(f"| {gene_name} | {total} | {recruiting} | {top_drug} | {top_country} |")

    print()

    # 逐基因详情
    for gene_name, trials in results.items():
        print_trials_table(trials)
        print_summary(trials, gene_name)

    input("\n按回车返回主菜单...")


# ---------------------------------------------------------------------------
# 功能3：NCCN 月报
# ---------------------------------------------------------------------------
async def nccn_report() -> None:
    """生成月报。"""
    print("\n📋 NCCN 胰腺癌临床试验月报生成器\n")

    use_llm_input = input("是否启用 LLM 深度分析？(y/n, 默认y): ").strip().lower()
    use_llm = use_llm_input != "n"

    gene_filter = input("仅生成指定基因？(回车=全部月报基因, 或输入基因ID如 kras): ").strip() or None

    print()
    await generate_report(gene_filter=gene_filter, use_llm=use_llm)

    input("\n按回车返回主菜单...")


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------
async def main() -> None:
    """主循环。"""
    while True:
        print_header()
        print_menu()

        choice = input("请输入选项 [0-3]: ").strip()

        if choice == "0":
            print("\n👋 再见！\n")
            break
        elif choice == "1":
            await single_gene_search()
        elif choice == "2":
            await multi_gene_analysis()
        elif choice == "3":
            await nccn_report()
        else:
            print("\n⚠️ 无效选项，请重新输入。")
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 已退出。\n")
