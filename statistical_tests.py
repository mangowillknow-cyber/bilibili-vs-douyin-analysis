"""
统计假设检验模块。

3个假设检验：
1. H1: 抖音爆款视频的平均时长显著短于B站爆款视频（双样本T检验）
2. H2: 两个平台的爆款分类分布存在显著差异（卡方检验）
3. H3: B站爆款的评论互动率显著高于抖音爆款（双样本T检验）
"""
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROCESSED_DIR


def load_data():
    """加载两个平台的清洗数据"""
    bilibili_path = os.path.join(PROCESSED_DIR, "bilibili_clean.csv")
    douyin_path = os.path.join(PROCESSED_DIR, "douyin_clean.csv")

    if not os.path.exists(bilibili_path) or not os.path.exists(douyin_path):
        print("  请先运行 data_cleaner.py")
        return None, None

    return pd.read_csv(bilibili_path), pd.read_csv(douyin_path)


def test_h1_duration(bilibili_df, douyin_df):
    """
    假设1：抖音爆款视频的平均时长显著短于B站爆款视频

    检验方法：独立双样本T检验（或Mann-Whitney U检验）
    """
    print("\n" + "=" * 60)
    print("假设1：抖音爆款平均时长 < B站爆款平均时长")
    print("=" * 60)

    if 'duration' not in bilibili_df.columns or 'duration' not in douyin_df.columns:
        print("  缺少时长数据，跳过检验")
        return

    # 检查时长数据是否可用
    bili_has_duration = not bilibili_df['duration'].isna().all()
    douyin_has_duration = not douyin_df['duration'].isna().all()
    if not bili_has_duration or not douyin_has_duration:
        print("  时长数据全为NaN（两个数据集均无时长字段），跳过检验")
        return

    # 获取爆款视频（Top 5%播放量）
    bili_threshold = bilibili_df['view_count'].quantile(0.95) if 'view_count' in bilibili_df.columns else 0
    douyin_threshold = douyin_df['view_count'].quantile(0.95) if 'view_count' in douyin_df.columns else 0

    bili_viral_duration = bilibili_df[bilibili_df['view_count'] >= bili_threshold]['duration']
    douyin_viral_duration = douyin_df[douyin_df['view_count'] >= douyin_threshold]['duration']

    # 移除缺失值
    bili_viral_duration = bili_viral_duration.dropna()
    douyin_viral_duration = douyin_viral_duration.dropna()

    if len(bili_viral_duration) < 5 or len(douyin_viral_duration) < 5:
        print("  样本量不足，跳过检验")
        return

    # 基本统计
    print(f"\n  B站爆款样本量：{len(bili_viral_duration)}")
    print(f"  抖音爆款样本量：{len(douyin_viral_duration)}")
    print(f"  B站爆款平均时长：{bili_viral_duration.mean():.1f} 秒")
    print(f"  抖音爆款平均时长：{douyin_viral_duration.mean():.1f} 秒")
    print(f"  时长差异：{bili_viral_duration.mean() - douyin_viral_duration.mean():.1f} 秒")

    # 检验方差齐性（Levene检验）
    lev_stat, lev_p = stats.levene(bili_viral_duration, douyin_viral_duration)
    print(f"\n  Levene方差齐性检验：统计量={lev_stat:.4f}, P值={lev_p:.4f}")
    equal_var = lev_p > 0.05

    # 独立双样本T检验
    t_stat, t_p = stats.ttest_ind(
        bili_viral_duration, douyin_viral_duration,
        equal_var=equal_var, alternative='greater'
    )

    print(f"\n  独立双样本T检验结果：")
    print(f"    T统计量：{t_stat:.4f}")
    print(f"    P值：{t_p:.6f}")
    print(f"    显著性水平 α=0.05")

    # 95%置信区间
    diff_mean = bili_viral_duration.mean() - douyin_viral_duration.mean()
    se = np.sqrt(bili_viral_duration.var()/len(bili_viral_duration) +
                 douyin_viral_duration.var()/len(douyin_viral_duration))
    ci_lower = diff_mean - 1.96 * se
    ci_upper = diff_mean + 1.96 * se

    print(f"    均值差95%置信区间：[{ci_lower:.1f}, {ci_upper:.1f}] 秒")

    # 结论
    if t_p < 0.05:
        print(f"\n  结论：拒绝原假设，抖音爆款平均时长显著短于B站爆款")
        print(f"    （P值={t_p:.6f} < 0.05）")
    else:
        print(f"\n  结论：无法拒绝原假设，差异不显著")
        print(f"    （P值={t_p:.6f} >= 0.05）")


