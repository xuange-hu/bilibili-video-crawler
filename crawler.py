import requests
import time
import os
import random
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from config import Config
from logger import Logger
from database import Database
from wbi_sign import wbi_sign


class BilibiliCrawler:
    """B站视频爬虫类 - 支持现代反爬虫机制"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.logger = Logger(self.config).get_logger()
        self.db = Database(self.config)
        self.config.create_directories()
        self.session = self._create_session()
        self._init_wbi_sign()
    
    def _init_wbi_sign(self):
        """初始化 WBI 签名"""
        try:
            self.logger.info("正在获取WBI签名密钥...")
            img_key, sub_key = wbi_sign.fetch_keys()
            if img_key and sub_key:
                wbi_sign.update_keys(img_key, sub_key)
                self.logger.info(f"✓ WBI签名密钥获取成功 (img_key: {img_key[:8]}..., sub_key: {sub_key[:8]}...)")
            else:
                self.logger.warning("⚠ 无法获取WBI签名密钥，API请求可能失败")
        except Exception as e:
            self.logger.warning(f"⚠ WBI签名初始化失败: {e}")
    
    def _create_session(self):
        """创建requests会话，配置反爬虫应对策略"""
        session = requests.Session()
        
        # 完整的请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'DNT': '1',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
        }
        session.headers.update(headers)
        
        # 添加Cookie
        cookie = self.config.get('cookie', '')
        if cookie:
            session.headers.update({'Cookie': cookie})
            self.logger.info("✓ 已加载B站Cookie")
        else:
            self.logger.warning("⚠ 未配置Cookie，某些API可能无法访问")
        
        # 配置代理
        if self.config.get('use_proxy'):
            proxy_url = self.config.get('proxy_url', '')
            if proxy_url:
                proxies = {'http': proxy_url, 'https': proxy_url}
                session.proxies.update(proxies)
                self.logger.info(f"✓ 已配置代理: {proxy_url}")
        
        return session
    
    def _make_request(self, url: str, method: str = 'GET', params: Dict = None, **kwargs) -> requests.Response:
        """
        发送请求，带重试机制和WBI签名
        
        Args:
            url: 请求URL
            method: HTTP方法
            params: 查询参数
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        max_retries = self.config.get('max_retries', 5)
        timeout = self.config.get('request_timeout', 15)
        
        # 如果需要WBI签名，则添加签名参数
        if self.config.get('use_wbi_sign') and 'api.bilibili.com' in url and method == 'GET':
            if params is None:
                params = {}
            # 确保是真正需要签名的API
            if any(api in url for api in ['playurl', 'view', 'search']):
                params = wbi_sign.sign(params.copy())
        
        for attempt in range(max_retries):
            try:
                # 随机延迟，避免被识别为爬虫
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 0.5)
                    self.logger.info(f"等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                
                # 更新User-Agent
                self.session.headers['User-Agent'] = self._get_random_user_agent()
                
                self.logger.debug(f"[{attempt + 1}/{max_retries}] {method} {url}")
                if params:
                    self.logger.debug(f"参数: {params}")
                
                if method.upper() == 'GET':
                    response = self.session.get(
                        url,
                        params=params,
                        timeout=timeout,
                        **kwargs
                    )
                else:
                    response = self.session.post(
                        url,
                        json=params,
                        timeout=timeout,
                        **kwargs
                    )
                
                # 检查HTTP状态码
                if response.status_code == 403:
                    raise Exception("请求被拒绝(403) - IP被限制或Cookie过期")
                
                if response.status_code == 404:
                    raise Exception("资源不存在(404)")
                
                if response.status_code == 429:
                    raise Exception("请求过于频繁(429) - 被限流")
                
                response.raise_for_status()
                
                # 检查API响应
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'code' in data:
                        code = data.get('code')
                        message = data.get('message', '未知错误')
                        
                        if code == 0:
                            # 成功
                            return response
                        elif code == -412:
                            raise Exception(f"请求被限流({code}) - {message}")
                        elif code == -4:
                            raise Exception(f"未登录或权限不足({code}) - {message}")
                        elif code == -401:
                            raise Exception(f"Cookie过期({code}) - {message}")
                        elif code == -403:
                            raise Exception(f"无权限访问({code}) - {message}")
                        elif code == -404:
                            raise Exception(f"资源不存在({code}) - {message}")
                        else:
                            raise Exception(f"API错误({code}) - {message}")
                except (ValueError, KeyError, TypeError):
                    # 不是JSON响应或不包含code字段，直接返回
                    return response
                
                return response
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏱ 请求超时 (第 {attempt + 1}/{max_retries} 次)")
                if attempt == max_retries - 1:
                    raise Exception("请求超时 - 网络连接较差")
            
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"🔌 连接错误 (第 {attempt + 1}/{max_retries} 次)")
                if attempt == max_retries - 1:
                    raise Exception("无法连接B站 - 请检查网络")
            
            except Exception as e:
                self.logger.warning(f"⚠ 请求失败 (第 {attempt + 1}/{max_retries} 次): {str(e)}")
                if attempt == max_retries - 1:
                    self.logger.error(f"❌ 请求最终失败: {url}")
                    raise
        
        raise Exception("未知错误")
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)
    
    def get_video_info(self, bvid: str) -> Optional[Dict[str, Any]]:
        """获取视频信息"""
        try:
            self.logger.info(f"📺 正在获取视频信息: {bvid}")
            
            url = "https://api.bilibili.com/x/web-interface/view"
            params = {'bvid': bvid}
            
            response = self._make_request(url, params=params)
            data = response.json()
            
            if data.get('code') != 0:
                error_msg = data.get('message', '未知错误')
                self.logger.error(f"❌ API返回错误: {error_msg} (code: {data.get('code')})")
                return None
            
            video_data = data.get('data', {})
            if not video_data:
                self.logger.error("❌ 获取视频数据为空")
                return None
            
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
            try:
                self.db.save_video_info(video_info)
            except Exception as db_error:
                self.logger.warning(f"⚠ 数据库保存失败: {db_error}")
            
            self.logger.info(f"✓ 获取成功: {video_info['title'][:50]}...")
            time.sleep(self.config.get('request_delay', 2))
            
            return video_info
        
        except Exception as e:
            self.logger.error(f"❌ 获取视频信息失败: {str(e)}")
            return None
    
    def download_video(self, bvid: str, output_dir: str = None) -> bool:
        """下载视频"""
        output_dir = output_dir or self.config.get('download_dir')
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            self.logger.info(f"\n📥 开始下载: {bvid}")
            
            # 获取视频信息
            video_info = self.get_video_info(bvid)
            if not video_info:
                raise Exception("无法获取视频信息")
            
            # 获取播放信息
            playback_url = "https://api.bilibili.com/x/player/playurl"
            params = {
                'bvid': bvid,
                'qn': 80,  # 清晰度
                'fnver': 0,
                'fnval': 4048,  # 支持多种格式
            }
            
            response = self._make_request(playback_url, params=params)
            playback_data = response.json()
            
            if playback_data.get('code') != 0:
                code = playback_data.get('code')
                message = playback_data.get('message', '未知错误')
                error_msg = f"无法获取播放链接: {message} (code: {code})"
                self.logger.error(f"❌ {error_msg}")
                
                # 诊断信息
                if code == -401:
                    self.logger.error("💡 建议: Cookie已过期，请重新获取B站登录Cookie")
                elif code == -403:
                    self.logger.error("💡 建议: 无权限访问，可能需要大会员或地域限制")
                elif code == -4:
                    self.logger.error("💡 建议: 需要登录B站账号")
                
                self.db.save_download_record(bvid, status='failed', error_message=error_msg)
                return False
            
            # 获取下载链接
            durl = playback_data.get('data', {}).get('durl', [])
            if not durl:
                error_msg = "无法获取下载链接 - 视频可能有地域限制或需要特殊权限"
                self.logger.error(f"❌ {error_msg}")
                self.logger.debug(f"响应数据: {json.dumps(playback_data, ensure_ascii=False, indent=2)}")
                self.db.save_download_record(bvid, status='failed', error_message=error_msg)
                return False
            
            # 准备下载
            file_name = f"{video_info['title']}.mp4"
            # 清理不合法的文件名字符
            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in invalid_chars:
                file_name = file_name.replace(char, '_')
            
            file_path = os.path.join(output_dir, file_name)
            video_url = durl[0].get('url', '')
            
            if not video_url:
                error_msg = "下载链接为空"
                self.logger.error(f"❌ {error_msg}")
                self.db.save_download_record(bvid, status='failed', error_message=error_msg)
                return False
            
            self.logger.info(f"📍 保存路径: {file_path}")
            self.logger.info(f"🔗 下载地址: {video_url[:100]}...")
            
            # 下载视频文件
            download_headers = {
                'User-Agent': self._get_random_user_agent(),
                'Referer': f'https://www.bilibili.com/video/{bvid}/',
                'Origin': 'https://www.bilibili.com',
            }
            
            response = self.session.get(
                video_url,
                headers=download_headers,
                timeout=30,
                stream=True,
                verify=False
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            chunk_size = 1024 * 1024  # 1MB
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            mb_downloaded = downloaded_size / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            self.logger.info(f"⏳ 进度: {progress:.1f}% ({mb_downloaded:.1f}MB/{mb_total:.1f}MB)")
            
            # 保存下载记录
            file_size = os.path.getsize(file_path)
            self.db.save_download_record(
                bvid,
                file_path=file_path,
                file_size=file_size,
                status='success'
            )
            
            self.logger.info(f"✅ 下载成功: {file_path}")
            return True
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ 下载失败: {error_msg}")
            try:
                self.db.save_download_record(bvid, status='failed', error_message=error_msg)
            except:
                pass
            return False
    
    def batch_download(self, bv_list: List[str], output_dir: str = None) -> Tuple[int, int]:
        """批量下载视频"""
        output_dir = output_dir or self.config.get('download_dir')
        
        success_count = 0
        fail_count = 0
        total = len([b for b in bv_list if b.strip()])
        
        for i, bvid in enumerate(bv_list, 1):
            bvid = bvid.strip()
            if not bvid:
                continue
            
            try:
                self.logger.info(f"\n[{i}/{total}] 处理: {bvid}")
                if self.download_video(bvid, output_dir):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                self.logger.error(f"❌ 处理 {bvid} 时出错: {str(e)}")
                fail_count += 1
            
            # 批量下载时增加延迟
            if i < total:
                delay = self.config.get('request_delay', 2) * random.uniform(1.5, 2.5)
                self.logger.info(f"⏳ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"✅ 完成! 成功: {success_count}, 失败: {fail_count}")
        self.logger.info(f"{'='*60}")
        
        return success_count, fail_count
