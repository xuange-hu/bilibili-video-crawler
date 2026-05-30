import requests
import time
import os
from datetime import datetime
from pathlib import Path
from config import Config
from logger import Logger
from database import Database

class BilibiliCrawler:
    """B站视频爬虫类"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.logger = Logger(self.config).get_logger()
        self.db = Database(self.config)
        self.config.create_directories()
        self.session = self._create_session()
    
    def _create_session(self):
        """创建requests会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config.get('user_agent'),
            'Referer': 'https://www.bilibili.com/'
        })
        return session
    
    def _make_request(self, url, method='GET', **kwargs):
        """发送请求，带重试机制"""
        max_retries = self.config.get('max_retries', 3)
        timeout = self.config.get('request_timeout', 10)
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=timeout, **kwargs)
                else:
                    response = self.session.post(url, timeout=timeout, **kwargs)
                
                response.raise_for_status()
                return response
            except Exception as e:
                self.logger.warning(f"请求失败 (第 {attempt + 1} 次): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(f"请求最终失败: {url}")
                    raise
    
    def get_video_info(self, bvid):
        """获取视频信息"""
        try:
            self.logger.info(f"正在获取视频信息: {bvid}")
            
            url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            response = self._make_request(url)
            data = response.json()
            
            if data['code'] != 0:
                self.logger.error(f"API返回错误: {data.get('message', '未知错误')}")
                return None
            
            video_data = data['data']
            
            video_info = {
                'bvid': bvid,
                'title': video_data.get('title', ''),
                'duration': video_data.get('duration', 0),
                'views': video_data.get('stat', {}).get('view', 0),
                'likes': video_data.get('stat', {}).get('like', 0),
                'coins': video_data.get('stat', {}).get('coin', 0),
                'favorites': video_data.get('stat', {}).get('favorite', 0),
                'shares': video_data.get('stat', {}).get('share', 0),
                'description': video_data.get('desc', ''),
                'cover_url': video_data.get('pic', ''),
                'up_name': video_data.get('owner', {}).get('name', ''),
                'publish_time': video_data.get('pubdate', 0),
            }
            
            # 保存到数据库
            self.db.save_video_info(video_info)
            
            self.logger.info(f"获取视频信息成功: {video_info['title']}")
            time.sleep(self.config.get('request_delay', 1))
            
            return video_info
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return None
    
    def download_video(self, bvid, output_dir=None):
        """下载视频"""
        output_dir = output_dir or self.config.get('download_dir')
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            self.logger.info(f"正在下载视频: {bvid}")
            
            # 首先获取视频信息
            video_info = self.get_video_info(bvid)
            if not video_info:
                raise Exception("无法获取视频信息")
            
            # 获取播放列表
            playback_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&qn=32"
            response = self._make_request(playback_url)
            playback_data = response.json()
            
            if playback_data['code'] != 0:
                error_msg = f"无法获取播放URL: {playback_data.get('message', '未知错误')}"
                self.logger.error(error_msg)
                self.db.save_download_record(bvid, status='failed', error_message=error_msg)
                return False
            
            # 获取下载链接
            durl = playback_data.get('data', {}).get('durl', [])
            if not durl:
                error_msg = "无法获取下载链接"
                self.logger.error(error_msg)
                self.db.save_download_record(bvid, status='failed', error_message=error_msg)
                return False
            
            # 下载视频
            file_path = os.path.join(output_dir, f"{video_info['title']}.mp4")
            
            # 清理不合法的文件名字符
            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in invalid_chars:
                file_path = file_path.replace(char, '_')
            
            video_url = durl[0]['url']
            
            self.logger.info(f"下载地址: {video_url[:100]}...")
            self.logger.info(f"保存路径: {file_path}")
            
            # 下载视频文件
            headers = {
                'User-Agent': self.config.get('user_agent'),
                'Referer': 'https://www.bilibili.com/'
            }
            
            response = self.session.get(video_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.logger.info(f"下载进度: {progress:.1f}% ({downloaded_size}/{total_size} bytes)")
            
            # 保存下载记录
            file_size = os.path.getsize(file_path)
            self.db.save_download_record(bvid, file_path=file_path, file_size=file_size, status='success')
            
            self.logger.info(f"视频下载成功: {file_path}")
            return True
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"视频下载失败: {error_msg}")
            self.db.save_download_record(bvid, status='failed', error_message=error_msg)
            return False
    
    def batch_download(self, bv_list, output_dir=None):
        """批量下载视频"""
        output_dir = output_dir or self.config.get('download_dir')
        
        success_count = 0
        fail_count = 0
        
        for bvid in bv_list:
            bvid = bvid.strip()
            if not bvid:
                continue
            
            try:
                if self.download_video(bvid, output_dir):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                self.logger.error(f"处理 {bvid} 时出错: {e}")
                fail_count += 1
            
            # 批量下载时增加延迟
            time.sleep(self.config.get('request_delay', 1) * 2)
        
        self.logger.info(f"批量下载完成 - 成功: {success_count}, 失败: {fail_count}")
        return success_count, fail_count
