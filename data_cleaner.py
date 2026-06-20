"""
数据清洗与字段统一映射模块。

功能：
1. 加载原始数据
2. 清洗异常值、缺失值
3. 统一映射到标准字段
4. 生成清洗后的数据文件
5. 输出数据质量报告
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    BILIBILI_RAW, DOUYIN_RAW, PROCESSED_DIR, MERGED_DIR,
    BILIBILI_FIELD_MAP, DOUYIN_FIELD_MAP, STANDARD_FIELDS
)


def clean_bilibili_data():
    """
    清洗B站数据。
    支持两种数据源：
    - 爬虫数据（含时长、发布时间）：bilibili_scraped.csv
    - 下载数据（无时长、发布时间）：BiliBili_data.csv

    Returns:
        pd.DataFrame: 清洗后的B站数据（标准字段）
    """
    print("=" * 60)
    print("开始清洗B站数据...")
    print("=" * 60)

    # 1. 加载原始数据（优先使用爬虫数据）
    is_scraped = False
    raw_path = os.path.join(BILIBILI_RAW, "bilibili_scraped.csv")
    if os.path.exists(raw_path):
        is_scraped = True
    else:
        for name in ["BiliBili_data.csv", "bilibili_data.csv"]:
            raw_path = os.path.join(BILIBILI_RAW, name)
            if os.path.exists(raw_path):
                break
        else:
            print("  未找到原始数据文件")
            return None

    df = pd.read_csv(raw_path)
    print(f"\n数据源：{'爬虫数据' if is_scraped else '下载数据'}")
    print(f"原始数据：{len(df)} 行 x {len(df.columns)} 列")

    # 2. 字段重命名
    available_map = {k: v for k, v in BILIBILI_FIELD_MAP.items() if k in df.columns}
    df_clean = df.rename(columns=available_map)

    # 3. 生成 video_id（如果不在映射中）
    if 'video_id' not in df_clean.columns:
        if '链接' in df.columns:
            df_clean['video_id'] = df['链接'].apply(
                lambda x: str(x).split('/')[-1] if pd.notna(x) else f'bilibili_{df.index[0]}'
            )
        else:
            df_clean['video_id'] = [f'bilibili_{i}' for i in range(len(df_clean))]

    # 4. 处理发布时间
    if 'publish_time' in df_clean.columns:
        # 如果是Unix时间戳（整数），转换为datetime
        if df_clean['publish_time'].dtype in ['int64', 'float64']:
            df_clean['publish_time'] = pd.to_datetime(df_clean['publish_time'], unit='s', errors='coerce')
        else:
            df_clean['publish_time'] = pd.to_datetime(df_clean['publish_time'], errors='coerce')

    # 5. 处理时长
    if 'duration' in df_clean.columns:
        df_clean['duration'] = pd.to_numeric(df_clean['duration'], errors='coerce')
        print(f"  时长范围：{df_clean['duration'].min():.0f}s ~ {df_clean['duration'].max():.0f}s")

    # 6. 清理标题中的HTML标签
    if 'title' in df_clean.columns and not is_scraped:
        df_clean['title'] = df_clean['title'].str.replace(r'<[^>]+>', '', regex=True)
        print("  已清理标题中的HTML标签")

    # 7. 缺失值处理
    print("\n[缺失值检查]")
    missing = df_clean.isnull().sum()
    print(missing[missing > 0] if missing.any() else "  无缺失值")

    # 数值字段缺失值用中位数填充
    numeric_cols = ['view_count', 'like_count', 'comment_count', 'share_count',
                    'favorite_count', 'coin_count', 'danmaku_count', 'duration']
    for col in numeric_cols:
        if col in df_clean.columns and df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
            print(f"  {col}: 用中位数 {median_val:.0f} 填充")

    # 文本字段缺失值用空字符串填充
    for col in ['title', 'category', 'author']:
        if col in df_clean.columns:
            df_clean[col].fillna('', inplace=True)

    # 8. 异常值处理
    print("\n[异常值处理]")
    if 'view_count' in df_clean.columns:
        negative_views = (df_clean['view_count'] < 0).sum()
        if negative_views > 0:
            df_clean = df_clean[df_clean['view_count'] >= 0]
            print(f"  移除 {negative_views} 条播放量为负数的记录")
    print(f"  最终有效数据：{len(df_clean)} 条")

    # 9. 添加平台标识
    df_clean['platform'] = 'bilibili'

    # 10. 选择标准字段输出
    output_cols = ['video_id', 'title', 'category', 'author', 'view_count',
                   'like_count', 'comment_count', 'share_count', 'favorite_count',
                   'coin_count', 'danmaku_count', 'duration', 'publish_time', 'platform']
    output_cols = [c for c in output_cols if c in df_clean.columns]
    df_clean = df_clean[output_cols]

    # 11. 保存清洗后的数据
    save_path = os.path.join(PROCESSED_DIR, "bilibili_clean.csv")
    df_clean.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n  B站数据清洗完成，保存到 {save_path}")
    print(f"  最终数据：{len(df_clean)} 行 x {len(df_clean.columns)} 列")

    return df_clean


def clean_douyin_data():
    """
    清洗抖音用户行为数据并聚合为视频级统计。

    实际列名：Unnamed: 0, user_id, video_id, video_category, like_type(0/1), relay_type(0/1), time
    聚合逻辑：
        - view_count = 每个video_id的交互次数（即用户数）
        - like_count = like_type 求和（点赞用户数）
        - share_count = relay_type 求和（转发用户数）
        - comment_count = 不可用，设为0
        - category = video_category
        - publish_time = time

    Returns:
        pd.DataFrame: 清洗后的抖音数据（视频级，标准字段）
    """
    print("\n" + "=" * 60)
    print("开始清洗抖音数据...")
    print("=" * 60)

    # 1. 加载原始数据（优先使用带真实播放量的TikTok数据集）
    raw_paths = [
        (os.path.join(DOUYIN_RAW, "tiktok_trends_2025.csv"), "tiktok_trends"),
        (os.path.join(DOUYIN_RAW, "dy_action.csv"), "tianchi"),
        (os.path.join(DOUYIN_RAW, "douyin_user_behavior.csv"), "tianchi"),
        (os.path.join(DOUYIN_RAW, "tiktok_stats.csv"), "zenodo"),
    ]

    df = None
    data_source = None
    for path, source in raw_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            data_source = source
            print(f"\n从 {os.path.basename(path)} 加载数据（数据源: {source}）")
            break

    if df is None:
        print("  未找到抖音原始数据文件")
        return None

    print(f"原始数据：{len(df)} 行 x {len(df.columns)} 列")

    # 2. 根据数据源类型处理
    if data_source == "tiktok_trends":
        # GitHub TikTok趋势数据集（含真实播放量和时长）
        print("检测到TikTok趋势数据集（含真实播放量+时长）")
        # 只取TikTok平台数据
        if 'platform' in df.columns:
            df = df[df['platform'] == 'TikTok']
            print(f"  筛选TikTok平台: {len(df)} 条")

        df_clean = pd.DataFrame()
        df_clean['video_id'] = df['row_id'].astype(str) if 'row_id' in df.columns else [f'tiktok_{i}' for i in range(len(df))]
        df_clean['title'] = df['title'].fillna('') if 'title' in df.columns else ''
        df_clean['category'] = df['category'].fillna('') if 'category' in df.columns else ''
        df_clean['author'] = df['author_handle'].fillna('') if 'author_handle' in df.columns else ''
        df_clean['view_count'] = pd.to_numeric(df['views'], errors='coerce').fillna(0).astype(int)
        df_clean['like_count'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0).astype(int)
        df_clean['comment_count'] = pd.to_numeric(df['comments'], errors='coerce').fillna(0).astype(int)
        df_clean['share_count'] = pd.to_numeric(df['shares'], errors='coerce').fillna(0).astype(int)
        df_clean['favorite_count'] = pd.to_numeric(df['saves'], errors='coerce').fillna(0).astype(int) if 'saves' in df.columns else 0
        df_clean['duration'] = pd.to_numeric(df['duration_sec'], errors='coerce') if 'duration_sec' in df.columns else np.nan
        df_clean['publish_time'] = pd.to_datetime(df['publish_date_approx'], errors='coerce') if 'publish_date_approx' in df.columns else pd.NaT
        df_clean['platform'] = 'douyin'

    elif data_source == "tianchi":
        # 天池用户行为数据 → 聚合为视频级统计
        print("检测到用户行为数据，正在聚合为视频级统计...")
        df_agg = df.groupby('video_id').agg(
            view_count=('user_id', 'count'),
            like_count=('like_type', 'sum'),
            share_count=('relay_type', 'sum'),
            category=('video_category', 'first'),
            publish_time=('time', 'first'),
        ).reset_index()
        df_agg['comment_count'] = 0
        df_agg['favorite_count'] = 0
        df_agg['title'] = ''
        df_agg['author'] = ''
        df_agg['duration'] = np.nan
        df_agg['platform'] = 'douyin'
        df_clean = df_agg
        print(f"  聚合前: {len(df)} 条 → 聚合后: {len(df_clean)} 个视频")

    elif data_source == "zenodo":
        zenodo_map = {'video_id': 'video_id', 'description': 'title', 'views': 'view_count',
                      'likes': 'like_count', 'comments': 'comment_count', 'shares': 'share_count',
                      'duration': 'duration'}
        available_map = {k: v for k, v in zenodo_map.items() if k in df.columns}
        df_clean = df.rename(columns=available_map)
        df_clean['category'] = ''
        df_clean['platform'] = 'douyin'
    else:
        print("  未识别的数据格式")
        return None

    # 3. 缺失值处理
    print("\n[缺失值检查]")
    missing = df_clean.isnull().sum()
    print(missing[missing > 0] if missing.any() else "  无缺失值")

    numeric_cols = ['view_count', 'like_count', 'comment_count', 'share_count']
    for col in numeric_cols:
        if col in df_clean.columns and df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
            print(f"  {col}: 用中位数 {median_val:.0f} 填充")

    text_cols = ['title', 'category', 'author']
    for col in text_cols:
        if col in df_clean.columns:
            df_clean[col].fillna('', inplace=True)

    # 4. 确保时间字段格式
    if 'publish_time' in df_clean.columns:
        df_clean['publish_time'] = pd.to_datetime(df_clean['publish_time'], errors='coerce')

    # 5. 异常值处理
    print("\n[异常值处理]")
    if 'view_count' in df_clean.columns:
        negative_views = (df_clean['view_count'] < 0).sum()
        if negative_views > 0:
            df_clean = df_clean[df_clean['view_count'] >= 0]
            print(f"  移除 {negative_views} 条播放量为负数的记录")
    print(f"  最终有效数据：{len(df_clean)} 条")

    # 6. 选择标准字段输出
    output_cols = ['video_id', 'title', 'category', 'author', 'view_count',
                   'like_count', 'comment_count', 'share_count', 'favorite_count',
                   'duration', 'publish_time', 'platform']
    output_cols = [c for c in output_cols if c in df_clean.columns]
    df_clean = df_clean[output_cols]

    # 7. 保存
    save_path = os.path.join(PROCESSED_DIR, "douyin_clean.csv")
    df_clean.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n[OK] 抖音数据清洗完成，保存到 {save_path}")
    print(f"  最终数据：{len(df_clean)} 行 x {len(df_clean.columns)} 列")

    return df_clean


def merge_platform_data(bilibili_df, douyin_df):
    """
    合并两个平台的数据到统一格式。

    Args:
        bilibili_df: B站清洗后数据
        douyin_df: 抖音清洗后数据

    Returns:
        pd.DataFrame: 合并后的对比数据
    """
    print("\n" + "=" * 60)
    print("合并双平台数据...")
    print("=" * 60)

    # 两个数据框都有的列（排除平台特有字段如 coin_count, danmaku_count）
    bilibili_cols = set(bilibili_df.columns)
    douyin_cols = set(douyin_df.columns)
    common_cols = sorted(bilibili_cols & douyin_cols)

    print(f"B站特有字段：{sorted(bilibili_cols - douyin_cols)}")
    print(f"抖音特有字段：{sorted(douyin_cols - bilibili_cols)}")
    print(f"共同字段：{common_cols}")

    merged_df = pd.concat([
        bilibili_df[common_cols],
        douyin_df[common_cols]
    ], ignore_index=True)

    # 保存合并数据
    save_path = os.path.join(MERGED_DIR, "platform_comparison.csv")
    merged_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n[OK] 合并数据保存到 {save_path}")
    print(f"  B站：{len(bilibili_df)} 条 | 抖音：{len(douyin_df)} 条 | 合计：{len(merged_df)} 条")

    return merged_df


def generate_quality_report(df, platform_name):
    """
    生成数据质量报告。

    Args:
        df: 清洗后的数据
        platform_name: 平台名称
    """
    print(f"\n{'=' * 60}")
    print(f"{platform_name} 数据质量报告")
    print(f"{'=' * 60}")

    print(f"\n1. 基本信息")
    print(f"   总行数：{len(df)}")
    print(f"   总列数：{len(df.columns)}")
    print(f"   列名：{list(df.columns)}")

    print(f"\n2. 数据类型")
    print(df.dtypes.to_string())

    print(f"\n3. 缺失值统计")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "   无缺失值")

    print(f"\n4. 数值字段描述统计")
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        print(numeric_df.describe().round(2).to_string())

    print(f"\n5. 前5行样本")
    print(df.head().to_string())


def main():
    """主函数：清洗并合并数据"""
    # 清洗B站数据
    bilibili_df = clean_bilibili_data()
    if bilibili_df is not None:
        generate_quality_report(bilibili_df, "B站")

    # 清洗抖音数据
    douyin_df = clean_douyin_data()
    if douyin_df is not None:
        generate_quality_report(douyin_df, "抖音")

    # 合并数据
    if bilibili_df is not None and douyin_df is not None:
        merged_df = merge_platform_data(bilibili_df, douyin_df)

    print("\n" + "=" * 60)
    print("数据清洗完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
