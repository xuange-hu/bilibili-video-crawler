"""WBI 签名模块单测：纯逻辑、离线、可确定性复现。

覆盖：
- 空 img_key / sub_key 时 ``sign`` 原样返回参数（不注入 wts/w_rid）；
- ``_get_mixin_key`` 的混淆重排（含已知锚点值，作为回归护栏）；
- ``_get_sign`` 的字母序排序、URL 字符串拼接、SHA256，以及中文值 / 混合类型；
- ``sign`` 注入 wts / w_rid 且 w_rid 可被独立复现；
- ``update_keys`` / ``need_update`` 的过期判定；
- 模块级 ``sign`` 委托给全局单例；
- ``fetch_keys`` 用 mock 拦截 httpx，覆盖成功 / 错误码 / 缺字段 / 异常 / 非法 URL。

全程零网络：``httpx.get`` 与 ``time.time`` 均被 mock。
"""

import hashlib
import os
import sys
from unittest import mock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import wbi_sign  # noqa: E402
from wbi_sign import WbiSign  # noqa: E402

# 已知锚点（由独立实现计算，作为回归护栏；算法一旦改变此值必然失配）
_MIXIN_ANCHOR = "CciHpkPdLfjDNMomnhAIKBabOeGJlEFl"
_SIGN_ANCHOR = "0e24ea3843b94925e359fbb078941b0109e5fda7dc6a51f2ede0ebfe125bc070"


# --------------------------------------------------------------------- 空密钥

def test_sign_with_empty_keys_returns_params_unchanged():
    wb = WbiSign()  # 默认 img_key/sub_key 为空
    params = {"mid": 123, "name": "测试"}
    out = wb.sign(dict(params))
    assert out == params
    assert "wts" not in out
    assert "w_rid" not in out


def test_module_level_sign_with_empty_keys_is_noop():
    # 全局单例默认未初始化密钥
    out = wbi_sign.sign({"a": 1})
    assert out == {"a": 1}


# ------------------------------------------------------------- mixin key 重排

def test_get_mixin_key_known_anchor():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    assert wb._get_mixin_key() == _MIXIN_ANCHOR


def test_get_mixin_key_is_32_chars_and_deterministic():
    wb = WbiSign()
    wb.update_keys("img1234567890123", "sub4567890123456")
    k1 = wb._get_mixin_key()
    assert len(k1) == 32
    # 重复调用得到稳定结果
    assert wb._get_mixin_key() == k1


def test_get_mixin_key_changes_when_keys_change():
    a = WbiSign()
    a.update_keys("x" * 16, "y" * 16)
    b = WbiSign()
    b.update_keys("y" * 16, "x" * 16)
    assert a._get_mixin_key() != b._get_mixin_key()


def test_get_mixin_key_ignores_reordered_table_indices_out_of_range():
    # MIXIN_KEY_ENC_TAB 含 >= 32 的索引，orig_key 仅 32 长时这些应被跳过
    wb = WbiSign()
    wb.update_keys("a" * 16, "b" * 16)  # orig_key = 32 个 'a'/'b'
    mk = wb._get_mixin_key()
    assert len(mk) == 32
    # 越界索引被跳过，重排结果只会取自原串的合法字符，不会越界/崩溃
    assert set(mk) <= {"a", "b"}


# --------------------------------------------------------------- _get_sign

def _expected_sign(params: dict, mixin_key: str) -> str:
    items = sorted(params.items())
    query_string = "&".join(f"{k}={v}" for k, v in items)
    return hashlib.sha256((query_string + mixin_key).encode()).hexdigest()


def test_get_sign_is_recomputable():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    params = {"mid": 123, "name": "ce", "ps": 30}
    got = wb._get_sign(params)
    assert got == _expected_sign(params, wb._get_mixin_key())


def test_get_sign_sorts_by_key_alphabetically():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    # 故意乱序传入，签名应只取决于排序后的结果
    params = {"z": 1, "a": 2, "m": 3}
    expected = hashlib.sha256(
        ("a=2&m=3&z=1" + wb._get_mixin_key()).encode()
    ).hexdigest()
    assert wb._get_sign(params) == expected


def test_get_sign_handles_unicode_values():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    params = {"keyword": "中文搜索", "zone": "北京"}
    got = wb._get_sign(params)
    # 独立复现：中文按 UTF-8 字节参与 SHA256
    expected = hashlib.sha256(
        ("keyword=中文搜索&zone=北京" + wb._get_mixin_key()).encode("utf-8")
    ).hexdigest()
    assert got == expected


def test_get_sign_handles_mixed_value_types():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    params = {"mid": 123, "ps": 30, "order": "desc", "desc": True}
    got = wb._get_sign(params)
    expected = hashlib.sha256(
        ("desc=True&mid=123&order=desc&ps=30" + wb._get_mixin_key()).encode()
    ).hexdigest()
    assert got == expected


