"""
一键运行全流程脚本。

执行顺序：
1. 数据获取
2. 数据清洗
3. B站EDA
4. 抖音EDA
5. 单平台爆款分析
6. 跨平台对比分析
7. 统计检验
"""
import os
import sys
import time

# Windows控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_step(step_name, module_name):
    """运行单个步骤"""
    print(f"\n{'=' * 60}")
    print(f"步骤：{step_name}")
    print(f"{'=' * 60}")

    start_time = time.time()

    try:
        # 动态导入模块
        module = __import__(module_name)
        module.main()

        elapsed = time.time() - start_time
        print(f"\n  {step_name} 完成（耗时 {elapsed:.1f} 秒）")
        return True
    except Exception as e:
        print(f"\n  {step_name} 失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数：按顺序执行所有步骤"""
    print("=" * 60)
    print("B站 vs 抖音 爆款特征对比分析 - 全流程运行")
    print("=" * 60)

    start_time = time.time()

    steps = [
        ("数据获取", "data_fetcher"),
        ("数据清洗", "data_cleaner"),
        ("B站EDA", "eda_bilibili"),
        ("抖音EDA", "eda_douyin"),
        ("单平台爆款分析", "爆款对比分析_单平台"),
        ("跨平台对比分析", "跨平台对比分析"),
        ("统计检验", "statistical_tests"),
    ]

    results = []
    for step_name, module_name in steps:
        success = run_step(step_name, module_name)
        results.append((step_name, success))

        if not success:
            print(f"\n  {step_name} 失败，后续步骤可能受影响")
            # 数据清洗是后续所有分析的前提，失败则终止
            if module_name == "data_cleaner":
                print("  数据清洗失败，终止后续步骤")
                for remaining_name, remaining_module in steps[len(results):]:
                    results.append((remaining_name, False))
                break

    # 输出总结
    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("执行总结")
    print("=" * 60)

    for step_name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {step_name}")

    print(f"\n总耗时：{total_time:.1f} 秒")

    success_count = sum(1 for _, success in results if success)
    print(f"成功：{success_count}/{len(results)} 步骤")

    print("\n输出文件：")
    print("  figures/bilibili/    - B站图表")
    print("  figures/douyin/      - 抖音图表")
    print("  figures/comparison/  - 跨平台对比图表")


if __name__ == "__main__":
    main()
