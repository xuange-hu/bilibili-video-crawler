"""配置与日志的健壮性回归测试。

覆盖本轮修复的两类真实缺陷：
- 配置文件损坏（非法 JSON / 顶层不是对象）时应回退默认值，而不是让后续
  ``self.config.get`` 崩溃；
- ``log_dir`` 缺失或 ``log_level`` 非法时，Logger 不应抛异常。

全部使用临时目录，不污染仓库、不触网。
"""

import json
import logging
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from logger import Logger  # noqa: E402

DEFAULT_KEYS = {
    "request_timeout",
    "request_delay",
    "max_retries",
    "user_agent",
    "download_dir",
    "database_path",
    "log_level",
    "log_dir",
    "cookie",
    "use_proxy",
    "proxy_url",
}


def _write(path, raw):
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)


def test_missing_config_file_falls_back_to_defaults(tmp_path):
    cfg = Config(str(tmp_path / "nope.json"))
    assert set(cfg.config.keys()) == DEFAULT_KEYS


def test_invalid_json_falls_back_to_defaults(tmp_path):
    p = tmp_path / "broken.json"
    _write(p, "{ this is not json ")
    cfg = Config(str(p))
    assert set(cfg.config.keys()) == DEFAULT_KEYS


def test_non_object_json_falls_back_to_defaults(tmp_path):
    """顶层是数组（而非对象）时也必须回退，否则 config.get 会崩。"""
    p = tmp_path / "list.json"
    _write(p, "[1, 2, 3]")
    cfg = Config(str(p))
    assert set(cfg.config.keys()) == DEFAULT_KEYS


def test_valid_object_config_is_loaded(tmp_path):
    p = tmp_path / "ok.json"
    _write(p, json.dumps({"max_retries": 9, "cookie": "SESSDATA=x"}))
    cfg = Config(str(p))
    assert cfg.get("max_retries") == 9
    assert cfg.get("cookie") == "SESSDATA=x"


def test_get_returns_default_for_missing_key(tmp_path):
    cfg = Config(str(tmp_path / "nope.json"))
    assert cfg.get("does_not_exist", "fallback") == "fallback"
    assert cfg.get("does_not_exist") is None


def test_save_default_config_roundtrip(tmp_path):
    p = tmp_path / "generated.json"
    cfg = Config(str(p))
    cfg.save_default_config()
    reloaded = Config(str(p))
    assert set(reloaded.config.keys()) == DEFAULT_KEYS
    assert reloaded.get("request_timeout") == 15


def test_create_directories_uses_configured_paths(tmp_path):
    cfg = Config()
    cfg.config["download_dir"] = str(tmp_path / "videos")
    cfg.config["log_dir"] = str(tmp_path / "logs")
    cfg.create_directories()
    assert (tmp_path / "videos").is_dir()
    assert (tmp_path / "logs").is_dir()


# --------------------------------------------------------------------- Logger


def test_logger_missing_log_dir_does_not_crash(tmp_path, monkeypatch):
    """log_dir 为 None 时旧实现会在 os.makedirs(None) 崩溃。"""
    monkeypatch.chdir(tmp_path)
    cfg = Config()
    cfg.config["log_dir"] = None
    logger = Logger(cfg).get_logger()
    assert (tmp_path / "logs").is_dir(), "应回退到 ./logs 而不是崩溃"


def test_logger_invalid_log_level_falls_back_to_info(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = Config()
    cfg.config["log_dir"] = str(tmp_path / "logs")
    cfg.config["log_level"] = "NOT_A_LEVEL"
    assert Logger(cfg).get_logger().level == logging.INFO


def test_logger_returns_named_logger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = Config()
    cfg.config["log_dir"] = str(tmp_path / "logs")
    logger = Logger(cfg).get_logger()
    assert logger.name == "BilibiliCrawler"
    # 重复实例化不应叠加 handler（Logger 会先 clear）
    Logger(cfg)
    assert len(logger.handlers) == 2, "应为 控制台 + 文件 两个 handler"
