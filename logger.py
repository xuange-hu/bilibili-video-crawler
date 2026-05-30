import logging
import os
from datetime import datetime
from config import Config

class Logger:
    """日志管理类"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('BilibiliCrawler')
        level = getattr(logging, self.config.get('log_level', 'INFO'))
        logger.setLevel(level)
        
        # 清除现有的处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        log_dir = self.config.get('log_dir')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger
