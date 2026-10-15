"""重试策略回归测试：区分「可重试」与「不可重试」错误。

修复前的行为：403 / 404 / Cookie 过期这类**确定性**客户端错误也会落进通用的
``except Exception`` 分支，被重试满 ``max_retries`` 次（每次还要 sleep 2~5 秒），
既白白等待，又可能在已被封禁的状态下继续施压。

修复后：
- 不可重试（403 / 404 / API -401 -403 -404 -4 等）→ 立即失败，只请求 1 次；
- 可重试（超时 / 连接错误 / 429 / API -412）→ 退避重试满 max_retries 次。
"""

import os
import sys
import time

import pytest
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from crawler import BilibiliCrawler  # noqa: E402
import crawler as crawler_mod  # noqa: E402

MAX_RETRIES = 3


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
    monkeypatch.setattr(Config, "create_directories", lambda self: None)
    cfg = Config()
    cfg.config["database_path"] = str(tmp_path / "test.db")
    cfg.config["max_retries"] = MAX_RETRIES
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(crawler_mod.wbi_sign, "fetch_keys", lambda: ("i", "s"))
    return BilibiliCrawler(cfg)


def _install(crawler, response=None, exc=None):
    """把 session.get/post 换成计数器；返回计数字典。"""
    calls = {"n": 0}

    def _fake(*a, **k):
        calls["n"] += 1
        if exc is not None:
            raise exc
        return response

    crawler.session.get = _fake
    crawler.session.post = _fake
    return calls


# ----------------------------------------------------------- 不可重试：只请求 1 次


def test_403_is_not_retried(crawler):
    calls = _install(crawler, FakeResponse(403))
    with pytest.raises(Exception, match="403"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == 1, "403 是确定性错误，不应重试"


def test_404_is_not_retried(crawler):
    calls = _install(crawler, FakeResponse(404))
    with pytest.raises(Exception, match="404"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == 1


def test_api_cookie_expired_is_not_retried(crawler):
    calls = _install(crawler, FakeResponse(200, {"code": -401, "message": "expired"}))
    with pytest.raises(Exception, match="Cookie过期"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == 1, "Cookie 过期重试无意义"


def test_api_no_permission_is_not_retried(crawler):
    calls = _install(crawler, FakeResponse(200, {"code": -403, "message": "denied"}))
    with pytest.raises(Exception, match="无权限访问"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == 1


# ------------------------------------------------------ 可重试：重试满 max_retries


def test_timeout_is_retried(crawler):
    calls = _install(crawler, exc=requests.exceptions.Timeout())
    with pytest.raises(Exception, match="超时"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == MAX_RETRIES


def test_connection_error_is_retried(crawler):
    calls = _install(crawler, exc=requests.exceptions.ConnectionError())
    with pytest.raises(Exception, match="无法连接"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == MAX_RETRIES


def test_429_rate_limit_is_retried(crawler):
    """429 属于限流，退避重试是正确应对（与 403/404 区别对待）。"""
    calls = _install(crawler, FakeResponse(429))
    with pytest.raises(Exception, match="429"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == MAX_RETRIES


def test_api_minus_412_rate_limit_is_retried(crawler):
    calls = _install(crawler, FakeResponse(200, {"code": -412, "message": "rate"}))
    with pytest.raises(Exception, match="限流"):
        crawler._make_request("https://api.bilibili.com/x")
    assert calls["n"] == MAX_RETRIES


def test_success_short_circuits_after_one_call(crawler):
    resp = FakeResponse(200, {"code": 0, "data": {"ok": True}})
    calls = _install(crawler, resp)
    assert crawler._make_request("https://api.bilibili.com/x") is resp
    assert calls["n"] == 1
