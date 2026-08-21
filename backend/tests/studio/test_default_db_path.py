"""
`load_row`/`list_campaigns` must read the same sqlite file the rest of the
app writes to, via `settings.DATABASE_URL` — not a hardcoded `"sql_app.db"`
literal that happens to coincide with it only by accident of cwd.

Reported bug this guards against: docker-compose.yml's DATABASE_URL was
changed to `sqlite:////app/data/sql_app.db` (so the database survives an
image rebuild, persisted the same way generated assets already were), but
this module's `load_row`/`list_campaigns` still defaulted to
`Path("sql_app.db")` — a path with no connection to DATABASE_URL at all.
The ORM would write campaigns to `/app/data/sql_app.db` while the studio's
"campaigns" inbox kept reading (and finding nothing in) `/app/sql_app.db` —
a silent split-brain that would make every researched campaign invisible
to the studio in that environment.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.config import settings
from app.services.studio import from_research


def test_default_db_path_follows_relative_sqlite_url(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:///./sql_app.db")
    assert from_research._default_db_path() == Path("./sql_app.db")


def test_default_db_path_follows_absolute_sqlite_url(monkeypatch):
    """The exact case this fixes: docker-compose.yml's Docker-persistent path."""
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:////app/data/sql_app.db")
    assert from_research._default_db_path() == Path("/app/data/sql_app.db")


def test_default_db_path_falls_back_for_non_sqlite_url(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://user:pass@host/db")
    assert from_research._default_db_path() == Path("sql_app.db")


def _make_campaigns_db(path: Path) -> None:
    connection = sqlite3.connect(str(path))
    connection.execute(
        "create table campaigns (id text primary key, name text, status text, "
        "updated_at text, research_input text, research_result text)"
    )
    connection.execute(
        "insert into campaigns values (?, ?, ?, ?, ?, ?)",
        ("c-1", "Test Campaign", "researched", "2026-01-01", "{}", "{}"),
    )
    connection.commit()
    connection.close()


def _sqlite_url_for(path: Path) -> str:
    """Build a `sqlite:///` URL that `_default_db_path` round-trips back to
    exactly `path`, on whichever platform the test runs on. On POSIX this is
    the standard 4-slash absolute form; on Windows, `sqlite:///` (3 slashes)
    followed by the drive-letter path is what round-trips, since a 4th
    slash before `C:\\...` would leave a leading path separator baked into
    the string that `Path(...)` normalises away, breaking equality."""
    resolved = path.resolve()
    if resolved.drive:  # Windows: sqlite:///C:/Users/... (3 slashes)
        return f"sqlite:///{resolved.as_posix()}"
    return f"sqlite:////{resolved.as_posix().lstrip('/')}"  # POSIX: 4 slashes


def test_list_campaigns_reads_the_file_database_url_points_at(tmp_path, monkeypatch):
    """The actual regression test: point DATABASE_URL at a path that is NOT
    the historical "sql_app.db" literal, and confirm list_campaigns still
    finds the row — proving it followed DATABASE_URL rather than the old
    hardcoded default."""
    db_file = tmp_path / "data" / "sql_app.db"
    db_file.parent.mkdir(parents=True)
    _make_campaigns_db(db_file)

    monkeypatch.setattr(settings, "DATABASE_URL", _sqlite_url_for(db_file))

    rows = from_research.list_campaigns()
    assert [r["id"] for r in rows] == ["c-1"]


def test_list_campaigns_no_longer_reads_the_old_hardcoded_literal(tmp_path, monkeypatch):
    """If a file named exactly "sql_app.db" happens to sit in the process's
    cwd (the old default), it must be ignored once DATABASE_URL points
    somewhere else — otherwise the split-brain this fixes could still occur
    silently."""
    old_default = Path("sql_app.db")
    created_old_default = not old_default.exists()
    if created_old_default:
        _make_campaigns_db(old_default)
    try:
        real_db = tmp_path / "data" / "sql_app.db"
        real_db.parent.mkdir(parents=True)
        # Give the real DB a different row so the two are distinguishable.
        connection = sqlite3.connect(str(real_db))
        connection.execute(
            "create table campaigns (id text primary key, name text, status text, "
            "updated_at text, research_input text, research_result text)"
        )
        connection.commit()
        connection.close()

        monkeypatch.setattr(settings, "DATABASE_URL", _sqlite_url_for(real_db))

        rows = from_research.list_campaigns()
        # The real (empty) DB was read, not the stray old-default file with
        # its "c-1" row.
        assert rows == []
    finally:
        if created_old_default:
            old_default.unlink(missing_ok=True)
