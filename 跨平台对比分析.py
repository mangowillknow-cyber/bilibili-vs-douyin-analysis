"""
跨平台对比分析模块（项目核心）。

5大对比维度：
1. 爆款率与内容生态对比
2. 爆款时长分布对比
3. 爆款互动模式对比
4. 爆款生命周期对比
5. 头部效应对比
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    PROCESSED_DIR, COMPARISON_FIGURES,
    COLOR_BILIBILI, COLOR_DOUYIN, FIGURE_DPI
)

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# B站 -> TikTok 分类中英文映射表
CATEGORY_MAP_BILIBILI_TO_EN = {
    '游戏': 'Gaming', '游戏区': 'Gaming',
    '音乐': 'Music', '音乐区': 'Music',
    '舞蹈': 'Dance', '舞蹈区': 'Dance',
    '运动': 'Fitness', '运动区': 'Fitness',
    '生活': 'Lifestyle', '生活区': 'Lifestyle',
    '美食': 'Food', '美食区': 'Food',
    '时尚': 'Fashion', '时尚区': 'Fashion',
    '娱乐': 'Entertainment', '娱乐区': 'Entertainment',
    '科技': 'Tech', '科技区': 'Tech',
    '知识': 'Education', '知识区': 'Education',
    '影视': 'Entertainment', '影视区': 'Entertainment',
    '动画': 'Animation', '番剧': 'Animation', '国创': 'Animation',
    '鬼畜': 'Comedy', '鬼畜区': 'Comedy',
    '汽车': 'Automotive', '汽车区': 'Automotive',
    '动物圈': 'Pets', '动物': 'Pets',
    '纪录片': 'Documentary', '电影': 'Film', '电视剧': 'TV',
    '新闻': 'News',
}


def load_both_platforms():
    """加载两个平台的清洗数据"""
    bilibili_path = os.path.join(PROCESSED_DIR, "bilibili_clean.csv")
    douyin_path = os.path.join(PROCESSED_DIR, "douyin_clean.csv")

    if not os.path.exists(bilibili_path) or not os.path.exists(douyin_path):
        print("  请先运行 data_cleaner.py 生成清洗数据")
        return None, None

    bilibili_df = pd.read_csv(bilibili_path)
    douyin_df = pd.read_csv(douyin_path)

    return bilibili_df, douyin_df


def compare_category_viral_rate(bilibili_df, douyin_df):
    """
    对比1：各分类爆款率对比
    """
    print("\n" + "=" * 60)
    print("对比1：爆款率与内容生态对比")
    print("=" * 60)

    # 计算各平台各分类的爆款率
    def calc_viral_rate(df, platform_name):
        # 如果没有爆款标记，临时计算Top 5%
        if 'view_count' in df.columns:
            threshold = df['view_count'].quantile(0.95)
            df = df.copy()
            df['viral_temp'] = (df['view_count'] >= threshold).astype(int)
            viral_col = 'viral_temp'
        else:
            return pd.DataFrame()

        stats = df.groupby('category').agg(
            total=('title', 'count'),
            viral=(viral_col, 'sum')
        ).reset_index()
        stats['viral_rate'] = stats['viral'] / stats['total'] * 100
        stats['platform'] = platform_name
        return stats

    bili_stats = calc_viral_rate(bilibili_df, 'B站')
    douyin_stats = calc_viral_rate(douyin_df, '抖音')

    # 尝试用映射表统一分类名（B站中文 -> 英文）
    bili_stats['category_en'] = bili_stats['category'].map(
        lambda x: CATEGORY_MAP_BILIBILI_TO_EN.get(x, x)
    )

    # 合并共同分类（先试原始名，再试映射后名称）
    common_categories = set(bili_stats['category']) & set(douyin_stats['category'])
    if not common_categories:
        common_categories = set(bili_stats['category_en']) & set(douyin_stats['category'])

    if not common_categories:
        print("  分类映射后仍无共同分类，分别展示各自Top 10")
        # 分别展示
        bili_top = bili_stats.nlargest(10, 'viral_rate')
        douyin_top = douyin_stats.nlargest(10, 'viral_rate')

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        axes[0].barh(range(len(bili_top)), bili_top['viral_rate'].values,
                     color=COLOR_BILIBILI, alpha=0.7)
        axes[0].set_yticks(range(len(bili_top)))
        axes[0].set_yticklabels(bili_top['category'].values)
        axes[0].set_title('B站 各分类爆款率 Top 10', fontsize=11)
        axes[0].set_xlabel('爆款率（%）')
        axes[0].invert_yaxis()

        axes[1].barh(range(len(douyin_top)), douyin_top['viral_rate'].values,
                     color=COLOR_DOUYIN, alpha=0.7)
        axes[1].set_yticks(range(len(douyin_top)))
        axes[1].set_yticklabels(douyin_top['category'].values)
        axes[1].set_title('抖音 各分类爆款率 Top 10', fontsize=11)
        axes[1].set_xlabel('爆款率（%）')
        axes[1].invert_yaxis()

        plt.tight_layout()
        save_path = os.path.join(COMPARISON_FIGURES, "category_viral_rate_comparison.png")
        plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        print(f"  分类爆款率对比图保存到 {save_path}")
        return

    # 取Top 10共同分类（使用映射后的分类名进行对比）
    bili_stats['compare_cat'] = bili_stats['category_en']
    douyin_stats['compare_cat'] = douyin_stats['category']

    combined = pd.concat([bili_stats, douyin_stats])
    category_avg = combined[combined['compare_cat'].isin(common_categories)].groupby('compare_cat')['viral_rate'].mean()
    top_categories = category_avg.nlargest(10).index.tolist()

    # 绘制并排柱状图
    fig, ax = plt.subplots(figsize=(12, 6))

    bili_values = [bili_stats[bili_stats['compare_cat'] == cat]['viral_rate'].values[0]
                   if cat in bili_stats['compare_cat'].values else 0 for cat in top_categories]
    douyin_values = [douyin_stats[douyin_stats['compare_cat'] == cat]['viral_rate'].values[0]
                     if cat in douyin_stats['compare_cat'].values else 0 for cat in top_categories]

    x = np.arange(len(top_categories))
    width = 0.35

    ax.bar(x - width/2, bili_values, width, label='B站', color=COLOR_BILIBILI, alpha=0.7)
    ax.bar(x + width/2, douyin_values, width, label='抖音', color=COLOR_DOUYIN, alpha=0.7)

    ax.set_xlabel('内容分类')
    ax.set_ylabel('爆款率（%）')
    ax.set_title('B站 vs 抖音：各分类爆款率对比', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(top_categories, rotation=45, ha='right')
    ax.legend()

    plt.tight_layout()
    save_path = os.path.join(COMPARISON_FIGURES, "category_viral_rate_comparison.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  分类爆款率对比图保存到 {save_path}")


def compare_duration_distribution(bilibili_df, douyin_df):
    """
    对比2：爆款时长分布对比
    """
    print("\n" + "=" * 60)
    print("对比2：爆款时长分布对比")
    print("=" * 60)

    # 检查时长数据是否可用
    bili_has_duration = 'duration' in bilibili_df.columns and not bilibili_df['duration'].isna().all()
    douyin_has_duration = 'duration' in douyin_df.columns and not douyin_df['duration'].isna().all()

    if not bili_has_duration or not douyin_has_duration:
        print("  [跳过] 至少一个平台缺少时长数据，无法进行跨平台时长对比")
        print(f"  B站时长数据：{'有' if bili_has_duration else '无'}")
        print(f"  抖音时长数据：{'有' if douyin_has_duration else '无'}")
        return

    # 获取爆款视频（使用播放量Top 5%作为统一标准）
    bili_threshold = bilibili_df['view_count'].quantile(0.95) if 'view_count' in bilibili_df.columns else 0
    douyin_threshold = douyin_df['view_count'].quantile(0.95) if 'view_count' in douyin_df.columns else 0

    bili_viral = bilibili_df[bilibili_df['view_count'] >= bili_threshold]['duration'] / 60
    douyin_viral = douyin_df[douyin_df['view_count'] >= douyin_threshold]['duration'] / 60

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 密度曲线叠加
    axes[0].hist(bili_viral, bins=50, alpha=0.5, label='B站爆款', color=COLOR_BILIBILI, density=True)
    axes[0].hist(douyin_viral, bins=50, alpha=0.5, label='抖音爆款', color=COLOR_DOUYIN, density=True)
    axes[0].set_title('B站 vs 抖音：爆款时长分布（密度）', fontsize=11)
    axes[0].set_xlabel('时长（分钟）')
    axes[0].set_ylabel('密度')
    axes[0].legend()

    # 箱线图对比
    data_to_plot = [bili_viral.values, douyin_viral.values]
    bp = axes[1].boxplot(data_to_plot, labels=['B站爆款', '抖音爆款'], patch_artist=True)
    bp['boxes'][0].set_facecolor(COLOR_BILIBILI)
    bp['boxes'][1].set_facecolor(COLOR_DOUYIN)
    axes[1].set_title('B站 vs 抖音：爆款时长箱线图', fontsize=11)
    axes[1].set_ylabel('时长（分钟）')

    plt.tight_layout()
    save_path = os.path.join(COMPARISON_FIGURES, "duration_comparison.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  时长对比图保存到 {save_path}")

    # 输出统计对比
    print(f"\n  B站爆款平均时长：{bili_viral.mean():.1f} 分钟")
    print(f"  抖音爆款平均时长：{douyin_viral.mean():.1f} 分钟")
    print(f"  B站爆款中位时长：{bili_viral.median():.1f} 分钟")
    print(f"  抖音爆款中位时长：{douyin_viral.median():.1f} 分钟")


def compare_interaction_pattern(bilibili_df, douyin_df):
    """
    对比3：爆款互动模式对比
    """
    print("\n" + "=" * 60)
    print("对比3：爆款互动模式对比")
    print("=" * 60)

    # 计算互动率
    def calc_interaction_rates(df):
        rates = {}
        view_col = 'view_count' if 'view_count' in df.columns else None

        if view_col:
            for col, name in [('like_count', '点赞率'), ('comment_count', '评论率'),
                              ('share_count', '分享率')]:
                if col in df.columns:
                    rates[name] = (df[col] / df[view_col].replace(0, np.nan)).fillna(0).mean()

        return rates

    bili_rates = calc_interaction_rates(bilibili_df)
    douyin_rates = calc_interaction_rates(douyin_df)

    if not bili_rates or not douyin_rates:
        print("  缺少互动数据，跳过对比")
        return

    # 绘制柱状图对比
    fig, ax = plt.subplots(figsize=(8, 6))

    metrics = list(set(bili_rates.keys()) & set(douyin_rates.keys()))
    x = np.arange(len(metrics))
    width = 0.35

    bili_values = [bili_rates.get(m, 0) * 100 for m in metrics]
    douyin_values = [douyin_rates.get(m, 0) * 100 for m in metrics]

    ax.bar(x - width/2, bili_values, width, label='B站', color=COLOR_BILIBILI, alpha=0.7)
    ax.bar(x + width/2, douyin_values, width, label='抖音', color=COLOR_DOUYIN, alpha=0.7)

    ax.set_xlabel('互动指标')
    ax.set_ylabel('互动率（%）')
    ax.set_title('B站 vs 抖音：平均互动率对比', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()

    plt.tight_layout()
    save_path = os.path.join(COMPARISON_FIGURES, "interaction_comparison.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  互动模式对比图保存到 {save_path}")

    # 输出对比
    for metric in metrics:
        bili_val = bili_rates.get(metric, 0) * 100
        douyin_val = douyin_rates.get(metric, 0) * 100
        print(f"  {metric}: B站 {bili_val:.2f}% vs 抖音 {douyin_val:.2f}%")


def compare_headline_effect(bilibili_df, douyin_df):
    """
    对比5：头部效应对比（Top 1%视频占总播放量比例）
    """
    print("\n" + "=" * 60)
    print("对比5：头部效应对比")
    print("=" * 60)

    def calc_headline_effect(df, platform_name):
        if 'view_count' not in df.columns:
            return None

        total_views = df['view_count'].sum()
        top_1_percent = df.nlargest(max(1, int(len(df) * 0.01)), 'view_count')
        top_1_views = top_1_percent['view_count'].sum()

        concentration = top_1_views / total_views * 100 if total_views > 0 else 0
        return {
            'platform': platform_name,
            'total_videos': len(df),
            'total_views': total_views,
            'top_1_percent_videos': len(top_1_percent),
            'top_1_percent_views': top_1_views,
            'concentration': concentration
        }

    bili_effect = calc_headline_effect(bilibili_df, 'B站')
    douyin_effect = calc_headline_effect(douyin_df, '抖音')

    if bili_effect and douyin_effect:
        fig, ax = plt.subplots(figsize=(8, 5))

        platforms = ['B站', '抖音']
        concentrations = [bili_effect['concentration'], douyin_effect['concentration']]
        colors = [COLOR_BILIBILI, COLOR_DOUYIN]

        bars = ax.bar(platforms, concentrations, color=colors, alpha=0.7)
        ax.set_ylabel('Top 1%视频占总播放量比例（%）')
        ax.set_title('B站 vs 抖音：头部效应（播放量集中度）', fontsize=12)

        for bar, val in zip(bars, concentrations):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        save_path = os.path.join(COMPARISON_FIGURES, "headline_effect_comparison.png")
        plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        print(f"  头部效应对比图保存到 {save_path}")

        print(f"\n  B站 Top 1%视频占总播放量：{bili_effect['concentration']:.1f}%")
        print(f"  抖音 Top 1%视频占总播放量：{douyin_effect['concentration']:.1f}%")


def main():
    """主函数：执行跨平台对比分析"""
    bilibili_df, douyin_df = load_both_platforms()
    if bilibili_df is None or douyin_df is None:
        return

    print("=" * 60)
    print("B站 vs 抖音 跨平台对比分析")
    print("=" * 60)

    compare_category_viral_rate(bilibili_df, douyin_df)
    compare_duration_distribution(bilibili_df, douyin_df)
    compare_interaction_pattern(bilibili_df, douyin_df)
    compare_headline_effect(bilibili_df, douyin_df)

    print("\n  跨平台对比分析完成，图表保存在 figures/comparison/")


if __name__ == "__main__":
    main()
