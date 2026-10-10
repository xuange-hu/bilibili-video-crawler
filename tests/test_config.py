"""配置层单元测试：默认值、容错加载、落盘往返、不泄露密钥。"""

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402


def test_default_config_has_expected_fields():
    cfg = Config()
    for key in ("request_timeout", "download_dir", "cookie", "use_proxy", "proxy_url"):
        assert key in cfg.config, f"默认配置缺少字段 {key}"


def test_load_invalid_json_falls_back_to_defaults(tmp_path):
    bad = tmp_path / "config.json"
    bad.write_text("{ this is not valid json", encoding="utf-8")
    cfg = Config(str(bad))
    assert cfg.config == cfg._get_default_config()


def test_save_default_config_roundtrip(tmp_path):
    f = tmp_path / "config.json"
    cfg = Config(str(f))
    cfg.save_default_config()
    assert f.exists()
    cfg2 = Config(str(f))
    assert cfg2.get("download_dir") == "./videos"
    assert cfg2.get("cookie") == ""


def test_example_config_has_empty_cookie_and_is_valid(tmp_path):
    """模板必须为空 Cookie，避免把密钥误提交进仓库（合规）。"""
    example = os.path.join(ROOT, "config.example.json")
    assert os.path.exists(example)
    data = json.loads(open(example, encoding="utf-8").read())
    assert data.get("cookie", "") == ""


def test_get_returns_default_when_missing():
    cfg = Config()
    assert cfg.get("does_not_exist", "fallback") == "fallback"
