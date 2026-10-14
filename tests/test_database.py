"""数据库层集成测试：使用临时 SQLite 文件，验证 CRUD 语义与边界分支。

覆盖 ``save_video_info`` / ``get_video_info`` / ``get_all_videos`` /
``save_download_record``，以及 UPSERT（INSERT OR REPLACE）语义、
失败记录 ``completed_at`` 为 NULL、表结构自举等分支。全程离线、无网络。
"""

import os
import sqlite3
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from database import Database  # noqa: E402


@pytest.fixture
def db(tmp_path):
    """把数据库与日志目录都指向临时目录，避免污染仓库根目录。"""
    cfg = Config()
    cfg.config["database_path"] = str(tmp_path / "test.db")
    cfg.config["log_dir"] = str(tmp_path / "logs")
    return Database(cfg)


def _sample(bvid: str = "BV1xx411c7XX", title: str = "测试视频") -> dict:
    return {
        "bvid": bvid,
        "title": title,
        "duration": 120,
        "views": 1000,
        "likes": 50,
        "coins": 10,
        "favorites": 5,
        "shares": 2,
        "description": "简介文本",
        "cover_url": "https://example.com/cover.jpg",
        "up_name": "UP主",
        "publish_time": "2026-01-01",
    }


def test_init_db_creates_tables(db, tmp_path):
    """初始化应自举 videos / downloads 两张表。"""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    try:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()
    assert {"videos", "downloads"} <= names


def test_save_and_get_video_info_roundtrip(db):
    assert db.save_video_info(_sample()) is True
    row = db.get_video_info("BV1xx411c7XX")
    assert row is not None
    assert row["title"] == "测试视频"
    assert row["up_name"] == "UP主"
    assert row["views"] == 1000


def test_get_video_info_missing_returns_none(db):
    assert db.get_video_info("BV-nonexistent") is None


def test_save_video_info_upserts_by_bvid(db):
    """相同 bvid 重复保存应更新而非新增（INSERT OR REPLACE）。"""
    db.save_video_info(_sample(title="第一版"))
    db.save_video_info(_sample(title="第二版"))

    rows = db.get_all_videos()
    assert len(rows) == 1, "UPSERT 应保持唯一 bvid 只有一行"
    assert rows[0]["title"] == "第二版"


def test_get_all_videos_empty_initially(db):
    assert db.get_all_videos() == []


def test_get_all_videos_returns_every_row(db):
    for i in range(3):
        db.save_video_info(_sample(bvid=f"BV{i}", title=f"视频{i}"))
    titles = {r["title"] for r in db.get_all_videos()}
    assert titles == {"视频0", "视频1", "视频2"}


def test_raw_data_is_persisted_as_json(db):
    db.save_video_info(_sample())
    row = db.get_video_info("BV1xx411c7XX")
    assert "测试视频" in row["raw_data"], "raw_data 应落库为 JSON 文本"


def test_save_download_record_success(db, tmp_path):
    assert (
        db.save_download_record(
            "BV1xx411c7XX", file_path="/tmp/a.mp4", file_size=1234, status="success"
        )
        is True
    )

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    try:
        row = conn.execute(
            "SELECT bvid, status, completed_at FROM downloads WHERE bvid = ?",
            ("BV1xx411c7XX",),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[1] == "success"
    assert row[2] is not None, "成功记录应写入 completed_at"


def test_save_download_record_failure_leaves_completed_at_null(db, tmp_path):
    db.save_download_record(
        "BV-failed", status="failed", error_message="下载超时"
    )

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    try:
        row = conn.execute(
            "SELECT status, completed_at, error_message FROM downloads WHERE bvid = ?",
            ("BV-failed",),
        ).fetchone()
    finally:
        conn.close()
    assert row[0] == "failed"
    assert row[2] == "下载超时"
    assert row[1] is None, "失败记录不应写入 completed_at"


def test_save_video_info_handles_partial_payload(db):
    """缺少可选字段时不应崩溃，缺失列落库为 NULL。"""
    assert db.save_video_info({"bvid": "BV-partial", "title": "只有标题"}) is True
    row = db.get_video_info("BV-partial")
    assert row["title"] == "只有标题"
    assert row["views"] is None
