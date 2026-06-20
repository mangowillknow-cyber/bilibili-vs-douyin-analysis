"""
多源降级数据获取模块。

B站数据源优先级：
1. 飞桨AI Studio数据集（直接下载CSV）
2. bilibili-api-python爬虫采集
3. 提示用户手动下载

抖音数据源优先级：
1. 阿里天池用户行为数据集
2. Zenodo TikTok公开数据集
3. 提示用户手动下载

所有获取的原始数据保存到 data/raw/{platform}/ 目录。
"""
import os
import sys
import pandas as pd
import requests
import warnings
warnings.filterwarnings('ignore')

# 导入项目配置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    BILIBILI_RAW, DOUYIN_RAW,
    BILIBILI_FIELD_MAP, DOUYIN_FIELD_MAP
)


def fetch_bilibili():
    """
    获取B站数据，按优先级尝试多个数据源。

    Returns:
        pd.DataFrame: 清洗前的原始B站数据
    """
    print("=" * 60)
    print("开始获取B站数据...")
    print("=" * 60)

    # 方式一：尝试从飞桨AI Studio下载
    print("\n[1/3] 尝试从飞桨AI Studio下载...")
    try:
        df = _fetch_from_aistudio()
        if df is not None and len(df) > 0:
            save_path = os.path.join(BILIBILI_RAW, "bilibili_data.csv")
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"[OK] 飞桨AI Studio数据获取成功，共 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"[FAIL] 飞桨AI Studio下载失败: {e}")

    # 方式二：尝试使用bilibili-api-python爬虫
    print("\n[2/3] 尝试使用bilibili-api爬虫...")
    try:
        df = _fetch_via_bilibili_api()
        if df is not None and len(df) > 0:
            save_path = os.path.join(BILIBILI_RAW, "bilibili_data.csv")
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"[OK] bilibili-api数据获取成功，共 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"[FAIL] bilibili-api爬虫失败: {e}")

    # 方式三：检查是否已有本地数据
    print("\n[3/3] 检查本地已有数据...")
    for filename in ["bilibili_scraped.csv", "BiliBili_data.csv", "bilibili_data.csv"]:
        local_path = os.path.join(BILIBILI_RAW, filename)
        if os.path.exists(local_path):
            df = pd.read_csv(local_path)
            print(f"[OK] 使用本地已有数据 ({filename})，共 {len(df)} 条记录")
            return df

    # 所有方式都失败，生成提示文件
    print("\n[FAIL] 所有自动获取方式均失败")
    _generate_manual_download_guide("bilibili")
    return None


def _fetch_from_aistudio():
    """
    从飞桨AI Studio下载B站数据集。

    注意：飞桨AI Studio可能需要登录才能下载。
    这里提供下载URL作为参考，实际可能需要手动下载。
    """
    url = "https://aistudio.baidu.com/datasetdetail/307018/data"
    print(f"  飞桨AI Studio数据集地址: {url}")
    print("  提示：该数据集可能需要登录后手动下载")

    # 飞桨AI Studio通常需要登录认证，这里作为占位
    # 如果有直接下载链接，可以取消下面的注释
    # download_url = "https://actual-download-url"
    # response = requests.get(download_url, timeout=30)
    # if response.status_code == 200:
    #     df = pd.read_csv(pd.io.common.BytesIO(response.content))
    #     return df

    return None


