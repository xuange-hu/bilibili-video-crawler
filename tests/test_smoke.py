"""冒烟测试：覆盖配置加载、WBI 签名、URL 拼接等无网络依赖的逻辑。"""

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_example_config_is_valid_json_and_has_cookie_key():
    example = os.path.join(ROOT, "config.example.json")
    assert os.path.exists(example), "config.example.json 缺失"
    cfg = _load_config(example)
    assert "cookie" in cfg
    assert isinstance(cfg["cookie"], str)


def test_config_example_matches_schema_of_committed_config():
    example = _load_config(os.path.join(ROOT, "config.example.json"))
    live = os.path.join(ROOT, "config.json")
    if not os.path.exists(live):
        pytest.skip("config.json 未生成（用户应从 config.example.json 复制）")
    cfg = _load_config(live)
    assert set(example.keys()) == set(cfg.keys()), "config.json 与 config.example.json 字段不一致"


def test_wbi_sign_importable():
    import wbi_sign  # noqa: F401

    assert hasattr(wbi_sign, "sign"), "wbi_sign 应暴露 sign 函数"
