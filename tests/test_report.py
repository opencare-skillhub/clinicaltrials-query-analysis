#!/usr/bin/env python3
"""
报告生成器测试。

测试 report_nccn 模块的格式化函数和统计函数（不依赖真实 API/LLM）。

运行: python3 tests/test_report.py
"""

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPT_DIR))

from report_nccn import (
    compute_stats,
    stats_to_table,
    format_gene_section,
    format_trial_list_all,
    format_glossary,
)


# 测试用的模拟试验数据
MOCK_TRIALS = [
    {
        "nct_id": "NCT00001",
        "title": "Study of Drug A in Pancreatic Cancer",
        "phase": "PHASE2",
        "status": "RECRUITING",
        "conditions": "Pancreatic Adenocarcinoma",
        "drugs": ["Drug A", "Drug B"],
        "interventions": "Drug A (DRUG); Drug B (DRUG)",
        "sponsor": "Test Sponsor",
        "start_date": "2026-06-01",
        "first_post_date": "2026-06-05",
        "primary_completion_date": "2027-06-01",
        "completion_date": "2027-12-01",
        "last_update": "2026-06-20",
        "countries": ["United States", "China"],
        "cities": ["Boston", "Shanghai"],
        "biomarker": "KRAS G12D",
        "url": "https://clinicaltrials.gov/study/NCT00001",
        "_gene_id": "kras",
        "_gene_name": "KRAS",
    },
    {
        "nct_id": "NCT00002",
        "title": "ADC Therapy Trial",
        "phase": "PHASE1",
        "status": "ACTIVE_NOT_RECRUITING",
        "conditions": "Pancreatic Cancer",
        "drugs": ["ADC Drug"],
        "interventions": "ADC Drug (DRUG)",
        "sponsor": "Another Sponsor",
        "start_date": "2026-05-01",
        "first_post_date": "2026-05-10",
        "primary_completion_date": "",
        "completion_date": "",
        "last_update": "2026-06-15",
        "countries": ["Japan"],
        "cities": ["Tokyo"],
        "biomarker": "HER2+",
        "url": "https://clinicaltrials.gov/study/NCT00002",
        "_gene_id": "erbb2",
        "_gene_name": "HER2 (ERBB2)",
    },
]

MOCK_GENE = {
    "id": "kras",
    "name": "KRAS",
    "category": "guideline",
    "cn_name": "KRAS 癌基因",
    "cn_desc": "胰腺癌最常见的驱动突变（>90%）",
    "search_terms": ["KRAS G12D", "KRAS pancreatic"],
}


def test_compute_stats():
    """统计函数计算正确。"""
    stats = compute_stats(MOCK_TRIALS)
    assert stats["total"] == 2
    assert stats["status"].get("RECRUITING") == 1
    assert stats["status"].get("ACTIVE_NOT_RECRUITING") == 1
    assert "Drug A" in stats["drug"]
    assert "United States" in stats["country"]
    assert "China" in stats["country"]
    print("✅ test_compute_stats 通过")


def test_compute_stats_empty():
    """空列表统计返回零值。"""
    stats = compute_stats([])
    assert stats["total"] == 0
    assert stats["status"] == {}
    print("✅ test_compute_stats_empty 通过")


def test_stats_to_table():
    """统计表格生成。"""
    stats = compute_stats(MOCK_TRIALS)
    table = stats_to_table(stats)
    assert "试验总数" in table
    assert "招募状态" in table
    assert "临床阶段" in table
    # 应包含表格格式
    assert "|" in table
    print("✅ test_stats_to_table 通过")


def test_format_gene_section_with_trials():
    """基因专区格式化（有试验）。"""
    section = format_gene_section(MOCK_GENE, MOCK_TRIALS, "LLM分析占位内容")
    assert "KRAS" in section
    assert "KRAS 癌基因" in section
    assert "NCT00001" in section
    assert "NCT00002" in section
    assert "深度分析" in section
    assert "LLM分析占位内容" in section
    # 包含日期字段
    assert "📅发布" in section or "发布" in section
    print("✅ test_format_gene_section_with_trials 通过")


def test_format_gene_section_empty():
    """基因专区格式化（无试验）。"""
    section = format_gene_section(MOCK_GENE, [], "")
    assert "KRAS" in section
    assert "未检索到" in section
    print("✅ test_format_gene_section_empty 通过")


def test_format_gene_section_with_translation():
    """基因专区带翻译时显示双语标题。"""
    translations = {
        "NCT00001": {"title": "药物A治疗胰腺癌研究"},
        "NCT00002": {"title": "ADC疗法试验"},
    }
    section = format_gene_section(MOCK_GENE, MOCK_TRIALS, "", translations)
    assert "药物A治疗胰腺癌研究" in section
    assert "ADC疗法试验" in section
    # 原英文也在
    assert "Study of Drug A" in section
    print("✅ test_format_gene_section_with_translation 通过")


def test_format_trial_list_all():
    """合并试验清单。"""
    content = format_trial_list_all(MOCK_TRIALS)
    assert "KRAS" in content
    assert "HER2" in content
    assert "NCT00001" in content
    # 按基因分组
    assert "KRAS" in content
    print("✅ test_format_trial_list_all 通过")


def test_format_trial_list_all_empty():
    """空列表返回提示。"""
    content = format_trial_list_all([])
    assert "无匹配" in content
    print("✅ test_format_trial_list_all_empty 通过")


def test_format_trial_list_all_with_dates():
    """合并清单包含日期字段。"""
    content = format_trial_list_all(MOCK_TRIALS)
    assert "2026-06-05" in content  # first_post_date
    assert "2026-06-20" in content  # last_update
    print("✅ test_format_trial_list_all_with_dates 通过")


def test_format_glossary():
    """术语表生成。"""
    genes = [MOCK_GENE]
    glossary = format_glossary(genes)
    assert "KRAS" in glossary
    assert "KRAS 癌基因" in glossary
    assert "ADC" in glossary  # 通用术语
    assert "PROTAC" in glossary
    assert "PARP" in glossary
    print("✅ test_format_glossary 通过")


def run_all():
    """运行所有测试。"""
    print("\n🧪 报告生成器测试\n" + "=" * 40)
    tests = [
        test_compute_stats,
        test_compute_stats_empty,
        test_stats_to_table,
        test_format_gene_section_with_trials,
        test_format_gene_section_empty,
        test_format_gene_section_with_translation,
        test_format_trial_list_all,
        test_format_trial_list_all_empty,
        test_format_trial_list_all_with_dates,
        test_format_glossary,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 失败: {e}")
            failed += 1
    print(f"\n{'=' * 40}")
    print(f"结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)