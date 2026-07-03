#!/usr/bin/env python3
"""
测试统一入口 — 运行所有测试模块。

用法:
  python3 tests/run_all_tests.py           # 运行全部
  python3 tests/run_all_tests.py config     # 仅配置
  python3 tests/run_all_tests.py translator # 仅翻译
  python3 tests/run_all_tests.py report     # 仅报告
  python3 tests/run_all_tests.py search     # 仅搜索
"""

import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent

_MODULES = {
    "config": "test_config_loader.py",
    "translator": "test_translator.py",
    "report": "test_report.py",
    "search": "test_search.py",
}


def run_module(module_name: str, script: str) -> bool:
    """运行单个测试模块。"""
    print(f"\n{'=' * 60}")
    print(f"  🔬 运行: {module_name}")
    print(f"{'=' * 60}")
    result = subprocess.run(
        [sys.executable, str(_TESTS_DIR / script)],
        capture_output=False,
    )
    return result.returncode == 0


def main() -> None:
    args = sys.argv[1:] if len(sys.argv) > 1 else list(_MODULES.keys())

    print("\n🧪 ClinicalTrials Search — 测试套件")
    print(f"   测试目录: {_TESTS_DIR}")

    total = 0
    passed = 0
    failed = 0

    for arg in args:
        if arg not in _MODULES:
            print(f"⚠️ 未知测试模块: {arg}")
            print(f"   可用: {', '.join(_MODULES.keys())}")
            continue
        total += 1
        success = run_module(arg, _MODULES[arg])
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  📊 总结: {passed}/{total} 模块通过")
    if failed > 0:
        print(f"  ❌ {failed} 个模块失败")
        sys.exit(1)
    else:
        print("  ✅ 全部通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()