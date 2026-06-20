"""
抖音数据探索性分析（EDA）。

功能：
1. 数据概况统计
2. 各字段分布可视化
3. 相关性分析
4. 异常值检测
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROCESSED_DIR, DOUYIN_FIGURES, COLOR_DOUYIN, FIGURE_DPI

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_douyin_data():
    """加载抖音清洗后数据"""
    path = os.path.join(PROCESSED_DIR, "douyin_clean.csv")
    if not os.path.exists(path):
        print(f"  未找到数据文件：{path}")
        print("  请先运行 data_cleaner.py")
        return None
    return pd.read_csv(path)


def analyze_overview(df):
    """数据分析概况"""
    print("=" * 60)
    print("抖音数据概况分析")
    print("=" * 60)

    print(f"\n1. 基本信息")
    print(f"   总视频数：{len(df)}")
    print(f"   字段数：{len(df.columns)}")
    print(f"   列名：{list(df.columns)}")

    print(f"\n2. 数据类型")
    print(df.dtypes.to_string())

    print(f"\n3. 缺失值统计")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "   无缺失值")

    print(f"\n4. 数值字段统计")
    numeric_cols = ['view_count', 'like_count', 'comment_count', 'share_count', 'duration']
    available_cols = [c for c in numeric_cols if c in df.columns]
    if available_cols:
        print(df[available_cols].describe().round(2).to_string())


def plot_view_distribution(df):
    """播放量分布"""
    if 'view_count' not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].hist(df['view_count'], bins=50, color=COLOR_DOUYIN, alpha=0.7, edgecolor='white')
    axes[0].set_title('抖音播放量分布（线性刻度）', fontsize=12)
    axes[0].set_xlabel('播放量')
    axes[0].set_ylabel('视频数量')

    positive_views = df['view_count'][df['view_count'] > 0]
    axes[1].hist(positive_views, bins=50, color=COLOR_DOUYIN, alpha=0.7, edgecolor='white')
    axes[1].set_xscale('log')
    axes[1].set_title('抖音播放量分布（对数刻度）', fontsize=12)
    axes[1].set_xlabel('播放量（对数）')
    axes[1].set_ylabel('视频数量')

    plt.tight_layout()
    save_path = os.path.join(DOUYIN_FIGURES, "douyin_view_distribution.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  播放量分布图保存到 {save_path}")


def plot_duration_distribution(df):
    """视频时长分布"""
    if 'duration' not in df.columns or df['duration'].isna().all():
        print("  [跳过] 时长数据缺失，无法绘制时长分布图")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].hist(df['duration'] / 60, bins=50, color=COLOR_DOUYIN, alpha=0.7, edgecolor='white')
    axes[0].set_title('抖音视频时长分布', fontsize=12)
    axes[0].set_xlabel('时长（分钟）')
    axes[0].set_ylabel('视频数量')

    axes[1].boxplot(df['duration'] / 60, vert=True, patch_artist=True,
                    boxprops=dict(facecolor=COLOR_DOUYIN, alpha=0.7))
    axes[1].set_title('抖音视频时长箱线图', fontsize=12)
    axes[1].set_ylabel('时长（分钟）')

    plt.tight_layout()
    save_path = os.path.join(DOUYIN_FIGURES, "douyin_duration_distribution.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  时长分布图保存到 {save_path}")


def plot_category_analysis(df):
    """内容分类分析"""
    if 'category' not in df.columns:
        return

    category_counts = df['category'].value_counts()
    top_15 = category_counts.head(15)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(top_15)), top_15.values, color=COLOR_DOUYIN, alpha=0.7)
    ax.set_yticks(range(len(top_15)))
    ax.set_yticklabels(top_15.index)
    ax.set_title('抖音视频分类分布 Top 15', fontsize=12)
    ax.set_xlabel('视频数量')
    ax.invert_yaxis()

    plt.tight_layout()
    save_path = os.path.join(DOUYIN_FIGURES, "douyin_category_distribution.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  分类分布图保存到 {save_path}")


def plot_correlation_heatmap(df):
    """相关性热力图"""
    numeric_cols = ['view_count', 'like_count', 'comment_count', 'share_count', 'duration']
    available_cols = [c for c in numeric_cols if c in df.columns]

    if len(available_cols) < 2:
        return

    corr = df[available_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='RdYlBu_r', center=0,
                fmt='.2f', square=True, ax=ax)
    ax.set_title('抖音各指标相关性矩阵', fontsize=12)

    plt.tight_layout()
    save_path = os.path.join(DOUYIN_FIGURES, "douyin_correlation_heatmap.png")
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  相关性热力图保存到 {save_path}")


def main():
    """主函数：执行抖音EDA"""
    df = load_douyin_data()
    if df is None:
        return

    analyze_overview(df)

    print("\n" + "=" * 60)
    print("生成可视化图表...")
    print("=" * 60)

    plot_view_distribution(df)
    plot_duration_distribution(df)
    plot_category_analysis(df)
    plot_correlation_heatmap(df)

    print("\n[OK] 抖音EDA完成，图表保存在 figures/douyin/")


if __name__ == "__main__":
    main()
