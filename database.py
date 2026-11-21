from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import aiosqlite

import config
from config import BOT_VERSION, DB_PATH
from utils.helpers import day_start, now_iso

USERS_PAGE = 6
LOGS_PAGE = 8

_EXTRA_COLUMNS = (
    ("downloads", "source_url", "TEXT NOT NULL DEFAULT ''"),
    ("downloads", "platform", "TEXT NOT NULL DEFAULT ''"),
    ("downloads", "title", "TEXT NOT NULL DEFAULT ''"),
    ("downloads", "size_bytes", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "preferences", "TEXT NOT NULL DEFAULT ''"),
)


def pg_sql(sql: str) -> str:
    index = 0
    parts: list[str] = []
    for char in sql:
        if char == "?":
            index += 1
            parts.append(f"${index}")
        else:
            parts.append(char)
    return "".join(parts)


def postgres_dsn(url: str) -> tuple[str, bool]:
    parts = urlsplit(url)
    query: list[tuple[str, str]] = []
    ssl = False
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            ssl = value != "disable"
            continue
        if key == "channel_binding":
            continue
        query.append((key, value))
    host = parts.hostname or ""
    if host.endswith("neon.tech"):
        ssl = True
    scheme = "postgresql" if parts.scheme in {"postgres", "postgresql"} else parts.scheme
    clean = urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    return clean, ssl


class PgCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self._index = 0

    async def fetchone(self) -> dict[str, Any] | None:
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    async def fetchall(self) -> list[dict[str, Any]]:
        rows = self._rows[self._index :]
        self._index = len(self._rows)
        return rows


class PgConn:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def execute(self, sql: str, params: tuple | list = ()) -> PgCursor:
        statement = pg_sql(sql)
        async with self._pool.acquire() as conn:
            if statement.lstrip()[:6].upper() == "SELECT" or " RETURNING " in statement.upper():
                rows = await conn.fetch(statement, *params)
                return PgCursor([dict(row) for row in rows])
            await conn.execute(statement, *params)
            return PgCursor([])

    async def commit(self) -> None:
        return None

    async def close(self) -> None:
        await self._pool.close()


