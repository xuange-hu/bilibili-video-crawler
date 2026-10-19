"""``_evaluate_response`` 离线单测：把「成功 / 不可重试 / 可重试」的判定逻辑与
网络调用解耦后，无需真正发起请求即可覆盖每条分支。

此前这段逻辑嵌在 ``BilibiliCrawler._make_request`` 内部，只能靠替换 ``session.get``
的集成式测试间接覆盖；抽成纯函数后，这里用 duck-typed 的假响应直接断言判定结果。
"""

import os
import sys

import pytest
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from crawler import (  # noqa: E402
    NonRetryableHTTPError,
    RetryableHTTPError,
    _evaluate_response,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


def test_200_with_code_0_is_success():
    assert _evaluate_response(FakeResponse(200, {"code": 0, "data": {}})) is None


def test_403_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="403"):
        _evaluate_response(FakeResponse(403))


def test_404_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="404"):
        _evaluate_response(FakeResponse(404))


def test_429_is_retryable():
    with pytest.raises(RetryableHTTPError, match="429"):
        _evaluate_response(FakeResponse(429))


def test_api_minus_412_is_retryable():
    with pytest.raises(RetryableHTTPError, match="限流"):
        _evaluate_response(FakeResponse(200, {"code": -412, "message": "rate"}))


def test_api_minus_4_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="未登录"):
        _evaluate_response(FakeResponse(200, {"code": -4, "message": "auth"}))


def test_api_cookie_expired_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="Cookie过期"):
        _evaluate_response(FakeResponse(200, {"code": -401, "message": "expired"}))


def test_api_no_permission_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="无权限访问"):
        _evaluate_response(FakeResponse(200, {"code": -403, "message": "denied"}))


def test_api_resource_missing_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="资源不存在"):
        _evaluate_response(FakeResponse(200, {"code": -404, "message": "gone"}))


def test_api_unknown_code_is_non_retryable():
    with pytest.raises(NonRetryableHTTPError, match="API错误"):
        _evaluate_response(FakeResponse(200, {"code": 100, "message": "weird"}))


def test_non_json_body_is_treated_as_success():
    # 没有 code 字段的响应（如静态资源、二进制流）按成功处理
    assert _evaluate_response(FakeResponse(200)) is None


def test_other_4xx_propagates_to_raise_for_status():
    # 既非 403/404/429，也不是带 code 的 API 体：交给 raise_for_status 抛原始错误
    with pytest.raises(requests.exceptions.HTTPError):
        _evaluate_response(FakeResponse(400, {"detail": "bad"}))
