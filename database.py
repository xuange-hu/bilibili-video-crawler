import sqlite3
import json
from datetime import datetime
from config import Config
from logger import Logger

class Database:
    """数据库管理类"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.logger = Logger(self.config).get_logger()
        self.db_path = self.config.get('database_path')
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建视频信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bvid TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    duration INTEGER,
                    views INTEGER,
                    likes INTEGER,
                    coins INTEGER,
                    favorites INTEGER,
                    shares INTEGER,
                    description TEXT,
                    cover_url TEXT,
                    up_name TEXT,
                    publish_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data TEXT
                )
            ''')
            
            # 创建下载记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bvid TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    status TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (bvid) REFERENCES videos(bvid)
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库初始化成功")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def save_video_info(self, video_info):
        """保存视频信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (bvid, title, duration, views, likes, coins, favorites, shares, 
                 description, cover_url, up_name, publish_time, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_info.get('bvid'),
                video_info.get('title'),
                video_info.get('duration'),
                video_info.get('views'),
                video_info.get('likes'),
                video_info.get('coins'),
                video_info.get('favorites'),
                video_info.get('shares'),
                video_info.get('description'),
                video_info.get('cover_url'),
                video_info.get('up_name'),
                video_info.get('publish_time'),
                json.dumps(video_info, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"视频信息保存成功: {video_info.get('title')}")
            return True
        except Exception as e:
            self.logger.error(f"视频信息保存失败: {e}")
            return False
    
    def save_download_record(self, bvid, file_path=None, file_size=None, status='success', error_message=None):
        """保存下载记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO downloads 
                (bvid, file_path, file_size, status, error_message, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                bvid,
                file_path,
                file_size,
                status,
                error_message,
                datetime.now() if status == 'success' else None
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"下载记录保存成功: {bvid}")
            return True
        except Exception as e:
            self.logger.error(f"下载记录保存失败: {e}")
            return False
    
    def get_video_info(self, bvid):
        """获取视频信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM videos WHERE bvid = ?', (bvid,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"查询视频信息失败: {e}")
            return None
    
    def get_all_videos(self):
        """获取所有视频信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM videos ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"查询所有视频信息失败: {e}")
            return []
