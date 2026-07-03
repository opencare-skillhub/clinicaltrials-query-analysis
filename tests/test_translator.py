#!/usr/bin/env python3
"""
翻译模块测试。

测试 translator 模块的边界情况和解析逻辑（不依赖真实 LLM 调用）。

运行: python3 tests/test_translator.py
"""

import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPT_DIR))

from translator import translate_fields, _parse_translate_response


def test_empty_input():
    """空输入返回空字典。"""
    assert translate_fields([], ["title"], "nct_id") == {}
    print("✅ test_empty_input 通过")


def test_use_llm_false():
    """use_llm=False 时返回空字典。"""
    items = [{"nct_id": "NCT123", "title": "test"}]
    result = translate_fields(items, ["title"], "nct_id", use_llm=False)
    assert result == {}, "use_llm=False 应返回空字典"
    print("✅ test_use_llm_false 通过")


def test_parse_response_plain_json():
    """解析纯 JSON 数组。"""
    content = json.dumps([
        {"nct_id": "NCT001", "title": "KRAS 抑制剂研究"},
        {"nct_id": "NCT002", "title": "ADC 药物试验"},
    ])
    result = _parse_translate_response(content, "nct_id", ["title"])
    assert len(result) == 2
    assert result["NCT001"]["title"] == "KRAS 抑制剂研究"
    assert result["NCT002"]["title"] == "ADC 药物试验"
    print("✅ test_parse_response_plain_json 通过")


def test_parse_response_markdown_block():
    """解析 markdown code block 包裹的 JSON。"""
    content = '```json\n[{"nct_id": "NCT003", "title": "免疫治疗"}]\n```'
    result = _parse_translate_response(content, "nct_id", ["title"])
    assert len(result) == 1
    assert result["NCT003"]["title"] == "免疫治疗"
    print("✅ test_parse_response_markdown_block 通过")


def test_parse_response_with_prefix():
    """解析带前缀文本的 JSON。"""
    content = '好的，翻译结果如下：\n[{"nct_id": "NCT004", "title": "PROTAC降解剂"}]'
    result = _parse_translate_response(content, "nct_id", ["title"])
    assert len(result) == 1
    assert result["NCT004"]["title"] == "PROTAC降解剂"
    print("✅ test_parse_response_with_prefix 通过")


def test_parse_response_multi_fields():
    """解析多个字段的翻译。"""
    content = json.dumps([
        {"nct_id": "NCT005", "title": "中文标题", "conditions": "胰腺癌"},
    ])
    result = _parse_translate_response(content, "nct_id", ["title", "conditions"])
    assert result["NCT005"]["title"] == "中文标题"
    assert result["NCT005"]["conditions"] == "胰腺癌"
    print("✅ test_parse_response_multi_fields 通过")


def test_parse_response_invalid():
    """无效 JSON 返回空字典。"""
    # 没有 JSON 数组
    assert _parse_translate_response("这不是JSON", "nct_id", ["title"]) == {}
    # 畸形 JSON
    assert _parse_translate_response("[invalid json]", "nct_id", ["title"]) == {}
    # 空字符串
    assert _parse_translate_response("", "nct_id", ["title"]) == {}
    print("✅ test_parse_response_invalid 通过")


def test_parse_response_empty_array():
    """空 JSON 数组返回空字典。"""
    assert _parse_translate_response("[]", "nct_id", ["title"]) == {}
    print("✅ test_parse_response_empty_array 通过")


def test_parse_response_skip_empty_key():
    """空 key_field 值的条目被跳过。"""
    content = json.dumps([
        {"nct_id": "", "title": "无ID的"},
        {"nct_id": "NCT006", "title": "有ID的"},
    ])
    result = _parse_translate_response(content, "nct_id", ["title"])
    assert len(result) == 1
    assert "NCT006" in result
    print("✅ test_parse_response_skip_empty_key 通过")


def test_custom_key_field():
    """自定义 key_field 字段名。"""
    content = json.dumps([
        {"drug_id": "DRG001", "name": "阿司匹林"},
    ])
    result = _parse_translate_response(content, "drug_id", ["name"])
    assert "DRG001" in result
    assert result["DRG001"]["name"] == "阿司匹林"
    print("✅ test_custom_key_field 通过")


def run_all():
    """运行所有测试。"""
    print("\n🧪 翻译模块测试\n" + "=" * 40)
    tests = [
        test_empty_input,
        test_use_llm_false,
        test_parse_response_plain_json,
        test_parse_response_markdown_block,
        test_parse_response_with_prefix,
        test_parse_response_multi_fields,
        test_parse_response_invalid,
        test_parse_response_empty_array,
        test_parse_response_skip_empty_key,
        test_custom_key_field,
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