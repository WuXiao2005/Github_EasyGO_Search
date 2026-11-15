"""SQLite 快照库：记录每天的 star 数，用于计算 7 日增量；并缓存翻译结果。"""
import datetime as dt
import json
import os
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    repo TEXT NOT NULL,
    day  TEXT NOT NULL,
    stars INTEGER NOT NULL,
    forks INTEGER NOT NULL,
    PRIMARY KEY (repo, day)
);
CREATE TABLE IF NOT EXISTS repos (
    repo TEXT PRIMARY KEY,
    meta TEXT NOT NULL,
    updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS localizations (
    repo TEXT NOT NULL,
    sig  TEXT NOT NULL,
    payload TEXT NOT NULL,
    updated TEXT NOT NULL,
    PRIMARY KEY (repo, sig)
);
CREATE TABLE IF NOT EXISTS queries (
    qkey TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated TEXT NOT NULL
);
"""


class Store:
    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self.path = os.path.join(data_dir, "digest.db")
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.lock = threading.Lock()
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------- 快照 ----------
    def save_snapshot(self, items, day):
        rows = [(it["full_name"], day, it["stars"], it["forks"]) for it in items]
        self.conn.executemany(
            "INSERT OR REPLACE INTO snapshots(repo, day, stars, forks) VALUES (?,?,?,?)", rows
        )
        self.conn.commit()
        return len(rows)

    def stars_on_or_before(self, repo, day):
        """取 <= day 的最近一条快照，返回 (stars, day)；没有则返回 (None, None)。"""
        cur = self.conn.execute(
            "SELECT stars, day FROM snapshots WHERE repo=? AND day<=? ORDER BY day DESC LIMIT 1",
            (repo, day),
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)

    def coverage(self):
        cur = self.conn.execute("SELECT MIN(day), MAX(day), COUNT(*), COUNT(DISTINCT day) FROM snapshots")
        return cur.fetchone()

    # ---------- 元数据 ----------
    def save_meta(self, items, updated):
        rows = [(it["full_name"], json.dumps(it, ensure_ascii=False), updated) for it in items]
        self.conn.executemany(
            "INSERT OR REPLACE INTO repos(repo, meta, updated) VALUES (?,?,?)", rows
        )
        self.conn.commit()

    # ---------- 翻译缓存 ----------
    def get_localization(self, repo, sig):
        cur = self.conn.execute(
            "SELECT payload FROM localizations WHERE repo=? AND sig=?", (repo, sig)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def put_localization(self, repo, sig, payload, updated):
        self.conn.execute(
            "INSERT OR REPLACE INTO localizations(repo, sig, payload, updated) VALUES (?,?,?,?)",
            (repo, sig, json.dumps(payload, ensure_ascii=False), updated),
        )
        self.conn.commit()

    # ---------- 查询缓存 ----------
    def get_query(self, qkey, max_age_hours=6):
        cur = self.conn.execute("SELECT payload, updated FROM queries WHERE qkey=?", (qkey,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            fresh = dt.datetime.now() - dt.datetime.fromisoformat(row[1])
        except ValueError:
            return None
        if fresh.total_seconds() > max_age_hours * 3600:
            return None
        return json.loads(row[0])

    def put_query(self, qkey, payload):
        self.conn.execute(
            "INSERT OR REPLACE INTO queries(qkey, payload, updated) VALUES (?,?,?)",
            (qkey, json.dumps(payload, ensure_ascii=False), dt.datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()


def today_str():
    return dt.date.today().isoformat()


def days_ago(n):
    return (dt.date.today() - dt.timedelta(days=n)).isoformat()
