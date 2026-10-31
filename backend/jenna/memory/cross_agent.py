"""
Jenna Cross-Agent Memory Aggregator
Read-only ingestion from all local AI agent harnesses into a unified SQLite+FTS5 store.
"""
from __future__ import annotations
import sqlite3
import json
import os
import glob
import hashlib
import re
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterator, Optional
import logging

log = logging.getLogger("jenna.memory.cross_agent")

SECRET_PATTERNS = [
    (re.compile(r'(api[_-]?key|apikey|secret|token|password|passwd|auth[_-]?token|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', re.I), r'\1=[REDACTED]'),
    (re.compile(r'(sk|pk)_(live|test)_[a-zA-Z0-9]{24,}'), '[REDACTED_STRIPE_KEY]'),
    (re.compile(r'gh[pousr]_[a-zA-Z0-9]{36,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'xox[baprs]-[a-zA-Z0-9-]{10,}'), '[REDACTED_SLACK_TOKEN]'),
    (re.compile(r'[a-zA-Z0-9+/]{40,}={0,2}'), '[REDACTED_BASE64]'),
]


def redact_secrets(text: str) -> str:
    """Redact common secret patterns from text."""
    for pattern, repl in SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


@dataclass
class MemoryRecord:
    agent: str
    session_id: str
    timestamp: datetime
    role: str
    text: str
    cwd: Optional[str] = None
    model: Optional[str] = None
    meta: Optional[dict] = None


class CrossAgentMemory:
    """Aggregates conversation history from all known AI harnesses."""

    HARNESS_PATHS = {
        "hermes": [
            Path.home() / ".hermes" / "state.db",
            Path.home() / ".hermes" / "sessions",
        ],
        "claude": [
            Path.home() / ".claude" / "projects",
        ],
        "antigravity": [
            Path.home() / ".gemini" / "antigravity-ide" / "conversations",
        ],
        "codex": [
            Path.home() / ".codex",
        ],
        "opencode": [
            Path.home() / ".local" / "share" / "opencode",
            Path.home() / ".config" / "opencode",
        ],
        "cursor": [
            Path.home() / ".cursor",
        ],
        "aider": [
            Path.home() / ".aider",
        ],
        "copilot": [
            Path.home() / ".copilot" / "logs",
        ],
    }

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (Path.home() / ".config" / "jenna" / "memory" / "agent_stream.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite schema with FTS5."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watermarks (
                    source TEXT PRIMARY KEY,
                    last_ingested TIMESTAMP,
                    last_file_mtime REAL,
                    last_rowid INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    cwd TEXT,
                    model TEXT,
                    meta TEXT,
                    content_hash TEXT UNIQUE
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    agent, session_id, role, text, cwd, model,
                    content='messages', content_rowid='id'
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO messages_fts(rowid, agent, session_id, role, text, cwd, model)
                    VALUES (new.id, new.agent, new.session_id, new.role, new.text, new.cwd, new.model);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, agent, session_id, role, text, cwd, model)
                    VALUES ('delete', old.id, old.agent, old.session_id, old.role, old.text, old.cwd, old.model);
                END
            """)
            conn.commit()

    def _get_watermark(self, source: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT last_ingested, last_file_mtime, last_rowid FROM watermarks WHERE source = ?",
                (source,)
            ).fetchone()
            if row:
                return {"last_ingested": row[0], "last_file_mtime": row[1], "last_rowid": row[2]}
        return {}

    def _set_watermark(self, source: str, last_ingested: str, last_file_mtime: float, last_rowid: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO watermarks (source, last_ingested, last_file_mtime, last_rowid)
                VALUES (?, ?, ?, ?)
            """, (source, last_ingested, last_file_mtime, last_rowid))
            conn.commit()

    def _hash_content(self, agent: str, session_id: str, timestamp: str, role: str, text: str) -> str:
        h = hashlib.sha256()
        h.update(f"{agent}|{session_id}|{timestamp}|{role}|{text}".encode())
        return h.hexdigest()[:32]

    def _insert_record(self, rec: MemoryRecord) -> bool:
        """Insert a record, return True if new, False if duplicate."""
        content_hash = self._hash_content(rec.agent, rec.session_id, rec.timestamp.isoformat(), rec.role, rec.text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO messages (agent, session_id, timestamp, role, text, cwd, model, meta, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec.agent, rec.session_id, rec.timestamp.isoformat(), rec.role,
                    redact_secrets(rec.text), rec.cwd, rec.model,
                    json.dumps(rec.meta) if rec.meta else None,
                    content_hash
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate

    def _insert_batch(self, records: list[MemoryRecord]) -> int:
        """Batch insert records, return count of new records."""
        if not records:
            return 0
        batch_data = []
        for rec in records:
            content_hash = self._hash_content(rec.agent, rec.session_id, rec.timestamp.isoformat(), rec.role, rec.text)
            batch_data.append((
                rec.agent, rec.session_id, rec.timestamp.isoformat(), rec.role,
                redact_secrets(rec.text), rec.cwd, rec.model,
                json.dumps(rec.meta) if rec.meta else None,
                content_hash
            ))
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany("""
                    INSERT OR IGNORE INTO messages (agent, session_id, timestamp, role, text, cwd, model, meta, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                conn.commit()
            return len(batch_data)  # Approximate, OR IGNORE skips duplicates
        except Exception:
            return 0

    # ── Source-specific ingesters ──

    def ingest_hermes(self) -> int:
        """Ingest from Hermes state.db (messages + sessions tables)."""
        db_file = Path.home() / ".hermes" / "state.db"
        if not db_file.exists():
            return 0

        wm = self._get_watermark("hermes")
        last_rowid = wm.get("last_rowid", 0)

        with sqlite3.connect(f"file:{db_file}?mode=ro", uri=True) as src:
            # Fetch sessions first (small table, 29 rows)
            sessions = {
                row[0]: {"cwd": row[1], "model": row[2], "git_branch": row[3], "git_repo_root": row[4]}
                for row in src.execute("SELECT id, cwd, model, git_branch, git_repo_root FROM sessions")
            }

            # Fetch messages (no JOIN, much faster)
            rows = src.execute("""
                SELECT id, session_id, role, content, timestamp
                FROM messages
                WHERE id > ? AND content IS NOT NULL AND content != ''
                ORDER BY id
            """, (last_rowid,)).fetchall()

            max_id = last_rowid
            batch = []
            for msg_id, session_id, role, content, timestamp in rows:
                if not content or not content.strip():
                    continue
                try:
                    ts = datetime.fromtimestamp(timestamp)
                except Exception:
                    ts = datetime.now()

                s = sessions.get(session_id, {})
                batch.append(MemoryRecord(
                    agent="hermes",
                    session_id=str(session_id),
                    timestamp=ts,
                    role=role,
                    text=content,
                    cwd=s.get("cwd"),
                    model=s.get("model"),
                    meta={"git_branch": s.get("git_branch"), "git_repo_root": s.get("git_repo_root")}
                ))
                max_id = max(max_id, msg_id)

            count = self._insert_batch(batch)

            if max_id > last_rowid:
                self._set_watermark("hermes", datetime.now().isoformat(), db_file.stat().st_mtime, max_id)
        return count

    def ingest_antigravity(self) -> int:
        """Ingest from Antigravity conversation SQLite databases."""
        conv_dir = Path.home() / ".gemini" / "antigravity-ide" / "conversations"
        if not conv_dir.exists():
            return 0

        wm = self._get_watermark("antigravity")
        last_mtime = wm.get("last_file_mtime", 0)

        count = 0
        max_mtime = last_mtime

        for db_file in sorted(conv_dir.glob("*.db")):
            mtime = db_file.stat().st_mtime
            if mtime <= last_mtime:
                continue

            try:
                with sqlite3.connect(f"file:{db_file}?mode=ro", uri=True) as src:
                    # Find tables with messages
                    tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                    msg_table = None
                    for t in tables:
                        cols = [c[1] for c in src.execute(f"PRAGMA table_info({t})")]
                        if any(c in cols for c in ('content', 'text', 'message', 'role')):
                            msg_table = t
                            break
                    if not msg_table:
                        continue

                    cols = [c[1] for c in src.execute(f"PRAGMA table_info({msg_table})")]
                    rows = src.execute(f"SELECT * FROM {msg_table}").fetchall()

                    for row in rows:
                        row_dict = dict(zip(cols, row))
                        text = row_dict.get('content') or row_dict.get('text') or row_dict.get('message') or ''
                        role = row_dict.get('role', 'assistant')
                        if not text or not text.strip():
                            continue
                        ts_str = row_dict.get('timestamp') or row_dict.get('created_at') or row_dict.get('time', '')
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        except Exception:
                            ts = datetime.fromtimestamp(mtime)

                        rec = MemoryRecord(
                            agent="antigravity",
                            session_id=db_file.stem,
                            timestamp=ts,
                            role=role,
                            text=text,
                            model=row_dict.get('model'),
                            meta=row_dict
                        )
                        if self._insert_record(rec):
                            count += 1

                max_mtime = max(max_mtime, mtime)
            except Exception as e:
                log.warning(f"Failed to ingest {db_file}: {e}")

        if max_mtime > last_mtime:
            self._set_watermark("antigravity", datetime.now().isoformat(), max_mtime, 0)
        return count

    def ingest_claude(self) -> int:
        """Ingest from Claude Code JSONL project files."""
        proj_dir = Path.home() / ".claude" / "projects"
        if not proj_dir.exists():
            return 0

        wm = self._get_watermark("claude")
        last_mtime = wm.get("last_file_mtime", 0)

        count = 0
        max_mtime = last_mtime

        for jsonl_file in proj_dir.rglob("*.jsonl"):
            mtime = jsonl_file.stat().st_mtime
            if mtime <= last_mtime:
                continue

            try:
                with open(jsonl_file, 'r', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Claude Code format: {"type": "user|assistant", "message": {...}, "timestamp": "..."}
                        msg_type = data.get('type')
                        if msg_type not in ('user', 'assistant'):
                            continue

                        msg = data.get('message', {})
                        role = msg.get('role', msg_type)
                        content = msg.get('content', '')
                        if isinstance(content, list):
                            # Handle multi-part content
                            content = ' '.join(str(c.get('text', '')) for c in content if c.get('type') == 'text')
                        if not content or not content.strip():
                            continue

                        ts_str = data.get('timestamp', '')
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        except Exception:
                            ts = datetime.fromtimestamp(mtime)

                        session_id = jsonl_file.stem
                        rec = MemoryRecord(
                            agent="claude",
                            session_id=session_id,
                            timestamp=ts,
                            role=role,
                            text=content,
                            cwd=str(jsonl_file.parent),
                            model=data.get('model'),
                            meta={"parent_uuid": data.get('parent_uuid'), "uuid": data.get('uuid')}
                        )
                        if self._insert_record(rec):
                            count += 1

                max_mtime = max(max_mtime, mtime)
            except Exception as e:
                log.warning(f"Failed to ingest {jsonl_file}: {e}")

        if max_mtime > last_mtime:
            self._set_watermark("claude", datetime.now().isoformat(), max_mtime, 0)
        return count

    def ingest_codex(self) -> int:
        """Ingest from Codex SQLite databases."""
        codex_dir = Path.home() / ".codex"
        if not codex_dir.exists():
            return 0

        wm = self._get_watermark("codex")
        last_mtime = wm.get("last_file_mtime", 0)

        count = 0
        max_mtime = last_mtime

        for db_file in codex_dir.glob("*.sqlite"):
            mtime = db_file.stat().st_mtime
            if mtime <= last_mtime:
                continue

            try:
                with sqlite3.connect(f"file:{db_file}?mode=ro", uri=True) as src:
                    tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                    for table in tables:
                        cols = [c[1] for c in src.execute(f"PRAGMA table_info({table})")]
                        if not any(c in cols for c in ('content', 'text', 'message', 'prompt', 'response')):
                            continue
                        rows = src.execute(f"SELECT * FROM {table}").fetchall()
                        for row in rows:
                            row_dict = dict(zip(cols, row))
                            text = row_dict.get('content') or row_dict.get('text') or row_dict.get('message') or ''
                            role = row_dict.get('role', 'assistant')
                            if not text or not text.strip():
                                continue
                            ts_str = row_dict.get('timestamp') or row_dict.get('created_at') or row_dict.get('time', '')
                            try:
                                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            except Exception:
                                ts = datetime.fromtimestamp(mtime)

                            rec = MemoryRecord(
                                agent="codex",
                                session_id=f"{db_file.stem}_{table}",
                                timestamp=ts,
                                role=role,
                                text=text,
                                model=row_dict.get('model'),
                                meta=row_dict
                            )
                            if self._insert_record(rec):
                                count += 1
                max_mtime = max(max_mtime, mtime)
            except Exception as e:
                log.warning(f"Failed to ingest {db_file}: {e}")

        if max_mtime > last_mtime:
            self._set_watermark("codex", datetime.now().isoformat(), max_mtime, 0)
        return count

    def ingest_all(self) -> dict[str, int]:
        """Run all ingesters and return counts per source."""
        results = {}
        for name, method in [
            ("hermes", self.ingest_hermes),
            ("antigravity", self.ingest_antigravity),
            ("claude", self.ingest_claude),
            ("codex", self.ingest_codex),
        ]:
            try:
                results[name] = method()
                log.info(f"Ingested {results[name]} messages from {name}")
            except Exception as e:
                log.error(f"Failed to ingest {name}: {e}")
                results[name] = 0
        return results

    # ── Query API ──

    def search(self, query: str, agent: Optional[str] = None, days: int = 30, limit: int = 50) -> list[dict]:
        """Full-text search across all agents."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT m.*, bm25(messages_fts) as rank
                FROM messages_fts
                JOIN messages m ON messages_fts.rowid = m.id
                WHERE messages_fts MATCH ? AND m.timestamp >= ?
            """
            params = [query, since]
            if agent:
                sql += " AND m.agent = ?"
                params.append(agent)
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            return [dict(r) for r in conn.execute(sql, params)]

    def recent(self, agent: Optional[str] = None, days: int = 7, limit: int = 100) -> list[dict]:
        """Get recent messages."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM messages WHERE timestamp >= ?"
            params = [since]
            if agent:
                sql += " AND agent = ?"
                params.append(agent)
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            return [dict(r) for r in conn.execute(sql, params)]

    def stats(self) -> dict:
        """Get collection statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            by_agent = dict(conn.execute("SELECT agent, COUNT(*) FROM messages GROUP BY agent"))
            date_range = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages").fetchone()
            return {
                "total_messages": total,
                "by_agent": by_agent,
                "date_range": {"earliest": date_range[0], "latest": date_range[1]},
                "db_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0,
            }

    def write_daily_digest(self, vault_path: Path, days: int = 1) -> Path:
        """Write a daily digest to Obsidian vault."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT agent, role, text, timestamp, cwd, model
                FROM messages
                WHERE timestamp >= ?
                ORDER BY agent, timestamp
            """, (since,)).fetchall()

        vault_path.mkdir(parents=True, exist_ok=True)
        digest_file = vault_path / f"cross-agent-digest-{datetime.now().strftime('%Y-%m-%d')}.md"

        by_agent = {}
        for r in rows:
            by_agent.setdefault(r['agent'], []).append(r)

        with open(digest_file, 'w') as f:
            f.write(f"# Cross-Agent Digest — {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(f"_Auto-generated from {sum(len(v) for v in by_agent.values())} messages across {len(by_agent)} agents_\n\n")

            for agent, messages in sorted(by_agent.items()):
                f.write(f"## {agent.upper()} ({len(messages)} messages)\n\n")
                for m in messages:
                    ts = m['timestamp'][:19].replace('T', ' ')
                    role = m['role'].upper()
                    text = m['text'][:200] + ('...' if len(m['text']) > 200 else '')
                    cwd = f" `{m['cwd']}`" if m['cwd'] else ''
                    model = f" *{m['model']}*" if m['model'] else ''
                    f.write(f"- **{ts}** [{role}]{cwd}{model}: {text}\n")
                f.write("\n")

        return digest_file


# Convenience function
def get_cross_agent_memory() -> CrossAgentMemory:
    return CrossAgentMemory()