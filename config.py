import json
import os
from pathlib import Path

class Config:
    """配置管理类"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"配置文件读取失败: {e}，使用默认配置")
        
        return self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "request_timeout": 10,
            "request_delay": 1,
            "max_retries": 3,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "download_dir": "./videos",
            "database_path": "./data.db",
            "log_level": "INFO",
            "log_dir": "./logs"
        }
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def save_default_config(self):
        """保存默认配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._get_default_config(), f, indent=2, ensure_ascii=False)
    
    def create_directories(self):
        """创建必要的目录"""
        Path(self.get('download_dir')).mkdir(parents=True, exist_ok=True)
        Path(self.get('log_dir')).mkdir(parents=True, exist_ok=True)
