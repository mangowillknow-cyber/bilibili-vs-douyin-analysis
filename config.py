"""
全局配置文件：定义项目路径、分析参数、可视化设置。
所有脚本通过 import config 获取统一配置。
"""
import os

# ===== 路径配置 =====
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MERGED_DIR = os.path.join(DATA_DIR, "merged")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")

# 各平台子目录
BILIBILI_RAW = os.path.join(RAW_DIR, "bilibili")
DOUYIN_RAW = os.path.join(RAW_DIR, "douyin")
BILIBILI_FIGURES = os.path.join(FIGURES_DIR, "bilibili")
DOUYIN_FIGURES = os.path.join(FIGURES_DIR, "douyin")
COMPARISON_FIGURES = os.path.join(FIGURES_DIR, "comparison")

# ===== 爆款定义参数 =====
VIRAL_PERCENTILE = 0.95          # 定义A：Top 5%
VIRAL_THRESHOLD_SIGMA = 2        # 定义B：均值 + N倍标准差
VIRAL_INTERACTION_PERCENTILE = 0.95  # 定义C：互动率Top 5%

# ===== 可视化配置 =====
COLOR_BILIBILI = "#00A1D6"       # B站品牌蓝
COLOR_DOUYIN = "#000000"         # 抖音品牌黑
COLOR_VIRAL = "#FF6B6B"          # 爆款红色
COLOR_NORMAL = "#4ECDC4"         # 普通视频青色
FIGURE_DPI = 150
FIGURE_SIZE = (10, 6)

# ===== 标准字段映射 =====
STANDARD_FIELDS = {
    "video_id": str,
    "title": str,
    "category": str,
    "view_count": float,
    "like_count": float,
    "comment_count": float,
    "share_count": float,
    "favorite_count": float,
    "duration": float,
    "publish_time": "datetime64[ns]",
    "author": str,
    "platform": str,
}

# B站字段映射：原始字段名 -> 标准字段名
# 爬虫数据列名：bvid, 标题, tid, 分区, 作者, 播放量, 点赞量, 评论量, 分享量, 收藏量, 硬币, 弹幕量, 时长, 发布时间
BILIBILI_FIELD_MAP = {
    "bvid": "video_id",
    "标题": "title",
    "分区": "category",
    "作者": "author",
    "播放量": "view_count",
    "点赞量": "like_count",
    "评论量": "comment_count",
    "分享量": "share_count",
    "收藏量": "favorite_count",
    "硬币": "coin_count",
    "弹幕量": "danmaku_count",
    "时长": "duration",
    "发布时间": "publish_time",
}

# 抖音字段映射（根据实际数据集字段调整）
# TikTok Trends 2025 数据集
TIKTOK_FIELD_MAP = {
    "views": "view_count",
    "likes": "like_count",
    "comments": "comment_count",
    "shares": "share_count",
    "saves": "favorite_count",
    "duration_sec": "duration",
    "category": "category",
    "author_handle": "author",
    "title": "title",
    "publish_date_approx": "publish_time",
    "row_id": "video_id",
}

# 阿里天池用户行为数据集（备用）
TIANCHI_FIELD_MAP = {
    "video_id": "video_id",
    "video_category": "category",
    "like_type": "like_type",
    "relay_type": "relay_type",
    "time": "publish_time",
    "user_id": "user_id",
}

# 兼容旧代码：默认使用 TikTok 映射
DOUYIN_FIELD_MAP = TIKTOK_FIELD_MAP

# ===== 分析报告配置 =====
REPORT_PATH = os.path.join(PROJECT_ROOT, "analysis_report.md")
REPORT_WORD_COUNT = 4000