# ------------------------------------------------------------------- sign 主路径

def test_sign_injects_wts_and_wrid_with_known_anchor():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    with mock.patch.object(wbi_sign.time, "time", return_value=1700000000):
        out = wb.sign({"mid": 123, "name": "ce", "ps": 30})
    assert out["wts"] == 1700000000
    assert out["w_rid"] == _SIGN_ANCHOR


def test_sign_wrid_matches_independent_recompute():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    with mock.patch.object(wbi_sign.time, "time", return_value=1700000000):
        out = wb.sign({"mid": 123, "name": "ce", "ps": 30})
    signed = {k: v for k, v in out.items() if k != "w_rid"}
    assert out["w_rid"] == _expected_sign(signed, wb._get_mixin_key())


def test_sign_mutates_input_in_place():
    wb = WbiSign()
    wb.update_keys("abcdefghijklmnop", "ABCDEFGHIJKLMNOP")
    original = {"mid": 123}
    with mock.patch.object(wbi_sign.time, "time", return_value=1700000000):
        wb.sign(original)
    # 入参被就地修改（源码文档已声明此行为）
    assert "wts" in original
    assert "w_rid" in original


def test_module_level_sign_delegates_to_singleton(monkeypatch):
    monkeypatch.setattr(wbi_sign.wbi_sign, "img_key", "abcdefghijklmnop")
    monkeypatch.setattr(wbi_sign.wbi_sign, "sub_key", "ABCDEFGHIJKLMNOP")
    with mock.patch.object(wbi_sign.time, "time", return_value=1700000000):
        out = wbi_sign.sign({"mid": 123, "name": "ce", "ps": 30})
    assert out["w_rid"] == _SIGN_ANCHOR


# --------------------------------------------------------- update_keys / need_update

def test_need_update_false_immediately_after_update():
    wb = WbiSign()
    wb.update_keys("i", "s")
    assert wb.need_update() is False


def test_need_update_true_after_interval():
    wb = WbiSign()
    wb.update_keys("i", "s")
    with mock.patch.object(
        wbi_sign.time, "time", return_value=wb.last_update + wb.update_interval + 1
    ):
        assert wb.need_update() is True


def test_update_keys_sets_fields():
    wb = WbiSign()
    wb.update_keys("imgK", "subK")
    assert wb.img_key == "imgK"
    assert wb.sub_key == "subK"
    assert wb.last_update > 0


# ----------------------------------------------------------------- fetch_keys

def _fake_response(payload):
    m = mock.MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = payload
    return m


def test_fetch_keys_success_extracts_keys():
    nav = {
        "code": 0,
        "data": {
            "wbi_img": {
                "img_url": "https://i0.hdslb.com/bfs/wbi/abcDEF123.png",
                "sub_url": "https://i0.hdslb.com/bfs/wbi/ghiJKL456.png",
            }
        },
    }
    with mock.patch.object(wbi_sign.httpx, "get", return_value=_fake_response(nav)):
        assert WbiSign.fetch_keys() == ("abcDEF123", "ghiJKL456")


def test_fetch_keys_nonzero_code_returns_empty():
    with mock.patch.object(
        wbi_sign.httpx, "get", return_value=_fake_response({"code": -412})
    ):
        assert WbiSign.fetch_keys() == ("", "")


def test_fetch_keys_missing_wbi_img_returns_empty():
    with mock.patch.object(
        wbi_sign.httpx, "get", return_value=_fake_response({"code": 0, "data": {}})
    ):
        assert WbiSign.fetch_keys() == ("", "")


def test_fetch_keys_exception_returns_empty():
    with mock.patch.object(
        wbi_sign.httpx, "get", side_effect=Exception("boom")
    ):
        assert WbiSign.fetch_keys() == ("", "")


def test_fetch_keys_malformed_url_returns_empty():
    nav = {
        "code": 0,
        "data": {"wbi_img": {"img_url": "not-a-url", "sub_url": "also-not"}},
    }
    with mock.patch.object(wbi_sign.httpx, "get", return_value=_fake_response(nav)):
        assert WbiSign.fetch_keys() == ("", "")


def test_fetch_keys_calls_nav_endpoint_with_headers():
    captured = {}

    def _spy(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        return _fake_response(
            {
                "code": 0,
                "data": {
                    "wbi_img": {
                        "img_url": "https://x/abc.png",
                        "sub_url": "https://x/def.png",
                    }
                },
            }
        )

    with mock.patch.object(wbi_sign.httpx, "get", side_effect=_spy):
        keys = WbiSign.fetch_keys()

    assert keys == ("abc", "def")
    assert captured["url"] == "https://api.bilibili.com/x/web-interface/nav"
    assert "User-Agent" in captured["headers"]
    assert captured["headers"].get("Referer") == "https://www.bilibili.com/"
