#!/usr/bin/env python3
"""
配置加载器测试。

测试 config_loader 模块的主要功能：
  - load_config() 加载 genes.yaml
  - get_gene_by_id() 基因查找
  - get_report_genes() 月报基因列表
  - get_llm_config() LLM 配置解析

运行: python3 tests/test_config_loader.py
"""

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPT_DIR))

from config_loader import (
    load_config,
    get_gene_by_id,
    get_all_genes,
    get_report_genes,
    get_genes_by_category,
    get_llm_config,
)


def test_load_config():
    """配置文件能正常加载。"""
    config = load_config()
    assert config is not None, "配置不应为 None"
    assert "genes" in config, "配置应包含 genes 键"
    assert "llm" in config, "配置应包含 llm 键"
    assert len(config["genes"]) >= 20, f"基因数量应>=20，实际 {len(config['genes'])}"
    print("✅ test_load_config 通过")


def test_get_gene_by_id():
    """按 ID 查找基因。"""
    config = load_config()
    kras = get_gene_by_id("kras", config)
    assert kras is not None, "kras 基因应存在"
    assert kras["name"] == "KRAS", f"基因名应为 KRAS，实际 {kras['name']}"
    assert kras.get("cn_name"), "kras 应有中文名"

    not_found = get_gene_by_id("nonexistent_gene", config)
    assert not_found is None, "不存在的基因应返回 None"
    print("✅ test_get_gene_by_id 通过")


def test_get_report_genes():
    """月报默认基因列表。"""
    config = load_config()
    report_genes = get_report_genes(config)
    assert len(report_genes) >= 15, f"月报基因应>=15，实际 {len(report_genes)}"
    # 所有月报基因都应有 report: True
    for g in report_genes:
        assert g.get("report") is True, f"基因 {g['name']} 的 report 应为 True"
    print(f"✅ test_get_report_genes 通过 ({len(report_genes)} 个基因)")


def test_get_all_genes():
    """全部基因列表。"""
    config = load_config()
    all_genes = get_all_genes(config)
    assert len(all_genes) >= 20, f"全部基因应>=20，实际 {len(all_genes)}"
    # 每个基因都有必要字段
    for g in all_genes:
        assert "id" in g, "基因缺少 id 字段"
        assert "name" in g, "基因缺少 name 字段"
        assert "search_terms" in g, f"基因 {g['name']} 缺少 search_terms"
    print(f"✅ test_get_all_genes 通过 ({len(all_genes)} 个基因)")


def test_get_genes_by_category():
    """按分组获取基因。"""
    config = load_config()
    for category in ("guideline", "hotspot", "advanced", "supplementary"):
        genes = get_genes_by_category(category, config)
        # 至少 guideline 应有基因
        if category == "guideline":
            assert len(genes) > 0, "guideline 分组应至少有1个基因"
    print("✅ test_get_genes_by_category 通过")


def test_get_llm_config():
    """LLM 配置解析。"""
    config = load_config()
    llm_cfg = get_llm_config(config)
    assert "provider" in llm_cfg, "LLM 配置应包含 provider"
    assert "temperature" in llm_cfg, "LLM 配置应包含 temperature"
    assert "max_tokens" in llm_cfg, "LLM 配置应包含 max_tokens"
    # provider 应是已知值之一
    assert llm_cfg["provider"] in ("custom", "stepfun", "dashscope"), \
        f"provider 应为 custom/stepfun/dashscope，实际 {llm_cfg['provider']}"
    print(f"✅ test_get_llm_config 通过 (provider={llm_cfg['provider']}, model={llm_cfg['model']})")


def test_search_terms_not_empty():
    """每个基因的 search_terms 不为空。"""
    config = load_config()
    for g in get_all_genes(config):
        terms = g.get("search_terms", [])
        assert len(terms) > 0, f"基因 {g['name']} 的 search_terms 不应为空"
    print("✅ test_search_terms_not_empty 通过")


def run_all():
    """运行所有测试。"""
    print("\n🧪 配置加载器测试\n" + "=" * 40)
    tests = [
        test_load_config,
        test_get_gene_by_id,
        test_get_report_genes,
        test_get_all_genes,
        test_get_genes_by_category,
        test_get_llm_config,
        test_search_terms_not_empty,
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