class Database:
    def __init__(self, path: str | None = None, url: str | None = None) -> None:
        self.path = str(path or DB_PATH)
        if url is not None:
            self.url = url.strip()
        elif path is None:
            self.url = config.DATABASE_URL
        else:
            self.url = ""
        self._conn: Any = None
        self._postgres = False

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected")
        return self._conn

    async def connect(self) -> None:
        if self.url.startswith(("postgres://", "postgresql://")):
            import asyncpg

            dsn, ssl = postgres_dsn(self.url)
            pool = await asyncpg.create_pool(
                dsn,
                ssl="require" if ssl else False,
                min_size=1,
                max_size=4,
                statement_cache_size=0,
            )
            self._conn = PgConn(pool)
            self._postgres = True
        else:
            self._conn = await aiosqlite.connect(self.path)
            self._conn.row_factory = aiosqlite.Row
            await self.conn.execute("PRAGMA journal_mode=WAL")
            await self.conn.execute("PRAGMA foreign_keys=ON")
            self._postgres = False
        await self._create_tables()
        await self._seed_settings()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _create_tables(self) -> None:
        if self._postgres:
            await self._create_postgres_tables()
        else:
            await self._create_sqlite_tables()
        await self._ensure_columns()
        await self.conn.commit()

    async def _column_names(self, table: str) -> set[str]:
        if self._postgres:
            cur = await self.conn.execute(
                """
                SELECT column_name AS name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = ?
                """,
                (table,),
            )
        else:
            cur = await self.conn.execute(f"PRAGMA table_info({table})")
        rows = await cur.fetchall()
        return {str(row["name"]) for row in rows}

    async def _ensure_columns(self) -> None:
        known: dict[str, set[str]] = {}
        for table, column, definition in _EXTRA_COLUMNS:
            if table not in known:
                known[table] = await self._column_names(table)
            if column in known[table]:
                continue
            await self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            known[table].add(column)

    async def _create_sqlite_tables(self) -> None:
        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                full_name TEXT,
                language TEXT NOT NULL DEFAULT 'tg',
                joined_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                block_reason TEXT,
                preferences TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                source_url TEXT NOT NULL DEFAULT '',
                platform TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                size_bytes INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                total_users INTEGER NOT NULL DEFAULT 0,
                successful INTEGER NOT NULL DEFAULT 0,
                failed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id);
            CREATE INDEX IF NOT EXISTS idx_downloads_created ON downloads(created_at);
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_logs_created ON activity_logs(created_at);
            """
        )

    async def _create_postgres_tables(self) -> None:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL UNIQUE,
                username TEXT,
                full_name TEXT,
                language TEXT NOT NULL DEFAULT 'tg',
                joined_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                block_reason TEXT,
                preferences TEXT NOT NULL DEFAULT ''
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS downloads (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(telegram_id),
                media_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                source_url TEXT NOT NULL DEFAULT '',
                platform TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                size_bytes BIGINT NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id BIGSERIAL PRIMARY KEY,
                admin_id BIGINT,
                action TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS settings (
                id BIGSERIAL PRIMARY KEY,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS broadcasts (
                id BIGSERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                total_users INTEGER NOT NULL DEFAULT 0,
                successful INTEGER NOT NULL DEFAULT 0,
                failed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_downloads_created ON downloads(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_logs_created ON activity_logs(created_at)",
        )
        for statement in statements:
            await self.conn.execute(statement)

    async def _seed_settings(self) -> None:
        defaults = {
            "downloads_enabled": "1",
            "registration_enabled": "1",
            "welcome_message": "",
            "error_message": "",
            "bot_version": BOT_VERSION,
        }
        insert_sql = (
            """
            INSERT INTO settings(setting_key, setting_value) VALUES (?, ?)
            ON CONFLICT (setting_key) DO NOTHING
            """
            if self._postgres
            else "INSERT OR IGNORE INTO settings(setting_key, setting_value) VALUES (?, ?)"
        )
        for key, value in defaults.items():
            await self.conn.execute(insert_sql, (key, value))
        await self.conn.execute(
            "UPDATE settings SET setting_value = ? WHERE setting_key = 'bot_version'",
            (BOT_VERSION,),
        )
        await self.conn.commit()

    async def upsert_user(self, telegram_id: int, username: str | None, full_name: str | None) -> dict[str, Any]:
        existing = await self.get_user(telegram_id)
        ts = now_iso()
        if existing:
            await self.conn.execute(
                """
                UPDATE users
                SET username = ?, full_name = ?, last_active = ?
                WHERE telegram_id = ?
                """,
                (username, full_name, ts, telegram_id),
            )
            await self.conn.commit()
            user = await self.get_user(telegram_id)
            assert user is not None
            return user

        await self.conn.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, language, joined_at, last_active)
            VALUES (?, ?, ?, 'tg', ?, ?)
            """,
            (telegram_id, username, full_name, ts, ts),
        )
        await self.conn.commit()
        user = await self.get_user(telegram_id)
        assert user is not None
        return user

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def set_language(self, telegram_id: int, language: str) -> None:
        await self.conn.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id),
        )
        await self.conn.commit()

    async def set_blocked(self, telegram_id: int, blocked: bool, reason: str | None = None) -> None:
        await self.conn.execute(
            "UPDATE users SET is_blocked = ?, block_reason = ? WHERE telegram_id = ?",
            (1 if blocked else 0, reason if blocked else None, telegram_id),
        )
        await self.conn.commit()

    async def count_users(self) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM users")
        row = await cur.fetchone()
        return int(row["c"] if row else 0)

    async def count_users_since(self, since_iso: str) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE joined_at >= ?",
            (since_iso,),
        )
        row = await cur.fetchone()
        return int(row["c"] if row else 0)

    async def count_blocked(self) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM users WHERE is_blocked = 1")
        row = await cur.fetchone()
        return int(row["c"] if row else 0)

    async def count_active_since(self, since_iso: str) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE last_active >= ? AND is_blocked = 0",
            (since_iso,),
        )
        row = await cur.fetchone()
        return int(row["c"] if row else 0)

    async def list_users(self, page: int = 0, per_page: int = USERS_PAGE, blocked: bool | None = None) -> tuple[list[dict[str, Any]], int]:
        where = ""
        params: list[Any] = []
        if blocked is True:
            where = "WHERE is_blocked = 1"
        elif blocked is False:
            where = "WHERE is_blocked = 0"
        cur = await self.conn.execute(f"SELECT COUNT(*) AS c FROM users {where}", params)
        total = int((await cur.fetchone())["c"])
        offset = page * per_page
        cur = await self.conn.execute(
            f"""
            SELECT * FROM users
            {where}
            ORDER BY joined_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, per_page, offset],
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows], total

    async def search_users(self, query: str) -> list[dict[str, Any]]:
        q = query.strip().lstrip("@")
        if q.isdigit():
            user = await self.get_user(int(q))
            return [user] if user else []
        cur = await self.conn.execute(
            """
            SELECT * FROM users
            WHERE username LIKE ? OR full_name LIKE ?
            ORDER BY last_active DESC
            LIMIT 15
            """,
            (f"%{q}%", f"%{q}%"),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def add_download(
        self,
        user_id: int,
        media_type: str,
        status: str,
        *,
        source_url: str = "",
        platform: str = "",
        title: str = "",
        size_bytes: int = 0,
    ) -> int:
        params = (
            user_id,
            media_type,
            status,
            now_iso(),
            source_url or "",
            platform or "",
            title or "",
            int(size_bytes or 0),
        )
        sql = """
            INSERT INTO downloads (
                user_id, media_type, status, created_at, source_url, platform, title, size_bytes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        if self._postgres:
            cur = await self.conn.execute(sql + " RETURNING id", params)
            row = await cur.fetchone()
            return int(row["id"]) if row else 0
        cur = await self.conn.execute(sql, params)
        await self.conn.commit()
        return int(cur.lastrowid or 0)

    async def count_downloads(
        self,
        status: str | None = None,
        media_type: str | None = None,
        since_iso: str | None = None,
        user_id: int | None = None,
    ) -> int:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if media_type:
            clauses.append("media_type = ?")
            params.append(media_type)
        if since_iso:
            clauses.append("created_at >= ?")
            params.append(since_iso)
        if user_id is not None:
            clauses.append("user_id = ?")
            params.append(user_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = await self.conn.execute(f"SELECT COUNT(*) AS c FROM downloads {where}", params)
        row = await cur.fetchone()
        return int(row["c"] if row else 0)

    async def user_download_counts(self, user_id: int) -> dict[str, int]:
        success = await self.count_downloads(status="success", user_id=user_id)
        failed = await self.count_downloads(status="failed", user_id=user_id)
        return {"success": success, "failed": failed, "total": success + failed}

    async def add_log(self, admin_id: int | None, action: str, description: str = "") -> None:
        await self.conn.execute(
            "INSERT INTO activity_logs (admin_id, action, description, created_at) VALUES (?, ?, ?, ?)",
            (admin_id, action, description, now_iso()),
        )
        await self.conn.commit()

    async def list_logs(self, page: int = 0, per_page: int = LOGS_PAGE) -> tuple[list[dict[str, Any]], int]:
        cur = await self.conn.execute("SELECT COUNT(*) AS c FROM activity_logs")
        total = int((await cur.fetchone())["c"])
        cur = await self.conn.execute(
            """
            SELECT * FROM activity_logs
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, page * per_page),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows], total

    async def get_setting(self, key: str, default: str = "") -> str:
        cur = await self.conn.execute(
            "SELECT setting_value FROM settings WHERE setting_key = ?",
            (key,),
        )
        row = await cur.fetchone()
        if not row:
            return default
        return str(row["setting_value"])

    async def set_setting(self, key: str, value: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO settings(setting_key, setting_value) VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """,
            (key, value),
        )
        await self.conn.commit()

    async def downloads_enabled(self) -> bool:
        return await self.get_setting("downloads_enabled", "1") == "1"

    async def registration_enabled(self) -> bool:
        return await self.get_setting("registration_enabled", "1") == "1"

    async def add_broadcast(self, message: str, total: int, successful: int, failed: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO broadcasts (message, total_users, successful, failed, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message, total, successful, failed, now_iso()),
        )
        await self.conn.commit()

    async def target_user_ids(self, active_only: bool = False) -> list[int]:
        if active_only:
            cur = await self.conn.execute(
                """
                SELECT telegram_id FROM users
                WHERE is_blocked = 0 AND last_active >= ?
                ORDER BY id
                """,
                (day_start(7),),
            )
        else:
            cur = await self.conn.execute(
                "SELECT telegram_id FROM users WHERE is_blocked = 0 ORDER BY id"
            )
        rows = await cur.fetchall()
        return [int(r["telegram_id"]) for r in rows]

    async def users_by_day(self, days: int = 7) -> list[tuple[str, int]]:
        since = day_start(days - 1)
        cur = await self.conn.execute(
            """
            SELECT substr(joined_at, 1, 10) AS day, COUNT(*) AS c
            FROM users
            WHERE joined_at >= ?
            GROUP BY day
            ORDER BY day
            """,
            (since,),
        )
        rows = await cur.fetchall()
        return [(r["day"], int(r["c"])) for r in rows]

    async def downloads_by_day(self, days: int = 7) -> list[tuple[str, int]]:
        since = day_start(days - 1)
        cur = await self.conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS c
            FROM downloads
            WHERE created_at >= ? AND status = 'success'
            GROUP BY day
            ORDER BY day
            """,
            (since,),
        )
        rows = await cur.fetchall()
        return [(r["day"], int(r["c"])) for r in rows]

    async def busiest_days(self, limit: int = 5) -> list[tuple[str, int]]:
        cur = await self.conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS c
            FROM downloads
            WHERE status = 'success'
            GROUP BY day
            ORDER BY c DESC, day DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cur.fetchall()
        return [(r["day"], int(r["c"])) for r in rows]

    async def media_type_counts(self) -> dict[str, int]:
        cur = await self.conn.execute(
            """
            SELECT media_type, COUNT(*) AS c
            FROM downloads
            WHERE status = 'success'
            GROUP BY media_type
            """
        )
        rows = await cur.fetchall()
        return {str(r["media_type"]): int(r["c"]) for r in rows}

    async def get_preferences(self, telegram_id: int) -> dict[str, Any]:
        user = await self.get_user(telegram_id)
        raw = str((user or {}).get("preferences") or "")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    async def save_preferences(self, telegram_id: int, data: dict[str, Any]) -> None:
        await self.conn.execute(
            "UPDATE users SET preferences = ? WHERE telegram_id = ?",
            (json.dumps(data, ensure_ascii=False), telegram_id),
        )
        await self.conn.commit()

    async def list_user_downloads(
        self,
        user_id: int,
        *,
        platform: str = "",
        query: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = ["user_id = ?"]
        params: list[Any] = [user_id]
        if platform:
            clauses.append("platform = ?")
            params.append(platform)
        text = query.strip()
        if text:
            like = f"%{text}%"
            clauses.append("(title LIKE ? OR source_url LIKE ? OR media_type LIKE ?)")
            params.extend((like, like, like))
        where = "WHERE " + " AND ".join(clauses)
        cur = await self.conn.execute(f"SELECT COUNT(*) AS c FROM downloads {where}", params)
        total = int((await cur.fetchone())["c"])
        offset = max(0, page - 1) * page_size
        cur = await self.conn.execute(
            f"""
            SELECT * FROM downloads
            {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows], total

    async def user_platform_counts(self, user_id: int, query: str = "", status: str = "") -> list[tuple[str, int]]:
        clauses = ["user_id = ?"]
        params: list[Any] = [user_id]
        if status:
            clauses.append("status = ?")
            params.append(status)
        text = query.strip()
        if text:
            like = f"%{text}%"
            clauses.append("(title LIKE ? OR source_url LIKE ? OR media_type LIKE ?)")
            params.extend((like, like, like))
        cur = await self.conn.execute(
            f"""
            SELECT platform, COUNT(*) AS c
            FROM downloads
            WHERE {' AND '.join(clauses)}
            GROUP BY platform
            """,
            params,
        )
        rows = await cur.fetchall()
        return [(str(row["platform"] or ""), int(row["c"])) for row in rows]

    async def get_user_download(self, user_id: int, download_id: int) -> dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT * FROM downloads WHERE id = ? AND user_id = ?",
            (download_id, user_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def delete_user_download(self, user_id: int, download_id: int) -> bool:
        if self._postgres:
            cur = await self.conn.execute(
                "DELETE FROM downloads WHERE id = ? AND user_id = ? RETURNING id",
                (download_id, user_id),
            )
            return await cur.fetchone() is not None
        cur = await self.conn.execute(
            "DELETE FROM downloads WHERE id = ? AND user_id = ?",
            (download_id, user_id),
        )
        await self.conn.commit()
        return int(cur.rowcount or 0) > 0

    async def clear_user_downloads(self, user_id: int) -> None:
        await self.conn.execute("DELETE FROM downloads WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def user_download_stats(self, user_id: int, since_iso: str) -> dict[str, int]:
        cur = await self.conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN created_at >= ? AND status = 'success' THEN 1 ELSE 0 END), 0) AS week,
                COALESCE(SUM(CASE WHEN status = 'success' THEN size_bytes ELSE 0 END), 0) AS size_bytes
            FROM downloads
            WHERE user_id = ? AND status = 'success'
            """,
            (since_iso, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return {"total": 0, "week": 0, "size_bytes": 0}
        return {
            "total": int(row["total"] or 0),
            "week": int(row["week"] or 0),
            "size_bytes": int(row["size_bytes"] or 0),
        }

    async def dashboard(self) -> dict[str, int]:
        return {
            "total_users": await self.count_users(),
            "new_today": await self.count_users_since(day_start(0)),
            "new_7": await self.count_users_since(day_start(6)),
            "new_30": await self.count_users_since(day_start(29)),
            "downloads_ok": await self.count_downloads(status="success"),
            "downloads_today": await self.count_downloads(status="success", since_iso=day_start(0)),
            "downloads_fail": await self.count_downloads(status="failed"),
            "active": await self.count_active_since(day_start(6)),
            "blocked": await self.count_blocked(),
        }


db = Database()
