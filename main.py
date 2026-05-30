#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path
from crawler import BilibiliCrawler
from config import Config

def main():
    parser = argparse.ArgumentParser(
        description='B站视频爬虫 - 获取视频信息并下载到本地',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 获取视频信息
  python main.py --bvid BV1oN411N7Jt
  
  # 下载视频
  python main.py --bvid BV1oN411N7Jt --download
  
  # 指定下载目录
  python main.py --bvid BV1oN411N7Jt --download --output ./my_videos
  
  # 批量下载（从文件读取BV号列表，每行一个）
  python main.py --batch video_list.txt --download
        '''
    )
    
    # 单个视频选项
    parser.add_argument('--bvid', type=str, help='视频BV号（例如: BV1oN411N7Jt）')
    
    # 批量视频选项
    parser.add_argument('--batch', type=str, help='包含BV号列表的文件路径（每行一个BV号）')
    
    # 下载选项
    parser.add_argument('--download', action='store_true', help='是否下载视频文件')
    
    # 输出目录
    parser.add_argument('--output', '-o', type=str, help='视频下载目录（默认: ./videos）')
    
    # 初始化配置
    parser.add_argument('--init-config', action='store_true', help='生成默认配置文件')
    
    args = parser.parse_args()
    
    # 初始化配置
    if args.init_config:
        config = Config()
        config.save_default_config()
        print("✓ 已生成默认配置文件: config.json")
        return 0
    
    # 创建配置和爬虫
    config = Config()
    crawler = BilibiliCrawler(config)
    
    # 单个视频处理
    if args.bvid:
        bvid = args.bvid.strip()
        output_dir = args.output or config.get('download_dir')
        
        print(f"\n{'='*60}")
        print(f"获取视频信息: {bvid}")
        print(f"{'='*60}\n")
        
        # 获取视频信息
        video_info = crawler.get_video_info(bvid)
        
        if not video_info:
            print("✗ 获取视频信息失败")
            return 1
        
        # 打印视频信息
        print(f"\n📺 视频信息:")
        print(f"  标题: {video_info['title']}")
        print(f"  UP主: {video_info['up_name']}")
        print(f"  播放量: {video_info['views']}")
        print(f"  点赞: {video_info['likes']}")
        print(f"  硬币: {video_info['coins']}")
        print(f"  收藏: {video_info['favorites']}")
        print(f"  分享: {video_info['shares']}")
        print(f"  时长: {video_info['duration']}秒")
        print(f"  简介: {video_info['description'][:100]}...\n")
        
        # 下载视频
        if args.download:
            print(f"下载视频到: {output_dir}\n")
            if crawler.download_video(bvid, output_dir):
                print(f"\n✓ 视频下载成功!")
                return 0
            else:
                print(f"\n✗ 视频下载失败")
                return 1
        else:
            print("✓ 视频信息已保存到数据库")
            return 0
    
    # 批量视频处理
    elif args.batch:
        batch_file = args.batch
        
        if not Path(batch_file).exists():
            print(f"✗ 文件不存在: {batch_file}")
            return 1
        
        # 读取BV号列表
        with open(batch_file, 'r', encoding='utf-8') as f:
            bv_list = f.readlines()
        
        output_dir = args.output or config.get('download_dir')
        
        print(f"\n{'='*60}")
        print(f"批量处理 {len(bv_list)} 个视频")
        print(f"{'='*60}\n")
        
        success, fail = crawler.batch_download(bv_list, output_dir)
        
        print(f"\n{'='*60}")
        print(f"批量处理完成")
        print(f"  成功: {success}")
        print(f"  失败: {fail}")
        print(f"{'='*60}\n")
        
        return 0 if fail == 0 else 1
    
    else:
        parser.print_help()
        print("\n错误: 必须指定 --bvid 或 --batch")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        sys.exit(1)