def _fetch_via_bilibili_api():
    """
    使用bilibili-api-python库采集B站热门视频数据。

    采集热门视频的标题、播放量、点赞、评论、分享、分区等信息。
    """
    try:
        import asyncio
        from bilibili_api import video, search, settings

        # 设置请求间隔，避免被封
        settings.timeout = 10

        async def _fetch_hot_videos():
            """异步获取B站热门视频列表"""
            results = []

            # 获取热门视频的搜索结果
            search_result = await search.search_by_type(
                keyword="热门",
                search_type=search.SearchType.VIDEO,
                page=1,
                page_size=50
            )

            if not search_result or 'result' not in search_result:
                return pd.DataFrame()

            for item in search_result['result']:
                bvid = item.get('bvid', '')
                if not bvid:
                    continue

                try:
                    v = video.Video(bvid=bvid)
                    info = await v.get_info()
                    stat = info.get('stat', {})

                    results.append({
                        'bvid': bvid,
                        '标题': info.get('title', ''),
                        '分区': info.get('tname', ''),
                        '播放量': stat.get('view', 0),
                        '点赞量': stat.get('like', 0),
                        '评论量': stat.get('reply', 0),
                        '分享量': stat.get('share', 0),
                        '收藏量': stat.get('favorite', 0),
                        '时长': info.get('duration', 0),
                        '发布时间': pd.to_datetime(info.get('pubdate', 0), unit='s'),
                        'UP主': info.get('owner', {}).get('name', ''),
                    })

                    print(f"  已采集: {info.get('title', '')[:30]}...")

                    # 请求间隔，避免触发风控
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"  跳过视频 {bvid}: {e}")
                    continue

            return pd.DataFrame(results)

        # 运行异步函数
        df = asyncio.run(_fetch_hot_videos())
        return df if len(df) > 0 else None

    except ImportError:
        print("  bilibili-api-python 未安装，跳过爬虫方式")
        return None
    except Exception as e:
        print(f"  bilibili-api 爬虫异常: {e}")
        return None


def fetch_douyin():
    """
    获取抖音数据，按优先级尝试多个数据源。

    Returns:
        pd.DataFrame: 清洗前的原始抖音数据
    """
    print("\n" + "=" * 60)
    print("开始获取抖音数据...")
    print("=" * 60)

    # 方式一：尝试从阿里天池下载
    print("\n[1/3] 尝试从阿里天池下载...")
    try:
        df = _fetch_from_tianchi()
        if df is not None and len(df) > 0:
            save_path = os.path.join(DOUYIN_RAW, "douyin_user_behavior.csv")
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"[OK] 阿里天池数据获取成功，共 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"[FAIL] 阿里天池下载失败: {e}")

    # 方式二：尝试从Zenodo下载TikTok数据
    print("\n[2/3] 尝试从Zenodo下载TikTok数据...")
    try:
        df = _fetch_from_zenodo()
        if df is not None and len(df) > 0:
            save_path = os.path.join(DOUYIN_RAW, "tiktok_stats.csv")
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"[OK] Zenodo TikTok数据获取成功，共 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"[FAIL] Zenodo下载失败: {e}")

    # 方式三：检查是否已有本地数据
    print("\n[3/3] 检查本地已有数据...")
    for filename in ["tiktok_trends_2025.csv", "dy_action.csv", "douyin_user_behavior.csv", "tiktok_stats.csv"]:
        local_path = os.path.join(DOUYIN_RAW, filename)
        if os.path.exists(local_path):
            df = pd.read_csv(local_path)
            print(f"[OK] 使用本地已有数据 ({filename})，共 {len(df)} 条记录")
            return df

    # 所有方式都失败
    print("\n[FAIL] 所有自动获取方式均失败")
    _generate_manual_download_guide("douyin")
    return None


def _fetch_from_tianchi():
    """
    从阿里天池下载抖音用户行为数据集。

    数据集信息：
    - 链接：https://tianchi.aliyun.com/dataset/178410
    - 数据量：122,539条记录
    - 字段：用户ID、视频ID、视频主题、是否喜欢、是否转发、时间戳
    """
    url = "https://tianchi.aliyun.com/dataset/178410"
    print(f"  阿里天池数据集地址: {url}")
    print("  提示：该数据集可能需要登录阿里云账号后手动下载")

    # 阿里天池通常需要登录后才能下载
    # 如果有直接下载链接，可以取消下面的注释
    # download_url = "https://actual-download-url"
    # response = requests.get(download_url, timeout=30)
    # if response.status_code == 200:
    #     df = pd.read_csv(pd.io.common.BytesIO(response.content))
    #     return df

    return None


