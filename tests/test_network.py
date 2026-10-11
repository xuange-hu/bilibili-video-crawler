"""网络层集成测试：mock requests.Session，覆盖 _make_request 的全部错误分支与正常路径。

无需真实网络；验证异常语义与重试逻辑（重试延迟被 monkeypatch 为 0）。
"""

import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from crawler import BilibiliCrawler  # noqa: E402
import crawler as crawler_mod  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="ok"):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.content = text.encode("utf-8", "replace")

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def crawler(monkeypatch, tmp_path):
    # 避免测试中在仓库根目录创建 ./videos、./logs，并把 DB 指向临时文件
    monkeypatch.setattr(Config, "create_directories", lambda self: None)
    cfg = Config()
    cfg.config["database_path"] = str(tmp_path / "test.db")
    cfg.config["max_retries"] = 1  # 单次即终局，便于断言最终异常
    # 关闭重试延迟，避免测试卡住
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    # 阻止 __init__ 中的真实 WBI 网络请求
    monkeypatch.setattr(crawler_mod.wbi_sign, "fetch_keys", lambda: ("img_key", "sub_key"))
    c = BilibiliCrawler(cfg)
    return c


def _patch_session(crawler, fake):
    crawler.session.get = lambda *a, **k: fake
    crawler.session.post = lambda *a, **k: fake


def test_status_403_raises(crawler, monkeypatch):
    _patch_session(crawler, FakeResponse(403))
    with pytest.raises(Exception, match="403"):
        crawler._make_request("https://api.bilibili.com/x")


def test_status_404_raises(crawler, monkeypatch):
    _patch_session(crawler, FakeResponse(404))
    with pytest.raises(Exception, match="404"):
        crawler._make_request("https://api.bilibili.com/x")


def test_status_429_raises(crawler, monkeypatch):
    _patch_session(crawler, FakeResponse(429))
    with pytest.raises(Exception, match="429"):
        crawler._make_request("https://api.bilibili.com/x")


def test_api_code_minus_412_ratelimited(crawler, monkeypatch):
    _patch_session(crawler, FakeResponse(200, {"code": -412, "message": "rate"}))
    with pytest.raises(Exception, match="限流"):
        crawler._make_request("https://api.bilibili.com/x")


def test_api_code_minus_401_cookie_expired(crawler, monkeypatch):
    _patch_session(crawler, FakeResponse(200, {"code": -401, "message": "expired"}))
    with pytest.raises(Exception, match="Cookie过期"):
        crawler._make_request("https://api.bilibili.com/x")


def test_api_code_zero_returns_response(crawler, monkeypatch):
    fake = FakeResponse(200, {"code": 0, "data": {"ok": True}})
    _patch_session(crawler, fake)
    resp = crawler._make_request("https://api.bilibili.com/x")
    assert resp is fake


def test_non_json_response_returned_as_is(crawler, monkeypatch):
    # 无 code 字段的 JSON 或无法解析，应直接返回响应（不报错）
    _patch_session(crawler, FakeResponse(200, payload=None, text="<html>"))
    resp = crawler._make_request("https://api.bilibili.com/x")
    assert resp.status_code == 200


def test_timeout_raises(crawler, monkeypatch):
    import requests

    def _boom(*a, **k):
        raise requests.exceptions.Timeout()

    crawler.session.get = _boom
    crawler.session.post = _boom
    with pytest.raises(Exception, match="超时"):
        crawler._make_request("https://api.bilibili.com/x")


def test_connection_error_raises(crawler, monkeypatch):
    import requests

    def _boom(*a, **k):
        raise requests.exceptions.ConnectionError()

    crawler.session.get = _boom
    crawler.session.post = _boom
    with pytest.raises(Exception, match="无法连接"):
        crawler._make_request("https://api.bilibili.com/x")
