"""
单平台爆款特征分析模块。

功能：
1. 三重爆款定义法（排名法、阈值法、互动率法）
2. 各维度特征分析（时长、分类、发布时间、互动模式）
3. 生成单平台爆款画像
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    PROCESSED_DIR, BILIBILI_FIGURES, DOUYIN_FIGURES,
    VIRAL_PERCENTILE, VIRAL_THRESHOLD_SIGMA, VIRAL_INTERACTION_PERCENTILE,
    COLOR_VIRAL, COLOR_NORMAL, COLOR_BILIBILI, COLOR_DOUYIN, FIGURE_DPI
)

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_platform_data(platform):
    """加载平台清洗后数据"""
    filename = f"{platform}_clean.csv"
    path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(path):
        print(f"  未找到 {platform} 数据文件：{path}")
        return None
    return pd.read_csv(path)


def define_viral_videos(df, platform_name):
    """
    三重爆款定义法。

    Returns:
        pd.DataFrame: 添加了爆款标记列的数据框
    """
    print(f"\n{'=' * 60}")
    print(f"{platform_name} 爆款定义")
    print(f"{'=' * 60}")

    df_result = df.copy()

    # 定义A：播放量Top 5%
    if 'view_count' in df.columns:
        threshold_a = df['view_count'].quantile(VIRAL_PERCENTILE)
        df_result['viral_rank'] = (df['view_count'] >= threshold_a).astype(int)
        viral_count_a = df_result['viral_rank'].sum()
        print(f"\n定义A（排名法 Top 5%）：")
        print(f"  阈值：{threshold_a:,.0f} 播放量")
        print(f"  爆款数量：{viral_count_a}（{viral_count_a/len(df)*100:.1f}%）")

    # 定义B：均值 + 2倍标准差
    if 'view_count' in df.columns:
        mean_views = df['view_count'].mean()
        std_views = df['view_count'].std()
        threshold_b = mean_views + VIRAL_THRESHOLD_SIGMA * std_views
        df_result['viral_threshold'] = (df['view_count'] >= threshold_b).astype(int)
        viral_count_b = df_result['viral_threshold'].sum()
        print(f"\n定义B（阈值法 均值+2σ）：")
        print(f"  均值：{mean_views:,.0f} | 标准差：{std_views:,.0f}")
        print(f"  阈值：{threshold_b:,.0f} 播放量")
        print(f"  爆款数量：{viral_count_b}（{viral_count_b/len(df)*100:.1f}%）")

    # 定义C：互动率Top 5%
    interaction_cols = ['like_count', 'comment_count', 'share_count']
    available_cols = [c for c in interaction_cols if c in df.columns]

    if available_cols and 'view_count' in df.columns:
        # 计算互动率
        df_result['interaction_rate'] = (
            df[available_cols].sum(axis=1) / df['view_count'].replace(0, np.nan)
        ).fillna(0)

        threshold_c = df_result['interaction_rate'].quantile(VIRAL_INTERACTION_PERCENTILE)
        df_result['viral_interaction'] = (df_result['interaction_rate'] >= threshold_c).astype(int)
        viral_count_c = df_result['viral_interaction'].sum()
        print(f"\n定义C（互动率法 Top 5%）：")
        print(f"  互动率阈值：{threshold_c:.4f}")
        print(f"  爆款数量：{viral_count_c}（{viral_count_c/len(df)*100:.1f}%）")

    # 综合定义：至少满足两种定义
    viral_cols = ['viral_rank', 'viral_threshold', 'viral_interaction']
    available_viral_cols = [c for c in viral_cols if c in df_result.columns]

    if len(available_viral_cols) >= 2:
        df_result['viral_combined'] = (
            df_result[available_viral_cols].sum(axis=1) >= 2
        ).astype(int)
        viral_combined = df_result['viral_combined'].sum()
        print(f"\n综合定义（满足>=2种定义）：")
        print(f"  爆款数量：{viral_combined}（{viral_combined/len(df)*100:.1f}%）")

    return df_result


def analyze_duration_by_viral(df, platform_name, figures_dir):
    """分析爆款vs普通视频的时长差异"""
    if 'duration' not in df.columns or df['duration'].isna().all():
        print(f"\n  [跳过] {platform_name} 时长数据缺失，无法分析")
        return
    if 'viral_combined' not in df.columns:
        return

    viral = df[df['viral_combined'] == 1]['duration'] / 60
    normal = df[df['viral_combined'] == 0]['duration'] / 60

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 直方图对比
    axes[0].hist(normal, bins=50, alpha=0.5, label='普通视频', color=COLOR_NORMAL, density=True)
    axes[0].hist(viral, bins=50, alpha=0.5, label='爆款视频', color=COLOR_VIRAL, density=True)
    axes[0].set_title(f'{platform_name} 爆款vs普通视频时长分布', fontsize=11)
    axes[0].set_xlabel('时长（分钟）')
    axes[0].set_ylabel('密度')
    axes[0].legend()

    # 箱线图对比
    data_to_plot = [normal.values, viral.values]
    bp = axes[1].boxplot(data_to_plot, labels=['普通视频', '爆款视频'], patch_artist=True)
    bp['boxes'][0].set_facecolor(COLOR_NORMAL)
    bp['boxes'][1].set_facecolor(COLOR_VIRAL)
    axes[1].set_title(f'{platform_name} 爆款vs普通视频时长箱线图', fontsize=11)
    axes[1].set_ylabel('时长（分钟）')

    plt.tight_layout()
    save_path = os.path.join(figures_dir, f"{platform_name.lower()}_duration_by_viral.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  时长对比图保存到 {save_path}")

    # 输出统计
    print(f"\n  爆款平均时长：{viral.mean():.1f} 分钟")
    print(f"  普通视频平均时长：{normal.mean():.1f} 分钟")


def analyze_category_by_viral(df, platform_name, figures_dir):
    """分析各分类的爆款率"""
    if 'category' not in df.columns or 'viral_combined' not in df.columns:
        return

    # 计算各分类爆款率
    category_stats = df.groupby('category').agg(
        total=('title', 'count'),
        viral=('viral_combined', 'sum')
    ).reset_index()
    category_stats['viral_rate'] = category_stats['viral'] / category_stats['total'] * 100
    category_stats = category_stats.sort_values('viral_rate', ascending=False)

    # Top 10 分类
    top_10 = category_stats.head(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    color = COLOR_BILIBILI if platform_name == 'B站' else COLOR_DOUYIN
    bars = ax.barh(range(len(top_10)), top_10['viral_rate'].values,
                   color=color, alpha=0.7)
    ax.set_yticks(range(len(top_10)))
    ax.set_yticklabels(top_10['category'].values)
    ax.set_title(f'{platform_name} 各分类爆款率 Top 10', fontsize=12)
    ax.set_xlabel('爆款率（%）')
    ax.invert_yaxis()

    # 在柱子上显示数值
    for i, (rate, total) in enumerate(zip(top_10['viral_rate'], top_10['total'])):
        ax.text(rate + 0.1, i, f'{rate:.1f}% (n={int(total)})', va='center', fontsize=9)

    plt.tight_layout()
    save_path = os.path.join(figures_dir, f"{platform_name.lower()}_category_viral_rate.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  分类爆款率图保存到 {save_path}")


def analyze_publish_time_by_viral(df, platform_name, figures_dir):
    """分析发布时间与爆款的关系"""
    if 'publish_time' not in df.columns or 'viral_combined' not in df.columns:
        return

    df_time = df.copy()
    df_time['publish_time'] = pd.to_datetime(df_time['publish_time'], errors='coerce')
    df_time = df_time.dropna(subset=['publish_time'])

    if len(df_time) == 0:
        return

    # 提取小时和星期
    df_time['hour'] = df_time['publish_time'].dt.hour
    df_time['weekday'] = df_time['publish_time'].dt.dayofweek

    # 按小时统计爆款率
    hourly_stats = df_time.groupby('hour').agg(
        total=('title', 'count'),
        viral=('viral_combined', 'sum')
    ).reset_index()
    hourly_stats['viral_rate'] = hourly_stats['viral'] / hourly_stats['total'] * 100

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 按小时
    color = COLOR_BILIBILI if platform_name == 'B站' else COLOR_DOUYIN
    axes[0].bar(hourly_stats['hour'], hourly_stats['viral_rate'], color=color, alpha=0.7)
    axes[0].set_title(f'{platform_name} 按发布小时的爆款率', fontsize=11)
    axes[0].set_xlabel('发布小时（0-23）')
    axes[0].set_ylabel('爆款率（%）')
    axes[0].set_xticks(range(0, 24))

    # 按星期
    weekday_stats = df_time.groupby('weekday').agg(
        total=('title', 'count'),
        viral=('viral_combined', 'sum')
    ).reset_index()
    weekday_stats['viral_rate'] = weekday_stats['viral'] / weekday_stats['total'] * 100

    weekday_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    axes[1].bar(weekday_stats['weekday'], weekday_stats['viral_rate'], color=color, alpha=0.7)
    axes[1].set_title(f'{platform_name} 按发布星期的爆款率', fontsize=11)
    axes[1].set_xlabel('星期')
    axes[1].set_ylabel('爆款率（%）')
    axes[1].set_xticks(range(7))
    axes[1].set_xticklabels(weekday_labels)

    plt.tight_layout()
    save_path = os.path.join(figures_dir, f"{platform_name.lower()}_publish_time_viral.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  发布时间分析图保存到 {save_path}")


def main():
    """主函数：执行单平台爆款分析"""
    platforms = [
        ('bilibili', 'B站', BILIBILI_FIGURES),
        ('douyin', '抖音', DOUYIN_FIGURES),
    ]

    for platform_key, platform_name, figures_dir in platforms:
        df = load_platform_data(platform_key)
        if df is None:
            continue

        # 定义爆款
        df = define_viral_videos(df, platform_name)

        # 各维度分析
        print(f"\n{'=' * 60}")
        print(f"{platform_name} 爆款特征分析")
        print(f"{'=' * 60}")

        analyze_duration_by_viral(df, platform_name, figures_dir)
        analyze_category_by_viral(df, platform_name, figures_dir)
        analyze_publish_time_by_viral(df, platform_name, figures_dir)

        print(f"\n  {platform_name} 单平台爆款分析完成")


if __name__ == "__main__":
    main()