def _fetch_from_zenodo():
    """
    从Zenodo下载TikTok公开数据集。

    数据集信息：
    - 链接：https://zenodo.org/records/4672495
    - 字段：views, likes, shares, comments, duration, description, hashtags
    - 特点：93.06%的视频来自2020年，平均播放量36,147
    """
    # Zenodo API 获取文件下载链接
    record_id = "4672495"
    api_url = f"https://zenodo.org/api/records/{record_id}"

    print(f"  正在查询Zenodo API: {api_url}")

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # 找到CSV或Excel文件
        files = data.get('files', [])
        for file_info in files:
            key = file_info.get('key', '')
            if key.endswith(('.csv', '.xlsx', '.xls')):
                download_url = file_info.get('links', {}).get('self', '')
                if download_url:
                    print(f"  找到文件: {key}，开始下载...")
                    file_response = requests.get(download_url, timeout=60)
                    file_response.raise_for_status()

                    if key.endswith('.csv'):
                        df = pd.read_csv(pd.io.common.BytesIO(file_response.content))
                    else:
                        df = pd.read_excel(pd.io.common.BytesIO(file_response.content))

                    return df

        print("  Zenodo记录中未找到CSV/Excel文件")
        return None

    except Exception as e:
        print(f"  Zenodo API请求失败: {e}")
        return None


def _generate_manual_download_guide(platform):
    """生成手动下载指南文件"""
    if platform == "bilibili":
        guide_path = os.path.join(BILIBILI_RAW, "DOWNLOAD_GUIDE.md")
        content = """# B站数据手动下载指南

## 数据源：飞桨AI Studio

1. 访问：https://aistudio.baidu.com/datasetdetail/307018/data
2. 登录百度账号（需要飞桨AI Studio账号）
3. 点击"下载"按钮，下载 `BiliBili_data.csv`
4. 将文件保存到本目录：`data/raw/bilibili/bilibili_data.csv`

## 备选方案：使用爬虫

```bash
pip install bilibili-api-python aiohttp
python data_fetcher.py  # 重新运行会自动尝试爬虫方式
```
"""
    else:
        guide_path = os.path.join(DOUYIN_RAW, "DOWNLOAD_GUIDE.md")
        content = """# 抖音数据手动下载指南

## 方案一：阿里天池（推荐）

1. 访问：https://tianchi.aliyun.com/dataset/178410
2. 登录阿里云账号（需要完成学生认证）
3. 下载 `douyin_user_behavior.csv`
4. 保存到：`data/raw/douyin/douyin_user_behavior.csv`

## 方案二：Zenodo TikTok数据

1. 访问：https://zenodo.org/records/4672495
2. 在页面底部找到CSV文件
3. 下载并保存到：`data/raw/douyin/tiktok_stats.csv`

## 数据集说明

- 天池数据集：122,539条记录，2022年7月一周数据
- Zenodo数据集：TikTok视频统计数据，2020年为主
"""

    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n已生成手动下载指南：{guide_path}")


def main():
    """主函数：获取B站和抖音数据"""
    print("B站 vs 抖音 数据获取工具")
    print("=" * 60)

    # 获取B站数据
    bilibili_df = fetch_bilibili()

    # 获取抖音数据
    douyin_df = fetch_douyin()

    # 输出汇总
    print("\n" + "=" * 60)
    print("数据获取汇总")
    print("=" * 60)
    if bilibili_df is not None:
        print(f"[OK] B站数据：{len(bilibili_df)} 条记录")
    else:
        print("[FAIL] B站数据：未获取（请查看下载指南）")

    if douyin_df is not None:
        print(f"[OK] 抖音数据：{len(douyin_df)} 条记录")
    else:
        print("[FAIL] 抖音数据：未获取（请查看下载指南）")


if __name__ == "__main__":
    main()