def test_h2_category(bilibili_df, douyin_df):
    """
    假设2：两个平台的爆款分类分布存在显著差异

    检验方法：卡方检验
    """
    print("\n" + "=" * 60)
    print("假设2：两个平台爆款分类分布存在显著差异")
    print("=" * 60)

    if 'category' not in bilibili_df.columns or 'category' not in douyin_df.columns:
        print("  缺少分类数据，跳过检验")
        return

    # 获取爆款视频
    bili_threshold = bilibili_df['view_count'].quantile(0.95) if 'view_count' in bilibili_df.columns else 0
    douyin_threshold = douyin_df['view_count'].quantile(0.95) if 'view_count' in douyin_df.columns else 0

    bili_viral = bilibili_df[bilibili_df['view_count'] >= bili_threshold]
    douyin_viral = douyin_df[douyin_df['view_count'] >= douyin_threshold]

    # 取共同分类
    bili_categories = bili_viral['category'].value_counts()
    douyin_categories = douyin_viral['category'].value_counts()

    common_cats = list(set(bili_categories.index) & set(douyin_categories.index))

    if len(common_cats) < 3:
        print("  共同分类不足3个，跳过卡方检验")
        return

    # 构建列联表
    contingency = pd.DataFrame({
        'B站': bili_categories[common_cats],
        '抖音': douyin_categories[common_cats]
    }).fillna(0)

    print(f"\n  共同分类数：{len(common_cats)}")
    print(f"  B站爆款样本量：{len(bili_viral)}")
    print(f"  抖音爆款样本量：{len(douyin_viral)}")

    # 卡方检验
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency.T)

    print(f"\n  卡方检验结果：")
    print(f"    卡方统计量：{chi2:.4f}")
    print(f"    自由度：{dof}")
    print(f"    P值：{p_value:.6f}")
    print(f"    显著性水平 α=0.05")

    if p_value < 0.05:
        print(f"\n  结论：拒绝原假设，两个平台的爆款分类分布存在显著差异")
        print(f"    （P值={p_value:.6f} < 0.05）")
    else:
        print(f"\n  结论：无法拒绝原假设，差异不显著")
        print(f"    （P值={p_value:.6f} >= 0.05）")


def test_h3_comment_rate(bilibili_df, douyin_df):
    """
    假设3：B站爆款的评论互动率显著高于抖音爆款

    检验方法：独立双样本T检验
    """
    print("\n" + "=" * 60)
    print("假设3：B站爆款评论互动率 > 抖音爆款评论互动率")
    print("=" * 60)

    required_cols = ['comment_count', 'view_count']
    for col in required_cols:
        if col not in bilibili_df.columns or col not in douyin_df.columns:
            print(f"  缺少 {col} 数据，跳过检验")
            return

    # 获取爆款视频
    bili_threshold = bilibili_df['view_count'].quantile(0.95)
    douyin_threshold = douyin_df['view_count'].quantile(0.95)

    bili_viral = bilibili_df[bilibili_df['view_count'] >= bili_threshold]
    douyin_viral = douyin_df[douyin_df['view_count'] >= douyin_threshold]

    # 计算评论率
    bili_comment_rate = (bili_viral['comment_count'] / bili_viral['view_count'].replace(0, np.nan)).dropna()
    douyin_comment_rate = (douyin_viral['comment_count'] / douyin_viral['view_count'].replace(0, np.nan)).dropna()

    if len(bili_comment_rate) < 5 or len(douyin_comment_rate) < 5:
        print("  样本量不足，跳过检验")
        return

    print(f"\n  B站爆款样本量：{len(bili_comment_rate)}")
    print(f"  抖音爆款样本量：{len(douyin_comment_rate)}")
    print(f"  B站爆款平均评论率：{bili_comment_rate.mean()*100:.2f}%")
    print(f"  抖音爆款平均评论率：{douyin_comment_rate.mean()*100:.2f}%")

    # 方差齐性检验
    lev_stat, lev_p = stats.levene(bili_comment_rate, douyin_comment_rate)
    equal_var = lev_p > 0.05

    # T检验
    t_stat, t_p = stats.ttest_ind(
        bili_comment_rate, douyin_comment_rate,
        equal_var=equal_var, alternative='greater'
    )

    print(f"\n  T检验结果：")
    print(f"    T统计量：{t_stat:.4f}")
    print(f"    P值：{t_p:.6f}")

    if t_p < 0.05:
        print(f"\n  结论：B站爆款评论互动率显著高于抖音爆款")
    else:
        print(f"\n  结论：差异不显著")


def main():
    """主函数：执行所有统计检验"""
    bilibili_df, douyin_df = load_data()
    if bilibili_df is None or douyin_df is None:
        return

    test_h1_duration(bilibili_df, douyin_df)
    test_h2_category(bilibili_df, douyin_df)
    test_h3_comment_rate(bilibili_df, douyin_df)

    print("\n" + "=" * 60)
    print("统计检验完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
