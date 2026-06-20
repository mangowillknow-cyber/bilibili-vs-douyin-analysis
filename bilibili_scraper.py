"""
B站数据爬虫模块。

使用 bilibili-api-python 获取B站热门/排行榜视频的完整元数据：
- 标题、分区、作者、播放量、点赞、评论、分享、收藏、硬币、弹幕
- 时长（秒）、发布时间

爬取策略：
1. 通过热门视频API获取全站热门
2. 通过分区排行榜API获取各分区Top视频
3. 逐个获取视频详情（含时长、发布时间）
"""
import os
import sys
import time
import pandas as pd
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BILIBILI_RAW


def scrape_bilibili_hot(limit=200):
    """
    爬取B站热门视频数据。

    策略：先获取热门视频列表，再逐个获取详情（含时长、发布时间）。

    Args:
        limit: 最多爬取视频数量

    Returns:
        pd.DataFrame: 包含完整元数据的B站数据
    """
    import asyncio
    from bilibili_api import video, rank, hot, settings, video_zone

    settings.timeout = 15

    # 构建 tid -> 分区名 映射
    tid_map = {}
    try:
        zones = video_zone.get_zone_list()
        for z in zones:
            tid = z.get('tid')
            name = z.get('name', '')
            if tid and name:
                tid_map[tid] = name
    except Exception:
        pass

    async def _scrape():
        results = []
        bvid_list = []

        # 方式1: 获取热门视频列表
        print("  [1/2] 获取B站热门视频列表...")
        try:
            page = 1
            while len(bvid_list) < limit:
                pop = await hot.get_hot_videos(pn=page)
                vlist = pop.get('list', [])
                if not vlist:
                    break
                for v in vlist:
                    bv = v.get('bvid', '')
                    if bv and bv not in bvid_list:
                        bvid_list.append(bv)
                page += 1
                if page > 10:  # 安全限制
                    break
                await asyncio.sleep(0.3)
            print(f"    获取到 {len(bvid_list)} 个热门视频BV号")
        except Exception as e:
            print(f"    热门API失败: {e}")

        # 方式2: 如果热门不够，补充排行榜
        if len(bvid_list) < limit:
            print("  [2/2] 补充各分区排行榜...")
            try:
                rank_data = await rank.get_rank(rid=0)  # 全站排行榜
                vlist = rank_data.get('list', rank_data) if isinstance(rank_data, dict) else rank_data
                if isinstance(vlist, list):
                    for v in vlist[:50]:
                        bv = v.get('bvid', '')
                        if bv and bv not in bvid_list:
                            bvid_list.append(bv)
                print(f"    排行榜补充后共 {len(bvid_list)} 个BV号")
            except Exception as e:
                print(f"    排行榜API失败: {e}")

        # 逐个获取视频详情（含时长、发布时间）
        print(f"\n  开始获取 {min(len(bvid_list), limit)} 个视频的详细信息...")
        for i, bv in enumerate(bvid_list[:limit]):
            try:
                v = video.Video(bvid=bv)
                info = await v.get_info()
                stat = info.get('stat', {})

                results.append({
                    'bvid': bv,
                    '标题': info.get('title', ''),
                    'tid': info.get('tid', 0),
                    '分区': tid_map.get(info.get('tid', 0), info.get('tname', '')),
                    '作者': info.get('owner', {}).get('name', ''),
                    '播放量': stat.get('view', 0),
                    '点赞量': stat.get('like', 0),
                    '评论量': stat.get('reply', 0),
                    '分享量': stat.get('share', 0),
                    '收藏量': stat.get('favorite', 0),
                    '硬币': stat.get('coin', 0),
                    '弹幕量': stat.get('danmaku', 0),
                    '时长': info.get('duration', 0),  # 秒
                    '发布时间': info.get('pubdate', 0),  # Unix时间戳
                })

                if (i + 1) % 20 == 0:
                    print(f"    已采集 {i+1}/{min(len(bvid_list), limit)} ...")

                # 请求间隔，避免风控
                await asyncio.sleep(0.5)

            except Exception as e:
                if '412' in str(e) or 'rate' in str(e).lower():
                    print(f"    触发限流，等待5秒后继续...")
                    await asyncio.sleep(5)
                continue

        return pd.DataFrame(results)

    return asyncio.run(_scrape())


def main():
    """主函数：爬取B站数据"""
    print("=" * 60)
    print("B站数据爬虫")
    print("=" * 60)

    limit = 200  # 默认爬取200个视频
    print(f"\n目标：爬取 {limit} 个B站热门视频的完整信息")
    print("字段：标题、分区、作者、播放量、点赞、评论、分享、收藏、硬币、弹幕、时长、发布时间")
    print()

    start_time = time.time()
    df = scrape_bilibili_hot(limit=limit)
    elapsed = time.time() - start_time

    if df is None or len(df) == 0:
        print("\n[FAIL] 爬取失败，未获取到数据")
        return None

    # 转换时间戳
    df['发布时间'] = pd.to_datetime(df['发布时间'], unit='s', errors='coerce')

    # 去重
    df = df.drop_duplicates(subset='bvid', keep='first')

    # 保存
    save_path = os.path.join(BILIBILI_RAW, "bilibili_scraped.csv")
    df.to_csv(save_path, index=False, encoding='utf-8-sig')

    print(f"\n{'=' * 60}")
    print(f"[OK] 爬取完成！")
    print(f"  视频数量：{len(df)}")
    print(f"  耗时：{elapsed:.1f} 秒")
    print(f"  保存到：{save_path}")
    print(f"\n  时长范围：{df['时长'].min()}s ~ {df['时长'].max()}s（均值 {df['时长'].mean():.0f}s）")
    print(f"  发布时间范围：{df['发布时间'].min()} ~ {df['发布时间'].max()}")
    print(f"  分区分布：{df['分区'].nunique()} 个分区")
    print(f"\n  前5条数据：")
    print(df[['标题', '分区', '播放量', '时长', '发布时间']].head().to_string())

    return df


if __name__ == "__main__":
    main()
