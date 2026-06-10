"""SQLite 数据库访问层。"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


@dataclass
class User:
    """当前登录用户。"""

    id: int
    username: str


class DatabaseManager:
    """封装 SQLite 建表、增删改查与事务提交。"""

    def __init__(self, db_path: str | Path = "study_assistant.db") -> None:
        self.db_path = Path(db_path)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.init_database()

    def init_database(self) -> None:
        """初始化用户、学习记录、错题、计划、成绩、问答历史等数据表。"""
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                record_date TEXT NOT NULL,
                minutes INTEGER NOT NULL CHECK(minutes >= 0),
                note TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                subject TEXT DEFAULT '通用',
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                target_date TEXT NOT NULL,
                status TEXT DEFAULT '未完成',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                score REAL NOT NULL CHECK(score >= 0),
                exam_date TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS qa_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
        ]
        with self.connection:
            for statement in sql_statements:
                self.connection.execute(statement)

    @staticmethod
    def hash_password(password: str) -> str:
        """用 SHA-256 保存密码摘要，避免明文入库。"""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def register_user(self, username: str, password: str) -> User:
        """注册新用户。"""
        username = username.strip()
        if not username or not password:
            raise ValueError("用户名和密码不能为空。")
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO users(username, password) VALUES(?, ?)",
                (username, self.hash_password(password)),
            )
        return User(id=int(cursor.lastrowid), username=username)

    def login_user(self, username: str, password: str) -> User:
        """校验用户名和密码。"""
        row = self.connection.execute(
            "SELECT id, username FROM users WHERE username = ? AND password = ?",
            (username.strip(), self.hash_password(password)),
        ).fetchone()
        if row is None:
            raise ValueError("用户名或密码错误。")
        return User(id=row["id"], username=row["username"])

    def add_study_record(self, user_id: int, minutes: int, note: str, record_date: str | None = None) -> None:
        if minutes < 0:
            raise ValueError("学习时长不能为负数。")
        with self.connection:
            self.connection.execute(
                "INSERT INTO study_records(user_id, record_date, minutes, note) VALUES(?, ?, ?, ?)",
                (user_id, record_date or date.today().isoformat(), minutes, note.strip()),
            )

    def add_mistake(self, user_id: int, question: str, answer: str, subject: str) -> None:
        if not question.strip() or not answer.strip():
            raise ValueError("题目和答案不能为空。")
        with self.connection:
            self.connection.execute(
                "INSERT INTO mistakes(user_id, question, answer, subject, created_at) VALUES(?, ?, ?, ?, ?)",
                (user_id, question.strip(), answer.strip(), subject.strip() or "通用", datetime.now().isoformat(timespec="seconds")),
            )

    def delete_mistake(self, mistake_id: int, user_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM mistakes WHERE id = ? AND user_id = ?", (mistake_id, user_id))

    def add_plan(self, user_id: int, title: str, target_date: str) -> None:
        if not title.strip():
            raise ValueError("计划标题不能为空。")
        datetime.strptime(target_date, "%Y-%m-%d")
        with self.connection:
            self.connection.execute(
                "INSERT INTO plans(user_id, title, target_date) VALUES(?, ?, ?)",
                (user_id, title.strip(), target_date),
            )

    def toggle_plan(self, plan_id: int, user_id: int) -> None:
        row = self.connection.execute(
            "SELECT status FROM plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        ).fetchone()
        if row is None:
            return
        new_status = "已完成" if row["status"] == "未完成" else "未完成"
        with self.connection:
            self.connection.execute("UPDATE plans SET status = ? WHERE id = ? AND user_id = ?", (new_status, plan_id, user_id))

    def add_score(self, user_id: int, subject: str, score: float, exam_date: str | None = None) -> None:
        if score < 0 or score > 150:
            raise ValueError("成绩应在 0 到 150 之间。")
        with self.connection:
            self.connection.execute(
                "INSERT INTO scores(user_id, subject, score, exam_date) VALUES(?, ?, ?, ?)",
                (user_id, subject.strip() or "通用", score, exam_date or date.today().isoformat()),
            )

    def add_qa_history(self, user_id: int, question: str, answer: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO qa_history(user_id, question, answer, created_at) VALUES(?, ?, ?, ?)",
                (user_id, question.strip(), answer.strip(), datetime.now().isoformat(timespec="seconds")),
            )

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.connection.execute(query, params).fetchall())

    def user_summary(self, user_id: int) -> dict[str, Any]:
        total_minutes = self.connection.execute(
            "SELECT COALESCE(SUM(minutes), 0) AS total FROM study_records WHERE user_id = ?",
            (user_id,),
        ).fetchone()["total"]
        mistake_count = self.connection.execute(
            "SELECT COUNT(*) AS total FROM mistakes WHERE user_id = ?",
            (user_id,),
        ).fetchone()["total"]
        finished_plans = self.connection.execute(
            "SELECT COUNT(*) AS total FROM plans WHERE user_id = ? AND status = '已完成'",
            (user_id,),
        ).fetchone()["total"]
        avg_score = self.connection.execute(
            "SELECT ROUND(AVG(score), 2) AS avg_score FROM scores WHERE user_id = ?",
            (user_id,),
        ).fetchone()["avg_score"]
        return {
            "total_minutes": total_minutes,
            "mistake_count": mistake_count,
            "finished_plans": finished_plans,
            "avg_score": avg_score or 0,
        }

    def close(self) -> None:
        self.connection.close()
