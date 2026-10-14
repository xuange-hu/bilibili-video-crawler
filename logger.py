"""日志管理：控制台 + 本地日志文件。"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

from config import Config


class Logger:
    """日志管理类"""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.logger: logging.Logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("BilibiliCrawler")
        # log_level 可能来自用户配置，取值非法时回退 INFO 而不是让 getattr 炸掉
        level = getattr(logging, str(self.config.get("log_level", "INFO")), logging.INFO)
        if not isinstance(level, int):
            level = logging.INFO
        logger.setLevel(level)

        # 清除现有的处理器，避免重复实例化时叠加输出
        logger.handlers.clear()

        formatter = logging.Formatter(
            "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件处理器：log_dir 缺失时回退 ./logs，避免 os.makedirs(None) 崩溃；
        # 磁盘不可写时退化为仅控制台输出，而不是让整个程序挂掉。
        log_dir = self.config.get("log_dir") or "./logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(
                log_dir, f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning("日志文件初始化失败，仅输出到控制台: %s", e)

        return logger

    def get_logger(self) -> logging.Logger:
        """获取logger实例"""
        return self.logger
