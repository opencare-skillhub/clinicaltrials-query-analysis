#!/usr/bin/env python3
"""
搜索模块测试。

测试 search 模块的解析和统计函数（不依赖真实 API 调用）。

运行: python3 tests/test_search.py
"""

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPT_DIR))

from search import ClinicalTrialsSearch, _BIOMARKER_PATTERNS


def test_biomarker_patterns_not_empty():
    """Biomarker 模式表不为空。"""
    assert len(_BIOMARKER_PATTERNS) > 20, \
        f"Biomarker 模式应>20，实际 {len(_BIOMARKER_PATTERNS)}"
    print(f"✅ test_biomarker_patterns_not_empty 通过 ({len(_BIOMARKER_PATTERNS)} 个模式)")


def test_extract_biomarker_kras():
    """提取 KRAS 突变 biomarker。"""
    eligibility = "Patients with KRAS G12D mutation"
    bm = ClinicalTrialsSearch._extract_biomarker(eligibility, "")
    assert "KRAS G12D" in bm, f"应提取 KRAS G12D，实际: {bm}"
    print(f"✅ test_extract_biomarker_kras 通过 ({bm})")


def test_extract_biomarker_brca():
    """提取 BRCA biomarker。"""
    eligibility = "Eligibility: BRCA1 or BRCA2 mutation carriers"
    bm = ClinicalTrialsSearch._extract_biomarker(eligibility, "")
    assert "BRCA1" in bm or "BRCA2" in bm or "BRCA1/2" in bm, \
        f"应提取 BRCA，实际: {bm}"
    print(f"✅ test_extract_biomarker_brca 通过 ({bm})")


def test_extract_biomarker_from_conditions():
    """从适应症中提取 biomarker。"""
    conditions = "Pancreatic Cancer with HER2 overexpression"
    bm = ClinicalTrialsSearch._extract_biomarker("", conditions)
    assert "HER2+" in bm, f"应提取 HER2+，实际: {bm}"
    print(f"✅ test_extract_biomarker_from_conditions 通过 ({bm})")


def test_extract_biomarker_empty():
    """无匹配 biomarker 返回空字符串。"""
    eligibility = "Patients with hypertension"
    bm = ClinicalTrialsSearch._extract_biomarker(eligibility, "Diabetes")
    assert bm == "", f"无匹配应返回空，实际: {bm}"
    print("✅ test_extract_biomarker_empty 通过")


def test_extract_biomarker_msih():
    """提取 MSI-H。"""
    eligibility = "Microsatellite Instability-High tumors"
    bm = ClinicalTrialsSearch._extract_biomarker(eligibility, "")
    assert "MSI-H/dMMR" in bm, f"应提取 MSI-H/dMMR，实际: {bm}"
    print(f"✅ test_extract_biomarker_msih 通过 ({bm})")


def test_extract_biomarker_specific_before_generic():
    """更具体的 biomarker 优先匹配（KRAS G12D 优先于泛 KRAS）。"""
    eligibility = "KRAS G12D mutated pancreatic cancer"
    bm = ClinicalTrialsSearch._extract_biomarker(eligibility, "")
    # 应包含 G12D 而非泛 KRAS
    assert "KRAS G12D" in bm, f"应包含 KRAS G12D，实际: {bm}"
    print(f"✅ test_extract_biomarker_specific_before_generic 通过 ({bm})")


def test_parse_study_minimal():
    """解析最小化试验数据。"""
    search = ClinicalTrialsSearch()
    minimal_study = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT99999",
                "briefTitle": "Test Trial",
                "phase": ["PHASE1"],
                "conditions": ["Test Condition"],
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
            },
            "armsInterventionsModule": {
                "interventions": [],
            },
            "eligibilityModule": {},
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "TestSponsor"},
            },
            "contactsLocationsModule": {
                "locations": [{"country": "United States", "city": "Boston"}],
            },
        }
    }
    parsed = search._parse_study(minimal_study)
    assert parsed is not None, "解析结果不应为 None"
    assert parsed["nct_id"] == "NCT99999"
    assert parsed["title"] == "Test Trial"
    assert parsed["status"] == "RECRUITING"
    assert parsed["phase"] == "PHASE1"
    assert "United States" in parsed["countries"]
    assert parsed["url"] == "https://clinicaltrials.gov/study/NCT99999"
    print("✅ test_parse_study_minimal 通过")


def test_parse_study_no_nct():
    """无 NCT ID 返回 None。"""
    search = ClinicalTrialsSearch()
    study = {"protocolSection": {"identificationModule": {}}}
    parsed = search._parse_study(study)
    assert parsed is None, "无 NCT ID 应返回 None"
    print("✅ test_parse_study_no_nct 通过")


def test_parse_study_with_dates():
    """解析包包含日期字段。"""
    search = ClinicalTrialsSearch()
    study = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT88888",
                "briefTitle": "Date Test",
            },
            "statusModule": {
                "overallStatus": "COMPLETED",
                "startDateStruct": {"date": "2025-01-01"},
                "studyFirstPostDateStruct": {"date": "2025-01-10"},
                "primaryCompletionDateStruct": {"date": "2026-01-01"},
                "completionDateStruct": {"date": "2026-06-01"},
                "lastUpdatePostDateStruct": {"date": "2025-06-15"},
            },
            "armsInterventionsModule": {"interventions": []},
            "eligibilityModule": {},
            "sponsorCollaboratorsModule": {},
            "contactsLocationsModule": {},
        }
    }
    parsed = search._parse_study(study)
    assert parsed["start_date"] == "2025-01-01"
    assert parsed["first_post_date"] == "2025-01-10"
    assert parsed["primary_completion_date"] == "2026-01-01"
    assert parsed["completion_date"] == "2026-06-01"
    assert parsed["last_update"] == "2025-06-15"
    print("✅ test_parse_study_with_dates 通过")


def run_all():
    """运行所有测试。"""
    print("\n🧪 搜索模块测试\n" + "=" * 40)
    tests = [
        test_biomarker_patterns_not_empty,
        test_extract_biomarker_kras,
        test_extract_biomarker_brca,
        test_extract_biomarker_from_conditions,
        test_extract_biomarker_empty,
        test_extract_biomarker_msih,
        test_extract_biomarker_specific_before_generic,
        test_parse_study_minimal,
        test_parse_study_no_nct,
        test_parse_study_with_dates,
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