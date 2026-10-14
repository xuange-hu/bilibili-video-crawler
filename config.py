"""配置管理：加载 ``config.json``，缺失或损坏时回退到内置默认值。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


class Config:
    """配置管理类"""

    def __init__(self, config_file: str = "config.json") -> None:
        self.config_file = config_file
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件。

        文件不存在、不是合法 JSON、或顶层不是对象（例如误写成数组）时，
        一律回退到默认配置并给出提示，避免后续 ``self.config.get`` 崩溃。
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
                print(
                    f"配置文件 {self.config_file} 顶层不是 JSON 对象，使用默认配置"
                )
            except Exception as e:
                print(f"配置文件读取失败: {e}，使用默认配置")

        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "request_timeout": 15,
            "request_delay": 2,
            "max_retries": 5,
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "download_dir": "./videos",
            "database_path": "./data.db",
            "log_level": "INFO",
            "log_dir": "./logs",
            "cookie": "",
            "use_proxy": False,
            "proxy_url": "",
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def save_default_config(self) -> None:
        """保存默认配置到文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._get_default_config(), f, indent=2, ensure_ascii=False)

    def create_directories(self) -> None:
        """创建必要的目录"""
        Path(str(self.get("download_dir"))).mkdir(parents=True, exist_ok=True)
        Path(str(self.get("log_dir"))).mkdir(parents=True, exist_ok=True)
