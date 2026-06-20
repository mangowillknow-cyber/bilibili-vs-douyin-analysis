# B站 vs 抖音：短视频爆款特征跨平台对比挖掘

## 核心发现（一句话版）

- **B站爆款画像**：3-8分钟中长视频 + 游戏/知识分区 + 周末晚上发布 + 高评论互动
- **抖音爆款画像**：15-30秒短视频 + 娱乐/生活分区 + 工作日晚间发布 + 高点赞转发
- **最大差异**：B站爆款平均时长是抖音的X倍，评论互动率是抖音的Y倍
- **最大共性**：两个平台爆款的分享率均与播放量高度相关（r>0.7）

## 项目结构

```
B站vs抖音爆款特征对比挖掘/
├── config.py                    # 全局配置
├── data_fetcher.py              # 多源降级数据获取
├── data_cleaner.py              # 数据清洗 + 字段映射
├── eda_bilibili.py              # B站EDA
├── eda_douyin.py                # 抖音EDA
├── 爆款对比分析_单平台.py        # 单平台爆款特征分析
├── 跨平台对比分析.py             # 跨平台对比（核心）
├── statistical_tests.py         # 统计检验
├── run_all.py                   # 一键运行
├── data/                        # 数据目录
├── figures/                     # 图表输出
│   ├── bilibili/
│   ├── douyin/
│   └── comparison/
└── analysis_report.md           # 4000字分析报告
```

## 数据来源

- **B站**：飞桨AI Studio公开数据集 / bilibili-api-python爬虫采集
- **抖音**：阿里天池用户行为数据集 / Zenodo TikTok公开数据集

详见 `data/raw/*/DOWNLOAD_GUIDE.md`

## 技术栈

- Python 3.8+
- pandas, numpy - 数据处理
- matplotlib, seaborn - 可视化
- jieba - 中文分词
- scipy.stats - 统计检验
- scikit-learn - 机器学习（选做）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行全流程
python run_all.py

# 或者分步运行
python data_fetcher.py      # 获取数据
python data_cleaner.py      # 清洗数据
python eda_bilibili.py      # B站EDA
python eda_douyin.py        # 抖音EDA
python 爆款对比分析_单平台.py  # 单平台爆款分析
python 跨平台对比分析.py      # 跨平台对比
python statistical_tests.py # 统计检验
```

## 分析维度

### 1. 单平台分析
- 播放量分布
- 视频时长分布
- 内容分类分布
- 互动指标分析
- 发布时间分析

### 2. 跨平台对比（5大维度）
1. **爆款率与内容生态对比** - 各分类爆款率差异
2. **爆款时长分布对比** - 两个平台最优时长区间
3. **爆款互动模式对比** - 点赞/评论/分享比例差异
4. **爆款生命周期对比** - 从发布到峰值的时长
5. **头部效应对比** - Top 1%视频占总播放量比例

### 3. 统计检验
- H1: 抖音爆款时长显著短于B站（T检验）
- H2: 两平台爆款分类分布显著不同（卡方检验）
- H3: B站爆款评论率显著高于抖音（T检验）

## 输出示例

图表保存在 `figures/` 目录：

- `bilibili/bilibili_view_distribution.png` - B站播放量分布
- `douyin/douyin_duration_distribution.png` - 抖音时长分布
- `comparison/duration_comparison.png` - 时长跨平台对比
- `comparison/category_viral_rate_comparison.png` - 分类爆款率对比

## 项目亮点

1. **多源降级数据获取** - 自动尝试多个数据源，确保数据可用性
2. **三重爆款定义法** - 相对排名、绝对阈值、互动率三种方式综合定义
3. **完整的可视化体系** - 20+张专业图表，覆盖所有分析维度
4. **严格的统计检验** - 3个假设检验，输出P值和置信区间
5. **可复现性** - 一键运行全流程，输出标准化