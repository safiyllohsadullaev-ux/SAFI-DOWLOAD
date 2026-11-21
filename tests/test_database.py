import sqlite3

import pytest

from database import Database, pg_sql, postgres_dsn


@pytest.fixture
async def database(tmp_path):
    db = Database(tmp_path / "test.db")
    await db.connect()
    yield db
    await db.close()


async def test_upsert_and_language(database: Database):
    user = await database.upsert_user(100, "safi", "Safi")
    assert user["telegram_id"] == 100
    assert user["language"] == "tg"
    await database.set_language(100, "ru")
    user = await database.get_user(100)
    assert user["language"] == "ru"
    again = await database.upsert_user(100, "safi2", "Safi Two")
    assert again["username"] == "safi2"
    assert await database.count_users() == 1


async def test_downloads_and_dashboard(database: Database):
    await database.upsert_user(1, "a", "A")
    await database.upsert_user(2, "b", "B")
    await database.add_download(1, "reels", "success")
    await database.add_download(1, "photo", "failed")
    await database.add_download(2, "carousel", "success")
    counts = await database.user_download_counts(1)
    assert counts["success"] == 1
    assert counts["failed"] == 1
    dash = await database.dashboard()
    assert dash["total_users"] == 2
    assert dash["downloads_ok"] == 2
    assert dash["downloads_fail"] == 1
    media = await database.media_type_counts()
    assert media["reels"] == 1
    assert media["carousel"] == 1


async def test_block_settings_logs(database: Database):
    await database.upsert_user(5, "x", "X")
    await database.set_blocked(5, True, "spam")
    user = await database.get_user(5)
    assert user["is_blocked"] == 1
    assert user["block_reason"] == "spam"
    assert await database.count_blocked() == 1
    await database.set_setting("downloads_enabled", "0")
    assert await database.downloads_enabled() is False
    await database.add_log(99, "block_user", "5: spam")
    rows, total = await database.list_logs(0, 10)
    assert total == 1
    assert rows[0]["action"] == "block_user"
    ids = await database.target_user_ids()
    assert 5 not in ids


async def test_history_fields(database: Database):
    await database.upsert_user(7, "s", "Safi")
    item_id = await database.add_download(
        7,
        "video",
        "success",
        source_url="https://youtu.be/abcdefghijk",
        platform="youtube",
        title="clip",
        size_bytes=1000,
    )
    rows, total = await database.list_user_downloads(7, platform="youtube", query="clip", page=1, page_size=10)
    assert total == 1
    assert rows[0]["id"] == item_id
    assert rows[0]["size_bytes"] == 1000
    await database.save_preferences(7, {"theme": "dark", "language": "ru"})
    assert (await database.get_preferences(7))["theme"] == "dark"
    assert await database.delete_user_download(7, item_id) is True
    assert await database.delete_user_download(7, item_id) is False


async def test_old_sqlite_gains_columns(tmp_path):
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            language TEXT,
            joined_at TEXT,
            last_active TEXT,
            is_blocked INTEGER,
            block_reason TEXT
        )
        """
    )
    con.execute(
        """
        CREATE TABLE downloads (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            media_type TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    con.commit()
    con.close()
    old = Database(path)
    await old.connect()
    await old.upsert_user(1, "a", "A")
    await old.add_download(1, "video", "success", platform="tiktok", title="t", source_url="https://www.tiktok.com/v", size_bytes=5)
    rows, total = await old.list_user_downloads(1)
    assert total == 1
    assert rows[0]["platform"] == "tiktok"
    await old.close()


def test_postgres_dsn_strips_neon_ssl_params():
    sql = pg_sql("SELECT * FROM users WHERE telegram_id = ? AND username = ?")
    assert sql == "SELECT * FROM users WHERE telegram_id = $1 AND username = $2"
    dsn, ssl = postgres_dsn(
        "postgresql://user:secret@ep-example.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    assert dsn.startswith("postgresql://")
    assert "sslmode" not in dsn
    assert "channel_binding" not in dsn
    assert ssl is True
