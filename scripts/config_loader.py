"""
基因配置文件加载器。

从 config/genes.yaml 加载基因定义，提供查询接口。
无 PyYAML 时回退到内置默认配置。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# 配置文件路径
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "genes.yaml"


def load_config() -> dict[str, Any]:
    """
    加载 genes.yaml 配置文件。

    Returns
    -------
    dict
        配置字典，包含 report_defaults, report_window, llm, genes 等键。
        如果 YAML 不可用或文件不存在，返回内置默认配置。
    """
    if not _HAS_YAML or not _CONFIG_PATH.exists():
        return _get_default_config()

    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_gene_by_id(gene_id: str, config: dict | None = None) -> dict[str, Any] | None:
    """根据基因 ID 查找基因定义。"""
    if config is None:
        config = load_config()
    for gene in config.get("genes", []):
        if gene["id"] == gene_id:
            return gene
    return None


def get_report_genes(config: dict | None = None) -> list[dict[str, Any]]:
    """获取月报默认基因列表（report: true 的基因）。"""
    if config is None:
        config = load_config()
    return [g for g in config.get("genes", []) if g.get("report", False)]


def get_all_genes(config: dict | None = None) -> list[dict[str, Any]]:
    """获取全部基因定义。"""
    if config is None:
        config = load_config()
    return config.get("genes", [])


def get_genes_by_category(category: str, config: dict | None = None) -> list[dict[str, Any]]:
    """按分组获取基因列表（guideline/hotspot/advanced/supplementary）。"""
    if config is None:
        config = load_config()
    return [g for g in config.get("genes", []) if g.get("category") == category]


def get_llm_config(config: dict | None = None) -> dict[str, Any]:
    """
    获取 LLM 配置，根据 provider 从环境变量解析实际值。

    支持三种 provider: custom / stepfun / dashscope

    Returns
    -------
    dict with keys: provider, api_key, base_url, model, temperature, max_tokens
    """
    if config is None:
        config = load_config()
    llm_cfg = config.get("llm", {})
    provider = llm_cfg.get("provider", "custom")
    providers = llm_cfg.get("providers", {})

    # 如果 provider 配置不存在，回退到旧的扁平配置
    if provider not in providers:
        return {
            "provider": "custom",
            "api_key": os.environ.get(llm_cfg.get("api_key_env", "LLM_API_KEY"), ""),
            "base_url": os.environ.get(llm_cfg.get("base_url_env", "LLM_BASE_URL"), ""),
            "model": os.environ.get(
                llm_cfg.get("model_env", "LLM_MODEL"),
                llm_cfg.get("model_default", "glm-4-flash"),
            ),
            "temperature": llm_cfg.get("temperature", 0.4),
            "max_tokens": llm_cfg.get("max_tokens", 2000),
        }

    prov_cfg = providers[provider]
    # base_url 优先级: base_url_env(环境变量) > base_url_default(配置默认值) > base_url(固定值)
    base_url_env = prov_cfg.get("base_url_env", "")
    base_url = os.environ.get(base_url_env, "") if base_url_env else ""
    if not base_url:
        base_url = prov_cfg.get("base_url_default", "") or prov_cfg.get("base_url", "")
    # model: 环境变量 > 默认值
    model = os.environ.get(
        prov_cfg.get("model_env", ""),
        prov_cfg.get("model_default", ""),
    )

    return {
        "provider": provider,
        "api_key": os.environ.get(prov_cfg.get("api_key_env", ""), ""),
        "base_url": base_url,
        "model": model,
        "temperature": llm_cfg.get("temperature", 0.4),
        "max_tokens": llm_cfg.get("max_tokens", 2000),
    }


def load_biomarker_patterns(config: dict | None = None) -> list[tuple[str, str]]:
    """
    从基因配置加载 biomarker 匹配模式，用于替换 search.py 中的硬编码列表。

    Returns
    -------
    list[tuple[str, str]]
        (search_keyword, display_label) 对，按特异性排序。
    """
    if config is None:
        config = load_config()

    patterns: list[tuple[str, str]] = []
    seen_labels: set[str] = set()

    for gene in config.get("genes", []):
        name = gene["name"]
        label = gene.get("cn_name") or name
        # 添加别名（更具体的先放）
        for alias in gene.get("aliases", []):
            alias_upper = alias.upper()
            if alias_upper not in seen_labels:
                patterns.append((alias_upper, name))
                seen_labels.add(alias_upper)
        # 添加主名
        name_upper = name.upper()
        if name_upper not in seen_labels:
            patterns.append((name_upper, name))
            seen_labels.add(name_upper)

    return patterns


def _get_default_config() -> dict[str, Any]:
    """内置默认配置（YAML 不可用时的回退）。"""
    return {
        "report_defaults": ["kras", "claudin18_2", "erbb2", "brca1", "brca2"],
        "report_window": "30d",
        "llm": {
            "api_key_env": "LLM_API_KEY",
            "base_url_env": "LLM_BASE_URL",
            "model_env": "LLM_MODEL",
            "model_default": "glm-4-flash",
            "temperature": 0.4,
        },
        "genes": [
            {
                "id": "kras",
                "name": "KRAS",
                "category": "guideline",
                "aliases": ["KRAS G12D", "KRAS G12V", "KRAS G12C", "KRAS"],
                "search_terms": ["KRAS G12D", "KRAS G12V", "KRAS G12C", "KRAS pancreatic"],
                "nccn_section": "靶点治疗",
                "report": True,
                "cn_name": "KRAS 癌基因",
                "cn_desc": "胰腺癌最常见的驱动突变（>90%）",
            },
        ],
    }
